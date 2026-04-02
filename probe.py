import os
import signal
import time
import json
import threading
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
        ttft_val = ttft if ttft is not None else 0.0
        print(f"[OK]  TTFT={ttft_val:.3f}s  Total={total:.3f}s", flush=True)

    except Exception as exc:
        import traceback
        total = time.monotonic() - start
        g_ttft.set(0)
        g_total.set(total)
        g_success.set(0)
        print(f"[NG]  {exc}", flush=True)
        traceback.print_exc()

    def _no_proxy_handler(url, method, timeout, headers, data):
        resp = requests.request(
            method, url,
            headers=dict(headers) if headers else {},
            data=data,
            timeout=timeout or 30,
            proxies={"http": None, "https": None},
            verify=False,
        )
        if resp.status_code >= 400:
            raise OSError(f"push_to_gateway error {resp.status_code}: {resp.text}")

    push_to_gateway(PUSHGATEWAY_URL, job="openwebui_probe", registry=registry,
                    handler=_no_proxy_handler)


if __name__ == "__main__":
    stop_event = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())
    signal.signal(signal.SIGINT,  lambda *_: stop_event.set())

    print(f"Probe started  url={OPENWEBUI_URL}  model={OPENWEBUI_MODEL}"
          f"  interval={PROBE_INTERVAL}s", flush=True)
    log_diagnostics()

    while not stop_event.is_set():
        try:
            probe()
        except Exception as exc:
            import traceback
            print(f"[ERROR] {exc}", flush=True)
            traceback.print_exc()
        stop_event.wait(timeout=PROBE_INTERVAL)

    print("Probe stopped.", flush=True)
