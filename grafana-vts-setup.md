# Nginx VTS - Grafana 設定ガイド

## 構成概要

nginx-module-vts が `/metrics` エンドポイントで Prometheus 形式のメトリクスを直接公開します。  
外部 exporter コンテナは不要です。

```
nginx:80/metrics  ←  Prometheus (scrape)  →  Grafana
```

---

## 1. Data Source の設定

1. Grafana (http://localhost:3001) に admin / admin でログイン
2. **Connections → Data Sources → Add data source**
3. `Prometheus` を選択
4. 以下を設定して **Save & Test**

| 項目 | 値 |
|-----|---|
| Name | Prometheus |
| URL  | `http://prometheus:9090` |

---

## 2. ダッシュボードのインポート

**Dashboards → Import → Dashboard IDを入力 → Load**

### 推奨ダッシュボード

| ID | 名前 | 特徴 |
|----|------|------|
| **2949** | Nginx VTS Stats | 定番。リクエスト数・レスポンスタイム・接続数 |
| **11967** | Nginx VTS/STS Performance Metrics | upstream 詳細・レスポンスタイム中心 |
| **24237** | Nginx VTS - Comprehensive Monitoring | 最も詳細。キャッシュ・ステータスコード分布 |

---

## 3. 主なメトリクス一覧

### リクエスト・レスポンス

```promql
# 総リクエスト数 (1分間のレート)
rate(nginx_vts_server_requests_total[1m])

# ステータスコード別リクエスト数
rate(nginx_vts_server_requests_total{code!="total"}[1m])
```

### レスポンスタイム

```promql
# upstream 平均レスポンスタイム (ms)
nginx_vts_upstream_response_msecs_avg

# upstream レスポンスタイム ヒストグラム (p95算出例)
histogram_quantile(0.95,
  rate(nginx_vts_upstream_response_msecs_bucket[5m])
)
```

### 接続数

```promql
# アクティブ接続数
nginx_vts_server_connections{status="active"}

# 接続ステータス別
nginx_vts_server_connections
```

### 転送量

```promql
# 受信バイト数レート
rate(nginx_vts_server_bytes_total{direction="in"}[1m])

# 送信バイト数レート
rate(nginx_vts_server_bytes_total{direction="out"}[1m])
```

---

## 4. メトリクス取得確認

コンテナ起動後、以下で動作確認できます。

```bash
# VTS Prometheus 形式の出力確認
curl http://localhost/metrics | grep nginx_vts

# Prometheus に入っているか確認
curl 'http://localhost:9090/api/v1/label/__name__/values' \
  | python3 -m json.tool | grep nginx_vts
```

---

## 5. ダッシュボードのパネルが空の場合

VTS モジュールのバージョンによってメトリクス名が異なる場合があります。  
パネル編集 (Edit) → Metrics Browser で以下を確認してください。

| 確認コマンド |
|------------|
| `curl http://localhost/metrics \| grep "^nginx_vts" \| head -30` |

表示されたメトリクス名をパネルの PromQL に合わせて修正してください。
