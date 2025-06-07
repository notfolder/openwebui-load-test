Grafana起動後、http://localhost:3001 にアクセスし：

ID: admin / PW: admin

DataSource に Prometheus を追加
http://prometheus:9090

ダッシュボードテンプレート例：

893：Docker Container Stats

17452：NGINX metrics dashboard

 Grafana に nginx ダッシュボードを追加
方法：
Grafana の + → Import

ダッシュボード ID： 17452

Grafana.com ダッシュボード 11865

データソースに Prometheus を指定


ステップ 1：Grafana にログイン
ブラウザで Grafana を開きます

arduino
コピーする
編集する
http://localhost:3001
初期ユーザー名・パスワードは admin / admin（変更済みであればそれに従う）

✅ ステップ 2：Nginxダッシュボードのインポート
左サイドバーの 「+（Create）」→「Import」 をクリック

「Import via grafana.com」 の欄に以下の ダッシュボードID を入力：

17452
ダッシュボード名: NGINX Prometheus Exporter Dashboard

「Load」ボタンを押すと、インポート画面に遷移します

✅ ステップ 3：データソース選択
Prometheus をデータソースとして選択します（事前に登録されていれば選択肢に表示されます）

「Import」をクリック

✅ ステップ 4：表示されるグラフ例
以下のような指標が自動でグラフ化されます：

グラフ	説明
Active Connections	現在の接続数
Accepted / Handled Connections	リクエスト数の推移
Reading / Writing / Waiting	状態別接続数（処理中など）
Request Rate, Bytes	トラフィック関連

1. ID 13496 「Docker and system monitoring」（推奨）

container_labels が空の場合、ダッシュボード中の「ラベル付きフィルタ」部分だけが一部 N/A になりますが、パネル自体は sum by (container_name) (…) のように既存のクエリに置き換えることで動作します。

たとえば、CPU 使用率パネルのクエリを以下のように書き直せば、ラベルが存在しない環境でもコンテナごとの CPU ゲージが得られます：

promql
コピーする
編集する
sum by (container_name) (
  rate(container_cpu_usage_seconds_total{container_name!=""}[1m])
) * 100
