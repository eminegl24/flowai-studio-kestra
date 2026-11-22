"""Test OIDC claims and the AgentHub adapter contract against controlled providers."""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from aiohttp import CookieJar, web
from aiohttp.test_utils import TestClient, TestServer
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt

import service

ISSUER = "https://sso.example.test"


class ConnectorTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        env = patch.dict(os.environ, {"FLOWAI_DB": str(Path(directory.name) / "test.db")})
        env.start()
        self.addCleanup(env.stop)
        self.config = {
            "users": {"admin": {"password": "test-admin", "role": "admin"}},
            "mcp_token": "test-token",
            "oidc": {
                "issuer": ISSUER, "client_id": "studio-test", "client_secret": "test-secret",
                "subjects": {"uid-test": "viewer"},
            },
        }
        self.client = TestClient(TestServer(service.application(self.config)), cookie_jar=CookieJar(unsafe=True))
        await self.client.start_server()
        self.addAsyncCleanup(self.client.close)
        self.origin = str(self.client.make_url("/")).rstrip("/")
        origin = patch.object(service, "ORIGIN", self.origin)
        origin.start()
        self.addCleanup(origin.stop)

    async def test_oidc_nonce_state_and_replay(self):
        signing_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        jwk = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(signing_key.public_key()))
        jwk["kid"] = "test-key"
        nonce = ""

        async def provider(_, method, endpoint, **kwargs):
            if endpoint.endswith("/.well-known/openid-configuration"):
                return {"issuer": ISSUER, "authorization_endpoint": ISSUER + "/authorize",
                        "token_endpoint": ISSUER + "/token", "jwks_uri": ISSUER + "/jwks"}
            if endpoint == ISSUER + "/jwks":
                return {"keys": [jwk]}
            self.assertEqual((method, endpoint), ("POST", ISSUER + "/token"))
            self.assertGreaterEqual(len(kwargs["data"]["code_verifier"]), 43)
            now = int(time.time())
            claims = {"iss": ISSUER, "aud": "studio-test", "sub": "uid-test",
                      "iat": now, "exp": now + 60, "nonce": nonce}
            return {"id_token": jwt.encode(claims, signing_key, algorithm="RS256", headers={"kid": "test-key"})}

        with patch.object(service, "remote_json", provider):
            start = await self.client.get("/sso/start", allow_redirects=False)
            self.assertEqual(start.status, 302)
            query = parse_qs(urlsplit(start.headers["Location"]).query)
            self.assertEqual(query["code_challenge_method"], ["S256"])
            nonce = query["nonce"][0]
            rejected = await self.client.get("/sso/callback?state=bad&code=good", allow_redirects=False)
            self.assertEqual(rejected.status, 403)
            callback = "/sso/callback?state=" + query["state"][0] + "&code=good"
            completed = await self.client.get(callback, allow_redirects=False)
            self.assertEqual(completed.status, 303)
            me = await self.client.get("/studio/me")
            self.assertEqual(await me.json(), {"actor": "oidc:uid-test", "role": "viewer"})
            replay = await self.client.get(callback, allow_redirects=False)
            self.assertEqual(replay.status, 403)
            start = await self.client.get("/sso/start", allow_redirects=False)
            state = parse_qs(urlsplit(start.headers["Location"]).query)["state"][0]
            wrong_nonce = await self.client.get("/sso/callback?state=" + state + "&code=good")
            self.assertEqual(wrong_nonce.status, 403)

    async def test_chat_sends_context_and_history_to_gemini(self):
        self.config["gemini"] = {"api_key": "test-key"}
        headers = {"Origin": self.origin}
        await self.client.post("/login", data={"username": "admin", "password": "test-admin"},
                               headers=headers, allow_redirects=False)
        history = [{"role": "user", "text": "Metrics nedir?"}, {"role": "model", "text": "Ölçümlerdir."}]

        async def generate(_, method, url, **kwargs):
            self.assertEqual(method, "POST")
            self.assertTrue(url.endswith("/gemini-3.5-flash-lite:generateContent"))
            self.assertEqual(kwargs["headers"], {"x-goog-api-key": "test-key"})
            body = kwargs["json"]
            self.assertNotIn("tools", body)
            self.assertEqual([turn["role"] for turn in body["contents"]], ["user", "model", "user"])
            return {"candidates": [{"content": {"parts": [
                {"thought": True, "text": "discard"}, {"text": "Outputs görev çıktılarıdır."}]}}]}

        with patch.object(service, "remote_json", generate):
            response = await self.client.post("/studio/chat", headers=headers,
                                              json={"prompt": "Outputs ile farkı ne?", "history": history})
            self.assertEqual(response.status, 200)
            self.assertEqual(await response.json(), {"reply": "Outputs görev çıktılarıdır."})
            invalid = await self.client.post("/studio/chat", headers=headers,
                                             json={"prompt": "Merhaba", "history": history[:1]})
            self.assertEqual(invalid.status, 400)

    async def test_gemini_draft_via_kestra(self):
        draft = "id: hello\nnamespace: examples\n"

        async def generate(request):
            payload = await request.json()
            self.assertEqual(payload["providerId"], "flowai-gemini")
            self.assertEqual(payload["userPrompt"], "Draft a log flow")
            self.assertNotIn("api_key", payload)
            return web.Response(text=draft, content_type="application/yaml")

        async def validate(request):
            self.assertEqual(await request.text(), draft)
            return web.json_response([])

        app = web.Application()
        app.router.add_post("/api/v1/main/ai/generate/flow", generate)
        app.router.add_post("/api/v1/main/flows/validate", validate)
        upstream = TestServer(app)
        await upstream.start_server()
        self.addAsyncCleanup(upstream.close)
        headers = {"Origin": self.origin}
        login = await self.client.post("/login", data={"username": "admin", "password": "test-admin"},
                                       headers=headers, allow_redirects=False)
        self.assertEqual(login.status, 303)
        args = {"json": {"prompt": "Draft a log flow"}, "headers": headers}
        missing_key = await self.client.post("/studio/copilot", **args)
        self.assertEqual(missing_key.status, 503)
        self.config["gemini"] = {"api_key": "test-key"}
        with patch.object(service, "ENGINE", str(upstream.make_url("/")).rstrip("/")):
            response = await self.client.post("/studio/copilot", **args)
            self.assertEqual(response.status, 200)
            self.assertEqual(await response.json(), {"draft": draft, "validation": []})

    async def test_agenthub_token_and_contract(self):
        async def connector(request):
            self.assertEqual(request.headers["Authorization"], "Bearer test-connector")
            self.assertEqual(await request.json(), {"prompt": "List tools"})
            return web.json_response({"reply": "Adapter received request"})

        app = web.Application()
        app.router.add_post("/agent", connector)
        upstream = TestServer(app)
        await upstream.start_server()
        self.addAsyncCleanup(upstream.close)
        self.config["agenthub"] = {"url": str(upstream.make_url("/agent")), "token": "test-connector"}
        headers = {"Origin": self.origin}
        response = await self.client.post("/login", data={"username": "admin", "password": "test-admin"},
                                          headers=headers, allow_redirects=False)
        self.assertEqual(response.status, 303)
        response = await self.client.post("/studio/agenthub", json={"prompt": "List tools"}, headers=headers)
        self.assertEqual(response.status, 200)
        self.assertEqual(await response.json(), {"reply": "Adapter received request"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
