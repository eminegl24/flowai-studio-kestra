"""Run FlowAI Studio and its private Kestra engine in a dedicated state directory."""
import argparse
import base64
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--java", required=True, type=Path)
parser.add_argument("--kestra", required=True, type=Path)
parser.add_argument("--state", required=True, type=Path)
args = parser.parse_args()
state = args.state.resolve()
state.mkdir(mode=0o700, parents=True, exist_ok=True)
config_path = Path(os.environ.get("FLOWAI_CONFIG", ROOT / "config.local.json")).resolve()
config = json.loads(config_path.read_text())
engine_account = config["engine_account"]
gateway_port = int(os.environ.get("FLOWAI_PORT", "18081"))
engine_port = int(os.environ.get("FLOWAI_ENGINE_PORT", "18082"))
if not (0 < gateway_port <= 65535 and 0 < engine_port <= 65535 and gateway_port != engine_port):
    parser.error("FlowAI gateway and engine must use different valid TCP ports")
engine_config = state / "engine.yml"
engine_settings = {
    "micronaut": {"server": {"host": "127.0.0.1", "port": engine_port}},
    "kestra": {
        "tutorial-flows": {"enabled": False},
        "anonymous-usage-report": {"enabled": False},
        "server": {"basic-auth": {
            "username": engine_account["login"], "password": engine_account["password"],
            "open-urls": ["/ping"],
        }},
    },
}
gemini = config.get("gemini", {})
if gemini.get("api_key"):
    engine_settings["kestra"]["ai"] = {
        "providers": [{
            "id": "flowai-gemini",
            "display-name": "Google Gemini",
            "type": "gemini",
            "is-default": True,
            "configuration": {
                "apiKey": gemini["api_key"],
                "modelName": gemini.get("model") or "gemini-3.5-flash-lite",
            },
        }],
    }
engine_config.write_text(json.dumps(engine_settings))
engine_config.chmod(0o600)


def stop(*_):
    raise KeyboardInterrupt


signal.signal(signal.SIGTERM, stop)
engine_env = dict(os.environ, HOME=str(state), XDG_CACHE_HOME=str(state / "cache"))
for name, value in config.get("secrets", {}).items():
    engine_env["SECRET_" + name] = base64.b64encode(value.encode()).decode()
plugins = state / "plugins"
if plugins.is_dir():
    engine_env.setdefault("KESTRA_PLUGINS_PATH", str(plugins))
gateway_env = dict(os.environ, FLOWAI_CONFIG=str(config_path), FLOWAI_DB=str(state / "studio.sqlite3"),
                   FLOWAI_UI=str(ROOT.parent / "webserver/src/main/resources/ui"),
                   FLOWAI_ENGINE=f"http://127.0.0.1:{engine_port}", FLOWAI_BIND="127.0.0.1",
                   FLOWAI_PORT=str(gateway_port), FLOWAI_ORIGIN=f"http://127.0.0.1:{gateway_port}")
with (state / "engine.log").open("a") as engine_log, (state / "studio.log").open("a") as studio_log:
    commands = [
        ([str(args.java.resolve()), "-Xmx2g", "-Duser.home=" + str(state), "-jar",
          str(args.kestra.resolve()), "server", "local", "--config", str(engine_config)], engine_env, engine_log),
        ([sys.executable, str(ROOT / "service.py")], gateway_env, studio_log),
    ]
    children = []
    try:
        for command, env, log in commands:
            children.append(subprocess.Popen(command, cwd=state, env=env, stdout=log, stderr=subprocess.STDOUT))
        while all(child.poll() is None for child in children):
            time.sleep(0.5)
        raise SystemExit("A FlowAI process exited. See the logs in the state directory.")
    except KeyboardInterrupt:
        pass
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
