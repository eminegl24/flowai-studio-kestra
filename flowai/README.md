# FlowAI Studio development

Open [FlowAI Studio](http://127.0.0.1:18081/ui/) on this Mac. Sign in as `admin`, `operator` or `viewer` using the matching password in the private runtime file at `../../work/flowai-runtime/config.local.json` relative to this repository. A fresh setup uses `flowai/config.local.json` by default. Set `FLOWAI_CONFIG` to use a different path. Use **Studio tools** in the sidebar for Copilot, SAP inventory, audit and AgentHub.

FlowAI Studio uses the Vue frontend and Java engine from the Apache-2.0 Kestra 1.3.48 source tag. The gateway provides independent authentication, access policies and Studio tools. The native launcher binds to loopback, stores state in a dedicated directory and protects the engine API on port 18082 with separate credentials. The existing service on port 8080 uses its own process and data.

## Build and run

Use Node 22, Python 3.13 or 3.14, Java 25, and a private writable state directory. From the repository root:

```sh
python3 flowai/setup.py
python3 -m venv ../flowai-venv
../flowai-venv/bin/pip install -r flowai/requirements.txt
HUSKY=0 npm --prefix ui ci
NODE_OPTIONS=--max-old-space-size=4096 npm --prefix ui run build -- --base=/ui/
JAVA_HOME=/path/to/jdk25 ./gradlew --no-daemon --no-build-cache shadowJar -x :ui:assembleFrontend
../flowai-venv/bin/python flowai/native.py \
  --java /path/to/jdk25/bin/java \
  --kestra build/libs/kestra-1.3.48.jar \
  --state ../flowai-runtime
```

You can also pass the official `kestra-1.3.48` executable to `--kestra`. Its SHA-256 is `15eaa2ad34cf938a8a59fe87a9d8ee86e1ab5a3df13c42c9c5c8712800a77e85`. See the [Kestra 1.3.48 release](https://github.com/kestra-io/kestra/releases/tag/v1.3.48).

Run `FLOWAI_CONFIG=/path/to/config.local.json python3 flowai/setup.py --gemini` to enter a Google Gemini API key at a hidden prompt, then restart FlowAI Studio. The editor and Studio tools use Kestra’s Gemini provider. The default model is `gemini-3.5-flash-lite`; set `gemini.model` in the private configuration to override it. Copilot sends an explicit prompt, displays a draft and checks it against the engine's validation API. The form does not save or run drafts.

**Copilot Sohbet** in Studio tools answers questions about FlowAI and explains pasted Python. It sends the current message and up to six previous turns to Gemini. History stays in the open page and can be reset with **Yeni sohbet**. It has no tools for executing code, inspecting files, or modifying workflows.

## Access and integrations

- **Roles.** Admin controls Kestra and Studio tools. Viewer can list flows and namespaces. Operator can additionally start existing flows. The gateway enforces these policies on the server. The prototype uses fixed, instance-wide roles.
- **Audit.** SQLite persists sign-ins, API and tool requests with an actor, method, path and HTTP status. The admin page shows the latest 100 events. The prototype has no export, retention controls or tamper-evident storage.
- **OIDC.** Add an `oidc` object to the local JSON file with `issuer`, `client_id`, `client_secret` and `subjects`. Map the provider's stable subject IDs to local role names. Register `http://127.0.0.1:18081/sso/callback` at a provider that permits loopback callbacks. The implementation uses HTTPS discovery and token endpoints, code flow with PKCE S256, client secret Basic authentication and RS256 ID tokens. Restart after configuration changes. The signed-token flow was tested against a simulated provider.
- **MCP.** Use `http://127.0.0.1:18081/mcp` with the bearer token in the local JSON file. The stateless HTTP endpoint implements the JSON response mode of [MCP Streamable HTTP 2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports). It exposes one tool, `inventory_sap_export`, which accepts a filename and UTF-8 export contents.
- **AgentHub.** Add an `agenthub` object with `url` and `token`, then restart. The adapter posts JSON with a `prompt` field and reads a JSON `reply` field. Place a vendor-specific translation adapter at that URL if needed. The tested contract uses a controlled HTTP service. Actual vendor integration needs an endpoint and credentials.
- **SAP Data Services.** The inventory recognizes simple ATL declarations and named XML job, workflow and dataflow elements. It generates a disabled Kestra placeholder for review. SAP transforms, mappings, datastores, schedules and dependencies still require translation. Tests use synthetic fixtures. See [SAP's export documentation](https://help.sap.com/docs/SAP_DATA_SERVICES/2d2abbb0fab34071a4c53b7de873241b/5718d4ba6d6d1014b3fc9283b0e91070.html).

The local config file contains development credentials and is ignored by Git. This setup is intended for local development. Private configuration, data, and ports must be adapted before any multi-user deployment.

## Tests

```sh
npm --prefix ui run test:unit
../flowai-venv/bin/python flowai/test_integrations.py
python3 flowai/smoke.py
node flowai/browser-smoke.mjs
```

Add `--copilot` to the HTTP smoke test to exercise the configured Google Gemini provider. The browser test uses Chrome by default. The HTTP test creates a small flow in the development namespace `flowai.tests`.
