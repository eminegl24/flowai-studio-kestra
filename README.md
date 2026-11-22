# FlowAI Studio

[🇹🇷 Türkçe kullanım kılavuzu](docs/flowai-studio.tr.md) · [🇬🇧 English user guide](docs/flowai-studio.en.md)

FlowAI Studio is a local workflow automation and development application built on Apache-2.0 Kestra OSS 1.3.48. This repository contains the Vue frontend, the Java workflow engine, the Python gateway and Copilot chat, plus a PostgreSQL-to-Oracle lab with synthetic data.

## Run on a Mac

Install **JDK 25**, **Node.js 22**, and **Python 3.13 or 3.14**. The optional database lab also needs **Docker Desktop**.

With access to the private GitHub repository, clone its main branch:

```sh
git clone --branch main https://github.com/eminegl24/flowai-studio-kestra.git
cd flowai-studio-kestra
./flowai/local.sh setup
./flowai/local.sh run
```

The first command installs dependencies and compiles the frontend and backend. Use `JAVA_HOME` to point at JDK 25 if it is outside the usual macOS location. The second command stays running in Terminal. Open [FlowAI Studio](http://127.0.0.1:18081/ui/), sign in as `admin`, and read the generated password under `users.admin.password` in `.flowai-local/config.local.json`.

If ports 18081 and 18082 are in use, start FlowAI with `FLOWAI_PORT=18181 FLOWAI_ENGINE_PORT=18182 ./flowai/local.sh run` and open port 18181. Set the same `FLOWAI_PORT` when importing examples.

### Optional Gemini and database lab

Run these before starting FlowAI, or stop it with **Ctrl+C** and restart it after configuration:

```sh
./flowai/local.sh gemini
./flowai/local.sh bank
```

Enter your own Gemini API key at the hidden prompt. Start Docker Desktop before running the bank command. It creates the database containers, generates independent passwords, and installs the JDBC, Python, and notification plugins used by the examples. [Bank ETL lab and DBeaver settings](examples/bank-etl/README.md)

With FlowAI running, open a **second Terminal** in the repository:

```sh
./flowai/local.sh examples
# Include the optional database lab after running the bank command:
./flowai/local.sh examples --bank
```

The optional bank examples include the connection check, customer transfer, read-only failure diagnosis, and Resend and Teams notifications. Existing flows are kept. Imported schedules and notification triggers start disabled, so review them before enabling them. Run `egitim.banka.banka_baglanti_kontrolu` and check **Outputs** for **3** PostgreSQL customers and **0** Oracle customers before loading data.

To configure the Resend example, stop FlowAI, run `./flowai/local.sh resend SENDER_EMAIL RECIPIENT_EMAIL`, enter your own sending key at the hidden prompt, then restart. Use a sender authorized by your Resend account. The Teams example requires your own `TEAMS_WEBHOOK_URL` in the local configuration's `secrets` object.

### Local state and tests

- `.flowai-local/` holds the generated credentials, runtime databases, logs and installed plugins. Keep it locally if you want to preserve your own new flows and runtime history. The database lab uses named Docker volumes.
- Git preserves source code, schema, seed data and the example flows. API keys, desktop connection profiles, runtime databases and chat history are local.
- Run backend integration tests with `.flowai-local/venv/bin/python flowai/test_integrations.py`, frontend tests with `npm --prefix ui run test:unit -- --maxWorkers=2`, and the running-instance smoke test with `FLOWAI_CONFIG="$PWD/.flowai-local/config.local.json" python3 flowai/smoke.py`.

[Technical development guide](flowai/README.md) · [Apache 2.0 license](LICENSE) · [Upstream attribution](FLOWAI-NOTICE.txt)
