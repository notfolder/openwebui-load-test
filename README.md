Grafana起動後、http://localhost:3001 にアクセスし：

ID: admin / PW: admin

DataSource に Prometheus を追加（http://prometheus:9090）

ダッシュボードテンプレート例：

893：Docker Container Stats

17452：NGINX metrics dashboard

 Grafana に nginx ダッシュボードを追加
方法：
Grafana の + → Import

ダッシュボード ID：17452

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

ID 893 “Docker and system monitoring” – cAdvisor を前提とした Docker ホストおよびコンテナ両方の主要リソースを一画面で可視化できる（Apache‐ライセンス）
grafana.com

ID 13946 “Docker-cAdvisor” – Grafana Labs 公式が公開するテンプレートで、cAdvisor からの指標を集約し、CPU・メモリ・ネットワーク・ディスク I/O を網羅的に表示できる
