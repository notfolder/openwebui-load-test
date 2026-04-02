import os
import time
import json
import requests
import urllib3
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OPENWEBUI_URL   = os.getenv("OPENWEBUI_URL",    "http://nginx")
OPENWEBUI_API_KEY = os.getenv("OPENWEBUI_API_KEY", "")
OPENWEBUI_MODEL = os.getenv("OPENWEBUI_MODEL",  "dummy:latest")
PUSHGATEWAY_URL = os.getenv("PUSHGATEWAY_URL",  "http://pushgateway:9091")
PROBE_INTERVAL  = int(os.getenv("PROBE_INTERVAL", "60"))
PROBE_QUESTION  = os.getenv("PROBE_QUESTION",   "Hello")


def log_diagnostics():
    print("=== 診断情報 ===", flush=True)
    print(f"  OPENWEBUI_URL    : {OPENWEBUI_URL}", flush=True)
    print(f"  OPENWEBUI_MODEL  : {OPENWEBUI_MODEL}", flush=True)
    print(f"  API_KEY set      : {bool(OPENWEBUI_API_KEY)}", flush=True)
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "NO_PROXY", "no_proxy"):
        val = os.getenv(key)
        if val:
            print(f"  [PROXY ENV] {key}={val}", flush=True)
    print("================", flush=True)


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
    target_url = f"{OPENWEBUI_URL}/api/chat/completions"
    print(f"[REQ] POST {target_url}", flush=True)

    try:
        with requests.post(
            target_url,
            headers=headers,
            json=body,
            stream=True,
            timeout=120,
            proxies={"http": None, "https": None},  # プロキシ環境変数を無視
            verify=False,                            # 自己署名証明書を許可
        ) as resp:
            print(f"[RES] status={resp.status_code} url={resp.url}", flush=True)
            if resp.history:
                for r in resp.history:
                    print(f"[REDIRECT] {r.status_code} {r.url} -> {r.headers.get('Location')}", flush=True)
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
        import traceback
        total = time.monotonic() - start
        g_ttft.set(0)
        g_total.set(total)
        g_success.set(0)
        print(f"[NG]  {exc}", flush=True)
        traceback.print_exc()

    push_to_gateway(PUSHGATEWAY_URL, job="openwebui_probe", registry=registry)


if __name__ == "__main__":
    print(f"Probe started  url={OPENWEBUI_URL}  model={OPENWEBUI_MODEL}"
          f"  interval={PROBE_INTERVAL}s", flush=True)
    log_diagnostics()
    while True:
        try:
            probe()
        except Exception as exc:
            print(f"[ERROR] {exc}", flush=True)
        time.sleep(PROBE_INTERVAL)
