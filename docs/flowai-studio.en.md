# FlowAI Studio user guide

[English](flowai-studio.en.md) · [Türkçe](flowai-studio.tr.md) · [Setup overview](../README.md)

FlowAI Studio is a local environment for authoring, scheduling and monitoring workflows in a browser. Its workflow engine is based on Apache-2.0 Kestra OSS 1.3.48. The PostgreSQL → Oracle lab is one of the bundled examples and uses synthetic data.

## 1. Set up on a Mac

You need access to the private GitHub repository, JDK 25, Node.js 22 and Python 3.13 or 3.14. The database lab also requires Docker Desktop.

```bash
git clone --branch main https://github.com/eminegl24/flowai-studio-kestra.git
cd flowai-studio-kestra
./flowai/local.sh setup
./flowai/local.sh run
```

[Open FlowAI Studio](http://127.0.0.1:18081/ui/main/welcome). The generated password for `admin` is in `users.admin.password` in your own `.flowai-local/config.local.json` file. The app runs while the Terminal process is open. Press **Ctrl+C** to stop it. The first build can take longer because it downloads dependencies. If Java is unavailable, set `JAVA_HOME` to your JDK 25 directory.

The interface uses port **18081** and the internal engine uses **18082** by default. For alternate ports, run `FLOWAI_PORT=18181 FLOWAI_ENGINE_PORT=18182 ./flowai/local.sh run`. Use the same `FLOWAI_PORT` when importing examples.

## 2. Run your first flow

1. On the **AI Copilot** page, select **Write a log message** or choose **Start a Tutorial** for a guided exercise.
2. Inspect the **Flow Code** pane in the editor. A flow has an `id`, a `namespace` and `tasks`.
3. Choose **Save → Execute**. Complete the input form if the example has inputs.
4. Open **Executions → latest run → Logs** to find the message. A **SUCCESS** state means the task completed.

Submitting an unchanged suggestion opens a bundled example. To generate a YAML draft with Gemini, use your own prompt in the **editor Copilot**. To configure Gemini, stop the app, run `./flowai/local.sh gemini`, enter your own API key at the hidden prompt and restart the app.

```yaml
id: first_hello
namespace: training.basics
tasks:
  - id: write_message
    type: io.kestra.plugin.core.log.Log
    message: Hello, FlowAI!
```

A `namespace` groups flows. The `main` part of a local URL identifies the top-level workspace. An **Execution ID** identifies one run and is generated automatically. Use **Execution labels** to add a searchable tag such as `purpose=first_test`.

## 3. Find your way around

| Screen | What to use it for |
|---|---|
| **Flows → Edit** | Edit YAML and inspect earlier saved versions in **Revisions**. |
| **Topology** | See task order and dependencies. |
| **Executions → Overview / Gantt** | Check the result, start time and task durations. |
| **Logs / Outputs / Metrics** | Inspect messages and errors, task data and files, or measurements. |
| **Debug Expression** | Evaluate a Pebble expression against the current execution context. |
| **Triggers** | Check what starts a flow. Use **Tenant → Triggers** to see schedules together. |
| **Blueprints → Community** | Browse example workflows and dashboards. Check plugin and connection requirements before running a template. |
| **Tenant → KV Store** | Store nonsecret operational values, such as the date of the last successful transfer. |
| **Studio Tools** | Open local audit activity, the SAP inventory and the AgentHub adapter. |

Use **Copilot Sohbet** to describe a job, ask about a screen or explain a failure. When you provide the full name of a saved flow, the app can inspect the source revision used by its latest execution locally and give Gemini a task summary and recognized error codes. It does not automatically send raw logs or saved YAML. Chat checks candidate code and may withhold code when an execution test is unavailable. For a reviewable draft in the workspace, use **Flow Code → AI Copilot**. Keep real customer records, passwords and API keys out of chat prompts.

## 4. PostgreSQL → Oracle lab

1. Start Docker Desktop. Stop FlowAI and run `./flowai/local.sh bank` to provision the training databases, local secrets and example plugins.
2. Restart FlowAI and run `./flowai/local.sh examples --bank` in a second Terminal. Existing flows with the same identifiers are preserved.
3. Execute `egitim.banka.banka_baglanti_kontrolu`. A fresh lab has **3** source customers and **0** target customers.
4. Open `egitim.banka.postgres_to_oracle_transactions`. Despite its historical identifier, the saved example in the repository transfers the **customer table**. Run it and verify the target through **Outputs**, **Logs**, or DBeaver.

| Connection | Local address | User |
|---|---|---|
| PostgreSQL | `127.0.0.1:15432/bank_source` | `bank_source` |
| Oracle | `127.0.0.1:11521/FREEPDB1` | `bank_dwh` |

See the [lab guide](../examples/bank-etl/README.md) for DBeaver settings and load options. If you build a flow that also loads accounts and transactions, load **customers → accounts → transactions** in that order. Oracle error `ORA-02291` indicates a missing parent record.

## 5. Schedule, monitor and notify

For a repeating schedule, use a **Schedule** trigger in the flow. The demo uses `cron: "0 8 * * *"` and `timezone: Europe/Istanbul` for **08:00 Istanbul time**. Imported triggers start disabled. Run a manual test first, then enable the trigger in **Triggers** and check the next run time. **Execute → Schedule date** schedules one run. **Backfill** creates runs for past schedule intervals. To process historical data, the query must use the scheduled date.

| Flow | What it does | Setup |
|---|---|---|
| `postgres_to_oracle_bildirim` | Logs the transfer result, then sends an email through Resend. | Run `./flowai/local.sh resend SENDER_EMAIL RECIPIENT_EMAIL` with your own credentials, restart FlowAI and enable the trigger. |
| `postgres_to_oracle_teams_bildirim` | Sends the result to a Teams channel. | Add your Teams Workflows URL as the local `TEAMS_WEBHOOK_URL` secret, restart FlowAI and enable the trigger. |
| `postgres_to_oracle_teshis` | Uses read-only queries to check whether accounts referenced by source payments exist in Oracle after a failed transfer. | Enable the trigger or enter a previous transfer’s `source_execution_id` for a manual test. |

To test the notification chain, manually start the **source transfer**. Running the notification flow directly produces a test log. Actual Teams delivery requires channel access and a valid Workflows URL. The diagnosis flow reports missing accounts. Automatic repair and rerun are outside this example.

## 6. Administration, data and integrations

- **Roles** — `admin` manages the app, `operator` can start existing flows, and `viewer` can inspect them. The local gateway enforces these roles. Accounts and secrets are stored in local configuration.
- **Audit** — An admin can open **Studio Tools → Load recent activity**. Task messages are in the corresponding **Execution → Logs** view.
- **AgentHub** — **Studio Tools** can send an HTTP request to an agent. The adapter was tested with a controlled service. Your organization’s URL, authorization and any request-format mapping are needed for a real connection.
- **MCP and SAP** — The MCP tool inventories ATL/XML exports. The inventory and starter flow do not translate every SAP transform or mapping.
- **Local files** — `.flowai-local/` holds credentials, execution history and plugins. The database lab uses Docker volumes. Git contains source, schema and sample data.

This setup is intended for local development. For a shared or production deployment, review access, identity management, retention and operations with your team. [Technical development guide](../flowai/README.md) · [Upstream attribution](../FLOWAI-NOTICE.txt) · [Apache 2.0 license](../LICENSE)

## 7. Troubleshooting

| Symptom | First check |
|---|---|
| **The page does not open** | Confirm that `local.sh run` is running. Check `.flowai-local/studio.log` and `.flowai-local/engine.log`. |
| **Invalid type / No plugin registered** | The requested task plugin may be missing. For the lab, complete `local.sh bank` and restart. |
| **Flow Code shows a red warning** | Paste YAML into the flow editor. Indent Python code under `script: |` inside a Python task. |
| **Execute succeeded but no notification arrived** | Inspect the transfer and notification runs separately. Check the Resend sender and recipient or the Teams URL. A direct manual notification test only logs a preview. |
| **A daily job did not run** | In **Tenant → Triggers**, check whether the trigger is enabled, its time zone and its next run time. The local app must be running at the scheduled time. |
