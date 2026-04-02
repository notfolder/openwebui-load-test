import os
import time
import json
import requests
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

OPENWEBUI_URL   = os.getenv("OPENWEBUI_URL",    "http://nginx")
OPENWEBUI_API_KEY = os.getenv("OPENWEBUI_API_KEY", "")
OPENWEBUI_MODEL = os.getenv("OPENWEBUI_MODEL",  "dummy:latest")
PUSHGATEWAY_URL = os.getenv("PUSHGATEWAY_URL",  "http://pushgateway:9091")
PROBE_INTERVAL  = int(os.getenv("PROBE_INTERVAL", "60"))
PROBE_QUESTION  = os.getenv("PROBE_QUESTION",   "Hello")


def probe():
    registry  = CollectorRegistry()
    g_ttft    = Gauge("openwebui_ttft_seconds",
                      "Time to first token (seconds)", registry=registry)
    g_total   = Gauge("openwebui_response_total_seconds",
                      "Total response time (seconds)",  registry=registry)
    g_success = Gauge("openwebui_probe_success",
                      "Probe result: 1=success, 0=failure", registry=registry)

    headers = {"Content-Type": "application/json"}
    if OPENWEBUI_API_KEY:
        headers["Authorization"] = f"Bearer {OPENWEBUI_API_KEY}"

    body = {
        "model":    OPENWEBUI_MODEL,
        "messages": [{"role": "user", "content": PROBE_QUESTION}],
        "stream":   True,
    }

    ttft  = None
    start = time.monotonic()

    try:
        with requests.post(
            f"{OPENWEBUI_URL}/api/chat/completions",
            headers=headers,
            json=body,
            stream=True,
            timeout=120,
        ) as resp:
            resp.raise_for_status()

            for raw in resp.iter_lines():
                if not raw:
                    continue
                line = raw.decode("utf-8")
                if not line.startswith("data: "):
                    continue
                payload = line[6:]
                if payload == "[DONE]":
                    break
                try:
                    chunk = json.loads(payload)
                    if ttft is None:
                        content = (
                            chunk.get("choices", [{}])[0]
                            .get("delta", {})
                            .get("content", "")
                        )
                        if content:
                            ttft = time.monotonic() - start
                except json.JSONDecodeError:
                    pass

        total = time.monotonic() - start
        g_ttft.set(ttft if ttft is not None else 0)
        g_total.set(total)
        g_success.set(1)
        print(f"[OK]  TTFT={ttft:.3f}s  Total={total:.3f}s", flush=True)

    except Exception as exc:
        total = time.monotonic() - start
        g_ttft.set(0)
        g_total.set(total)
        g_success.set(0)
        print(f"[NG]  {exc}", flush=True)

    push_to_gateway(PUSHGATEWAY_URL, job="openwebui_probe", registry=registry)


if __name__ == "__main__":
    print(f"Probe started  url={OPENWEBUI_URL}  model={OPENWEBUI_MODEL}"
          f"  interval={PROBE_INTERVAL}s", flush=True)
    while True:
        try:
            probe()
        except Exception as exc:
            print(f"[ERROR] {exc}", flush=True)
        time.sleep(PROBE_INTERVAL)
