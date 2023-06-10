# PandA to TickTick

## 概要

-   PandA から課題を取得する
-   ~~TickTick~~（現在はNotion）に課題を登録する

## 変更点

2023/06/10

-   何故か TickTick の API に接続できなくなった
    -   Notion に移行することにした

## 使い方

-   このリポジトリをクローンする
-   `pip install -r requirements.txt`で必要なライブラリをインストールする
-   .env ファイルを作成し、以下のように記述する
    ```
    PANDA_USER_NAME=******* # PandAのユーザー名
    PANDA_PASSWORD=******* # PandAのパスワード
    NOTION_SECRET=******* # Notionのシークレット
    NOTION_DB_ID=******* # NotionのデータベースID
    ```
-   `python main.py`で実行する
