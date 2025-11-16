# Kindle自動スクリーンショット＆PDF化システム

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Windows版Kindleアプリから1ページずつ自動でスクリーンショットを取得し、1冊の本を1つのPDFファイルにまとめるシステムです。

## 機能

- **自動ページキャプチャ**: Kindleアプリのページを自動でキャプチャ
- **自動ページめくり**: 右矢印キーでページを自動でめくり
- **完了判定**: 同じページが3回連続で表示されたら自動終了
- **PDF生成**: 取得した全ページを1つのPDFファイルに結合
- **高品質保存**: 最高品質（quality=95）でPDFを保存
- **設定管理**: 環境変数で全ての動作をカスタマイズ可能
- **ロギング機能**: 処理の進捗やエラーを詳細に記録

## システム要件

- Python 3.8以上
- Windows 10/11
- Kindleアプリ（Windows版）
- uv（パッケージマネージャー）

## クイックスタート

### 1. インストール

```bash
# リポジトリをクローン
git clone https://github.com/ykato27/kindle-to-pdf-capture.git
cd kindle-to-pdf-capture

# uvで依存関係をインストール
uv sync
```

### 2. 実行

```bash
# 方法1: 仮想環境で実行
uv run python main.py

# 方法2: インストール後のコマンド
uv run kindle-to-pdf

# 方法3: 直接実行
python main.py
```

### 3. 使用手順

1. Kindleアプリで読みたい本を開く
2. 本の最初のページを表示
3. スクリプトを実行
4. プロンプトで以下を入力：
   - **出力先フォルダ**: PDF出力フォルダのパス（デフォルト: カレントディレクトリ）
   - **本のタイトル**: PDFのファイル名として使用
5. 自動でページをキャプチャして処理が開始
6. 完了メッセージが表示されたら、PDF生成完了

### 処理の中断

Ctrl+C を押すことで処理を中断できます。

## 設定

### 環境変数でカスタマイズ

`.env`ファイルを作成して、以下の環境変数で動作をカスタマイズできます：

```bash
# .env.exampleをコピーして .env を作成
cp .env.example .env
```

| 変数名 | 説明 | デフォルト |
|--------|------|----------|
| `KINDLE_PAGE_TURN_WAIT` | ページめくり後の待機時間（秒） | 1.0 |
| `KINDLE_WINDOW_WAIT` | ウィンドウ有効化後の待機時間（秒） | 0.5 |
| `KINDLE_MAX_SAME_PAGE` | 同一ページ判定の連続判定回数 | 3 |
| `KINDLE_SIMILARITY_THRESHOLD` | 画像類似度の閾値（0-1） | 0.95 |
| `KINDLE_MAX_PAGES` | 最大ページ数（無限ループ防止） | 10000 |
| `KINDLE_PDF_QUALITY` | PDF品質（0-95） | 95 |
| `KINDLE_CLEANUP_TEMP` | 一時ファイル自動削除 | true |
| `KINDLE_WINDOW_KEYWORD` | Kindleウィンドウ検出キーワード | kindle |
| `KINDLE_OUTPUT_DIR` | PDF出力ディレクトリ | カレント |

詳細は [.env.example](.env.example) を参照してください。

## 処理フロー

```
1. Kindleアプリのウィンドウを検索
2. ウィンドウを前面に表示
3. 初回スクリーンショット取得
4. 以下をループ
   - 右矢印キーを送信してページめくり
   - 設定時間待機
   - スクリーンショット取得
   - 前回の画像とハッシュ値を比較
   - 同一画像が連続で検出されたらカウント
   - 設定回数に達したら終了、異なれば継続
5. 取得した全画像を1つのPDFに結合
6. 一時ファイルをクリーンアップ
7. 完了メッセージ表示
```

## ディレクトリ構成

```
kindle-to-pdf-capture/
├── kindle_to_pdf/          # メインパッケージ
│   ├── __init__.py
│   ├── cli.py              # CLIインターフェース
│   ├── converter.py        # コンバータロジック
│   ├── config.py           # 設定管理
│   ├── logger.py           # ロギング
│   └── utils.py            # ユーティリティ
├── tests/                  # テストスイート
├── main.py                 # エントリーポイント
├── pyproject.toml          # プロジェクト設定
├── README.md               # 本ドキュメント
├── CONTRIBUTING.md         # 開発者ガイド
└── .env.example            # 環境変数テンプレート
```

## トラブルシューティング

### Kindleアプリが見つからない

**症状**: 「Kindleアプリが見つかりません」というエラーが表示される

**解決方法**:
- Kindleアプリが起動していることを確認してください
- Kindleアプリのウィンドウタイトルに「Kindle」が含まれていることを確認
- 必要に応じて`KINDLE_WINDOW_KEYWORD`環境変数を調整してください

### ページがうまくめくれない

**症状**: ページが自動でめくれない、または途中で止まる

**解決方法**:
- Kindleアプリがアクティブ（最前面）になっていることを確認
- キーボード入力が正しく機能していることを確認
- `KINDLE_PAGE_TURN_WAIT`を大きめに設定してページ表示を待つ
- 別のアプリがキーボード入力をインターセプトしていないか確認

### PDFが作成されない

**症状**: スクリーンショットは取得しているがPDFが作成されない

**解決方法**:
- 出力ディレクトリが書き込み可能なことを確認
- ディスク容量が十分にあることを確認
- ファイル名に無効な文字がないか確認
- ログ出力を確認して詳細なエラーメッセージを見る

### 画像の比較がうまくいかない

**症状**: 最終ページが正しく判定されない

**解決方法**:
- `KINDLE_MAX_SAME_PAGE`を増やす（3から5に変更など）
- `KINDLE_SIMILARITY_THRESHOLD`を調整する（0.95から0.90に変更など）
- `KINDLE_PAGE_TURN_WAIT`を増やしてページの完全な読み込みを待つ

## 技術仕様

### 使用ライブラリ

| ライブラリ | 用途 |
|-----------|------|
| **pyautogui** | ウィンドウ検出、キーボード操作、スクリーンショット取得 |
| **pygetwindow** | Windowsウィンドウ操作 |
| **Pillow** | 画像処理、PDF変換 |
| **imagehash** | 画像ハッシュ値計算（同一ページ検出） |

### パフォーマンスチューニング

- **メモリ使用量**: スクリーンショットはメモリに保持。PDFファイルサイズが大きい場合はディスク容量に注意
- **処理速度**: ページめくり待機時間を調整することで速度を制御

## 開発者向け情報

開発に参加する場合は [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

以下の機能が提供されています：

- **テストスイート**: `pytest`で包括的なテストを実行
- **コード品質ツール**: Black、Ruff、MyPyで品質を保証
- **ロギング機能**: デバッグ情報の詳細な出力

```bash
# 開発環境をセットアップ
uv sync --all-extras

# テストを実行
uv run pytest

# コードをフォーマット
uv run black kindle_to_pdf tests

# 品質チェック
uv run ruff check --fix kindle_to_pdf tests
```

## ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照してください

## 貢献

バグ報告や機能リクエストは、[GitHub Issues](https://github.com/ykato27/kindle-to-pdf-capture/issues) で受け付けています。

PRも歓迎します！詳細は [CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。