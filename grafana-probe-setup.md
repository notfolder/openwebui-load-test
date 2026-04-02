# OpenWebUI Probe - Grafana パネル追加ガイド

## 概要

openwebui-probe が定期的に API を叩いた結果を Pushgateway 経由で Prometheus に送信します。  
既存の "docker and system monitoring" ダッシュボードにパネルを追加して可視化します。

```
openwebui-probe → pushgateway:9091 → prometheus → grafana
```

### 計測メトリクス

| メトリクス名 | 内容 | 単位 |
|-------------|------|------|
| `openwebui_ttft_seconds` | 最初のトークンが届くまでの時間 | 秒 |
| `openwebui_response_total_seconds` | 全レスポンス受信までの総時間 | 秒 |
| `openwebui_probe_success` | 成功=1 / 失敗=0 | - |

---

## 1. Pushgateway の Data Source 確認

Pushgateway のメトリクスは Prometheus 経由で取得します。  
既存の Prometheus Data Source がそのまま使えます。

---

## 2. 既存ダッシュボードへのパネル追加手順

1. Grafana (http://localhost:3001) を開く
2. **"docker and system monitoring"** ダッシュボードを開く
3. 右上の **Edit** ボタンをクリック
4. **Add → Visualization** をクリック
5. 右上の Data Source が `Prometheus` になっていることを確認
6. 以下のパネルを順番に追加する

---

## 3. 追加するパネル

---

### パネル① TTFT（最初のトークンまでの時間）

| 設定項目 | 値 |
|---------|---|
| Visualization | Time series |
| Title | OpenWebUI - Time to First Token |
| Unit | `seconds (s)` |

**Metrics:**
```promql
openwebui_ttft_seconds{job="openwebui_probe"}
```

---

### パネル② 総レスポンスタイム

| 設定項目 | 値 |
|---------|---|
| Visualization | Time series |
| Title | OpenWebUI - Total Response Time |
| Unit | `seconds (s)` |

**Metrics:**
```promql
openwebui_response_total_seconds{job="openwebui_probe"}
```

---

### パネル③ TTFT と総時間の比較（1パネルにまとめる場合）

| 設定項目 | 値 |
|---------|---|
| Visualization | Time series |
| Title | OpenWebUI - Response Time |
| Unit | `seconds (s)` |

**Metrics（Query A）:**
```promql
openwebui_ttft_seconds{job="openwebui_probe"}
```
Legend: `TTFT`

**Metrics（Query B）:**
```promql
openwebui_response_total_seconds{job="openwebui_probe"}
```
Legend: `Total`

---

### パネル④ 死活監視（成功／失敗）

| 設定項目 | 値 |
|---------|---|
| Visualization | Stat |
| Title | OpenWebUI - Probe Status |
| Unit | なし |
| Value mappings | `1` → `OK` (緑) / `0` → `FAIL` (赤) |

**Metrics:**
```promql
openwebui_probe_success{job="openwebui_probe"}
```

Value mappings の設定：
1. パネル右側 **Value mappings → Add value mapping**
2. Value `1` → Display text `OK`、Color `green`
3. Value `0` → Display text `FAIL`、Color `red`

---

## 4. パネルにデータが出ない場合の確認

### Pushgateway にデータが届いているか確認

```
http://localhost:9091
```

Pushgateway の UI を開き `openwebui_probe` ジョブが表示されていればデータが届いています。

### Prometheus に入っているか確認

`http://localhost:9090/graph` で以下を実行：

```promql
openwebui_probe_success
```

値が返れば Prometheus にデータがあります。

### probe のログ確認

```bash
docker logs openwebui-probe
```

`[OK] TTFT=...s  Total=...s` が出ていれば正常に計測できています。  
`[NG]` が出ている場合は `OPENWEBUI_API_KEY` の設定を確認してください。

---

## 5. probe の設定変更

`docker-compose.yml` の environment で調整できます。

| 変数 | 初期値 | 説明 |
|-----|--------|------|
| `PROBE_INTERVAL` | `60` | 計測間隔（秒） |
| `PROBE_QUESTION` | `Hello` | 送信するメッセージ |
| `OPENWEBUI_MODEL` | `dummy:latest` | 使用するモデル名 |
| `OPENWEBUI_API_KEY` | （空） | OpenWebUI の API キー |

設定変更後は再起動が必要です：

```bash
docker compose up -d openwebui-probe
```
