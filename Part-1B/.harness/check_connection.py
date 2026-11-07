#!/usr/bin/env python3
"""One request to the configured model, to diagnose an INVALID evaluation run.

Human-run, outside the application. The application hides underlying error text on purpose
(ServiceError), so when every evaluation case ends in a service error this script tells you why,
printing only the error class, HTTP status and API error code. It never prints the key, the
request, or the provider's error message.

    python .harness/check_connection.py
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_env_file(path):
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        name, value = name.strip(), value.strip()
        if name and value and name not in os.environ:
            os.environ[name] = value


def main():
    load_env_file(ROOT / ".env")
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    model = os.environ.get("OPENAI_MODEL", "").strip()
    print(f"OPENAI_API_KEY: {'present' if key else 'MISSING'}")
    print(f"OPENAI_MODEL:   {model or 'MISSING'}")
    if not key or not model:
        return 2
    try:
        import openai
    except ImportError:
        print("The openai package is not installed in this environment.")
        return 2
    client = openai.OpenAI(api_key=key, timeout=30.0, max_retries=0)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Reply with a single JSON object."},
                {"role": "user", "content": 'Return {"ok": true} as JSON.'},
            ],
            response_format={"type": "json_object"},
        )
    except openai.APIStatusError as error:
        print(f"FAILED: {type(error).__name__}, HTTP {error.status_code}")
        print(f"  error code: {getattr(error, 'code', None)}  type: {getattr(error, 'type', None)}  parameter: {getattr(error, 'param', None)}")
        return 1
    except openai.OpenAIError as error:
        print(f"FAILED: {type(error).__name__} (network, timeout or client configuration)")
        return 1
    content = response.choices[0].message.content or ""
    print(f"OK: the model answered with {len(content)} characters of JSON mode output.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
