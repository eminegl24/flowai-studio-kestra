#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
runtime="${FLOWAI_STATE:-$root/.flowai-local}"
mkdir -p -m 700 "$runtime"
runtime="$(cd "$runtime" && pwd)"
export FLOWAI_CONFIG="${FLOWAI_CONFIG:-$runtime/config.local.json}"
backend="$root/build/libs/kestra-1.3.48.jar"
bank="$root/examples/bank-etl"

find_java() {
    if [[ -z "${JAVA_HOME:-}" && -x /usr/libexec/java_home ]]; then
        JAVA_HOME="$(/usr/libexec/java_home -v 25 2>/dev/null || true)"
        export JAVA_HOME
    fi
    java="${JAVA_HOME:+$JAVA_HOME/bin/}java"
    local java_version
    java_version="$("$java" -version 2>&1 || true)"
    if [[ ! "$java_version" =~ version\ \"25[.\"] ]]; then
        printf '%s\n' 'Java 25 is required. Set JAVA_HOME to your JDK 25 installation.' >&2
        exit 1
    fi
}

case "${1:-}" in
    setup)
        find_java
        python3 flowai/setup.py
        python3 -m venv "$runtime/venv"
        "$runtime/venv/bin/python" -m pip install -r flowai/requirements.txt
        HUSKY=0 npm --prefix ui ci
        NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=4096}" npm --prefix ui run build -- --base=/ui/
        GRADLE_USER_HOME="$runtime/gradle" ./gradlew --no-daemon --no-build-cache shadowJar -x :ui:assembleFrontend
        ;;
    run)
        find_java
        if [[ ! -f "$backend" || ! -x "$runtime/venv/bin/python" ]]; then
            printf '%s\n' 'Run flowai/local.sh setup first.' >&2
            exit 1
        fi
        java_path="$(command -v "$java")"
        exec "$runtime/venv/bin/python" flowai/native.py --java "$java_path" --kestra "$backend" --state "$runtime"
        ;;
    gemini)
        exec python3 flowai/setup.py --gemini
        ;;
    resend)
        if [[ $# -ne 3 ]]; then
            printf '%s\n' 'Usage: flowai/local.sh resend SENDER_EMAIL RECIPIENT_EMAIL' >&2
            exit 2
        fi
        exec python3 flowai/setup.py --resend-from "$2" --resend-to "$3"
        ;;
    bank)
        find_java
        if [[ ! -f "$backend" ]]; then
            printf '%s\n' 'Run flowai/local.sh setup first.' >&2
            exit 1
        fi
        python3 "$bank/setup.py"
        docker compose -f "$bank/compose.yaml" --env-file "$bank/.env" up -d --wait
        python3 flowai/setup.py --bank-lab "$bank/.env"
        "$java" "-Duser.home=$runtime" -jar "$backend" plugins install \
            io.kestra.plugin:plugin-jdbc-postgres:1.15.10 io.kestra.plugin:plugin-jdbc-oracle:1.15.10 \
            io.kestra.plugin:plugin-script-python:1.18.9 io.kestra.plugin:plugin-resend:1.4.3 \
            io.kestra.plugin:plugin-prefect:1.4.4 io.kestra.plugin:plugin-jdbc-mariadb:1.15.10 \
            io.kestra.plugin:plugin-slack:1.4.6 \
            --plugins "$runtime/plugins" --repositories=https://repo.maven.apache.org/maven2
        ;;
    examples)
        exec "$runtime/venv/bin/python" flowai/import_examples.py "${@:2}"
        ;;
    *)
        printf '%s\n' 'Usage: flowai/local.sh {setup|run|gemini|resend|bank|examples}' >&2
        exit 2
        ;;
esac
