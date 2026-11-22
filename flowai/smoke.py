"""Exercise the running FlowAI instance and its Kestra engine."""
import argparse
from http.cookiejar import CookieJar
import json
import os
from pathlib import Path
import time
import unittest
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import build_opener, HTTPCookieProcessor, HTTPRedirectHandler, Request
from uuid import uuid4

URL = "http://127.0.0.1:18081"
CONFIG = json.loads(Path(os.environ.get("FLOWAI_CONFIG", Path(__file__).with_name("config.local.json"))).read_text())
XML = '<export><job name="Daily"><workflow name="Load"/><dataflow name="Extract"/></job></export>'
API = "/api/v1/main"
TEST_COPILOT = False


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def client():
    return build_opener(NoRedirect(), HTTPCookieProcessor(CookieJar()))


def request(browser, path, method="GET", body=None, headers=None):
    if isinstance(body, dict):
        headers = {"Content-Type": "application/json", **(headers or {})}
        body = json.dumps(body).encode()
    req = Request(URL + path, data=body, method=method, headers=headers or {})
    try:
        response = browser.open(req, timeout=125)
    except HTTPError as error:
        response = error
    with response:
        content = response.read()
        if "application/json" in response.headers.get("Content-Type", ""):
            content = json.loads(content)
        return response.status, content


def sign_in(role):
    browser = client()
    credentials = urlencode({"username": role, "password": CONFIG["users"][role]["password"]})
    status, _ = request(browser, "/login", "POST", credentials.encode(),
                        {"Content-Type": "application/x-www-form-urlencoded", "Origin": URL})
    if status != 303:
        raise RuntimeError(f"Sign-in failed for {role} with HTTP {status}")
    return browser


class StudioSmokeTest(unittest.TestCase):
    def test_auth_and_branding(self):
        self.assertEqual(request(client(), API + "/flows/search")[0], 401)
        self.assertEqual(request(client(), "/ui/")[0], 303)
        admin = sign_in("admin")
        status, markup = request(admin, "/ui/main/flows")
        self.assertEqual(status, 200)
        self.assertIn(b"<title>FlowAI Studio</title>", markup)
        self.assertEqual(request(admin, "/studio/me"), (200, {"actor": "admin", "role": "admin"}))
        self.assertEqual(request(admin, "/logout", "POST")[0], 403)
        self.assertEqual(request(admin, "/logout", "POST", headers={"Origin": URL})[0], 303)
        self.assertEqual(request(admin, "/studio/me")[0], 401)

    def test_roles_execution_and_audit(self):
        admin, viewer, operator = (sign_in(role) for role in ("admin", "viewer", "operator"))
        flow_id = "smoke_" + uuid4().hex[:10]
        payload = f"""id: {flow_id}
namespace: flowai.tests
tasks:
  - id: greeting
    type: io.kestra.plugin.core.log.Log
    message: FlowAI smoke test
""".encode()
        headers = {"Content-Type": "application/x-yaml", "Origin": URL}
        self.assertEqual(request(viewer, API + "/flows/search")[0], 200)
        self.assertEqual(request(viewer, API + "/flows", "POST", payload, headers)[0], 403)
        self.assertEqual(request(operator, API + "/flows", "POST", payload, headers)[0], 403)
        status, details = request(admin, API + "/flows", "POST", payload, headers)
        self.assertEqual(status, 200, details)
        execute = API + "/executions/flowai.tests/" + flow_id
        self.assertEqual(request(viewer, execute, "POST", b"", {"Origin": URL})[0], 403)
        status, execution = request(
            operator, execute, "POST", b"--flowai-smoke--\r\n",
            {"Origin": URL, "Content-Type": "multipart/form-data; boundary=flowai-smoke"},
        )
        self.assertIn(status, (200, 201), execution)
        for _ in range(40):
            status, details = request(admin, API + "/executions/" + execution["id"])
            self.assertEqual(status, 200, details)
            if details["state"]["current"] == "SUCCESS":
                break
            time.sleep(0.25)
        self.assertEqual(details["state"]["current"], "SUCCESS")
        self.assertEqual(request(viewer, "/studio/audit")[0], 403)
        status, activities = request(admin, "/studio/audit")
        self.assertEqual(status, 200)
        self.assertTrue(any(row["actor"] == "viewer" and row["route"] == execute and
                            row["status"] == 403 for row in activities))
        self.assertTrue(any(row["actor"] == "operator" and row["route"] == execute and
                            row["status"] in (200, 201) for row in activities))

    def test_migration_and_mcp(self):
        admin = sign_in("admin")
        status, result = request(admin, "/studio/migration", "POST",
                                 {"filename": "jobs.xml", "source": XML}, {"Origin": URL})
        self.assertEqual(status, 200, result)
        self.assertEqual([entry["kind"] for entry in result["objects"]], ["job", "workflow", "dataflow"])
        self.assertIn("disabled: true", result["draft"])
        self.assertEqual(request(admin, "/studio/migration", "POST", {
            "filename": "unsafe.xml", "source": '<!DOCTYPE x [<!ENTITY a "blocked">]><x>&a;</x>',
        }, {"Origin": URL})[0], 400)
        self.assertEqual(request(client(), "/mcp", "POST", {})[0], 401)
        headers = {"Authorization": "Bearer " + CONFIG["mcp_token"],
                   "Accept": "application/json, text/event-stream",
                   "MCP-Protocol-Version": "2025-06-18"}
        def call(method, params=None):
            status, body = request(client(), "/mcp", "POST",
                                   {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}, headers)
            self.assertEqual(status, 200, body)
            return body["result"]
        self.assertEqual(call("initialize")["protocolVersion"], "2025-06-18")
        self.assertEqual(call("tools/list")["tools"][0]["name"], "inventory_sap_export")
        result = call("tools/call", {"name": "inventory_sap_export", "arguments": {
            "filename": "jobs.atl", "source": 'CREATE AL_JOB "Daily Load"\nAL_DATAFLOW Extract'}})
        self.assertEqual(json.loads(result["content"][0]["text"])["objects"][0]["name"], "Daily Load")

    def test_optional_gemini(self):
        if not TEST_COPILOT:
            self.skipTest("Enable with --copilot")
        status, result = request(sign_in("admin"), "/studio/copilot", "POST",
                                 {"prompt": "Write a minimal log-only Kestra flow to print hello."}, {"Origin": URL})
        self.assertEqual(status, 200, result)
        self.assertIn("io.kestra.plugin.core.log.Log", result["draft"])
        self.assertEqual(len(result["validation"]), 1, result)
        self.assertFalse(result["validation"][0].get("constraints"), result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--copilot", action="store_true")
    args, rest = parser.parse_known_args()
    TEST_COPILOT = args.copilot
    unittest.main(argv=[__file__, *rest], verbosity=2)
