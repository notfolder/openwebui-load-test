# 1. ベースイメージを選択
# conda-forge提供のminiforge3イメージを使用
FROM condaforge/miniforge3:latest

# 2. 作業ディレクトリを設定
WORKDIR /app

# 3. 依存関係ファイル(environment.yml)をコピー
COPY environment.yml .

# 4. conda環境を更新し、依存ライブラリをインストール
# environment.ymlを元にbase環境を更新し、不要なキャッシュは削除する
RUN conda env update -n base -f environment.yml && \
    conda clean -afy

# 5. アプリケーションコードをコピー
COPY ollama-mock.py /app

# 6. アプリケーションが使用するポートを公開
EXPOSE 11434

# 7. Gunicornのワーカ数を環境変数で設定（デフォルトは4）
ENV GUNICORN_WORKERS=21

# 8. コンテナ起動時に実行するコマンド
# miniforgeの環境ではcondaが有効になっているため、直接gunicornを呼び出せる
# CMD ["gunicorn", "--worker-class", "gevent", "--workers", "$GUNICORN_WORKERS", "--bind", "0.0.0.0:11434", "ollama-mock:app"]
CMD gunicorn --worker-class gevent --workers $GUNICORN_WORKERS --bind 0.0.0.0:11434 ollama-mock:app
