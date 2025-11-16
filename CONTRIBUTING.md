# Contributing Guide

このプロジェクトへの貢献ありがとうございます。本ドキュメントに従って、開発に参加してください。

## 開発環境の設定

### 前提条件

- Python 3.8以上
- uv（パッケージマネージャー）
- Git

### セットアップ手順

1. リポジトリをクローン：
```bash
git clone https://github.com/ykato27/kindle-to-pdf-capture.git
cd kindle-to-pdf-capture
```

2. uvで依存関係をインストール：
```bash
uv sync --all-extras
```

3. 環境変数を設定（オプション）：
```bash
cp .env.example .env
# .envファイルを編集して必要な設定をカスタマイズ
```

## ディレクトリ構成

```
kindle-to-pdf-capture/
├── kindle_to_pdf/          # メインパッケージ
│   ├── __init__.py        # パッケージ初期化
│   ├── cli.py             # CLIインターフェース
│   ├── converter.py       # メイン変換ロジック
│   ├── config.py          # 設定管理
│   ├── logger.py          # ロギング設定
│   └── utils.py           # ユーティリティ関数
├── tests/                 # テスト
│   ├── __init__.py
│   ├── test_converter.py
│   ├── test_config.py
│   └── test_utils.py
├── main.py               # エントリーポイント
├── pyproject.toml        # プロジェクト設定
├── README.md             # 使用方法
├── CONTRIBUTING.md       # 貢献ガイド（本ファイル）
├── .env.example          # 環境変数テンプレート
└── LICENSE               # ライセンス
```

## コーディング規約

### スタイルガイド

本プロジェクトでは以下のツールを使用して、コード品質を保っています：

- **Black**: コードフォーマッター
- **Ruff**: ラインター
- **MyPy**: 型チェッカー

### フォーマット

コード提出前に、以下のコマンドを実行してください：

```bash
# Blackでフォーマット
uv run black kindle_to_pdf tests

# Ruffで品質チェック
uv run ruff check --fix kindle_to_pdf tests

# MyPyで型チェック
uv run mypy kindle_to_pdf
```

### コード規約

- **型ヒント**: すべての関数に型ヒントを指定してください
- **ドキュメント**: 各関数にDocstring（Google形式）を記述してください
- **行の長さ**: 最大100文字（Blackのデフォルト）
- **名前付け**:
  - クラス：PascalCase（例：`KindleToPdfConverter`）
  - 関数/変数：snake_case（例：`get_default_config`）
  - 定数：UPPER_SNAKE_CASE

## テスト

### テストの実行

```bash
# すべてのテストを実行
uv run pytest

# カバレッジレポートを表示
uv run pytest --cov=kindle_to_pdf

# 特定のテストのみ実行
uv run pytest tests/test_config.py

# 特定のテスト関数のみ実行
uv run pytest tests/test_config.py::test_get_default_config
```

### テストの書き方

- テストファイル：`tests/test_*.py`
- テスト関数：`test_*` で始まる関数
- テストクラス：`Test*` で始まるクラス

例：
```python
import pytest
from kindle_to_pdf.config import get_default_config

def test_get_default_config():
    """デフォルト設定が正しく作成されることを確認"""
    config = get_default_config()
    assert config.capture.page_turn_wait_time == 1.0
    assert config.capture.max_same_page_count == 3
```

## コミットメッセージ

### フォーマット

```
<type>: <subject>

<body>

Fixes #<issue-number>
```

### タイプの種類

- **feat**: 新機能
- **fix**: バグ修正
- **docs**: ドキュメント変更
- **style**: コード スタイル（フォーマット等）
- **refactor**: リファクタリング
- **perf**: パフォーマンス改善
- **test**: テスト追加・修正
- **ci**: CI/CD設定変更
- **chore**: パッケージ管理、その他の変更

### 例

```
feat: 画像品質設定を環境変数から読み込み可能に

ユーザーが KINDLE_PDF_QUALITY 環境変数で
PDF出力時の品質を カスタマイズできるようにしました。

Fixes #10
```

## プルリクエスト

### PR作成前のチェックリスト

- [ ] 機能のテストを追加した
- [ ] すべてのテストがパスしている
- [ ] `black`、`ruff`、`mypy`を実行した
- [ ] ドキュメント（README等）を更新した
- [ ] コミットメッセージが規約に従っている

### PR作成時

1. フィーチャーブランチを作成：
```bash
git checkout -b feature/<feature-name>
# または
git checkout -b fix/<bug-name>
```

2. コミット・プッシュ：
```bash
git add .
git commit -m "feat: <説明>"
git push origin feature/<feature-name>
```

3. GitHubで PR を作成し、以下の情報を記入：
   - 変更内容の説明
   - 関連するissueへのリンク
   - テスト方法

## ログレベルについて

本プロジェクトではloggingモジュールを使用しています：

- **DEBUG**: 開発時の詳細情報
- **INFO**: 処理の進捗状況（通常表示）
- **WARNING**: 警告情報
- **ERROR**: エラー情報
- **CRITICAL**: 重大エラー

デフォルトはINFOレベルです。

## 環境変数のカスタマイズ

`.env`ファイルを編集して、以下の設定をカスタマイズできます：

| 変数 | 説明 | デフォルト |
|------|------|----------|
| `KINDLE_PAGE_TURN_WAIT` | ページめくり待機時間 | 1.0秒 |
| `KINDLE_WINDOW_WAIT` | ウィンドウ有効化待機時間 | 0.5秒 |
| `KINDLE_MAX_SAME_PAGE` | 同一ページ判定回数 | 3回 |
| `KINDLE_PDF_QUALITY` | PDF品質 | 95 |
| `KINDLE_CLEANUP_TEMP` | 一時ファイル削除 | true |

詳細は `.env.example` を参照してください。

## よくある質問

### Q: 型チェックでエラーが出る場合は？

```bash
# 型チェックを実行
uv run mypy kindle_to_pdf

# 型ヒントを修正してください
# 詳細は MyPy のドキュメントを参照
```

### Q: テストが失敗する場合は？

```bash
# 詳細なエラーメッセージを表示
uv run pytest -v

# 特定のテストをデバッグ
uv run pytest -v tests/test_*.py -s
```

### Q: ドキュメントを追加したい場合は？

- `README.md`: 一般的な使用方法
- `CONTRIBUTING.md`: 開発者向け情報
- コード内コメント: 複雑なロジックの説明

## ライセンス

このプロジェクトはMITライセンスです。
貢献することで、あなたの変更がMITライセンスの下で公開されることに同意します。

## サポート

問題が発生した場合は、以下の方法で報告してください：

1. **バグ報告**: GitHubのIssueで報告
2. **機能リクエスト**: GitHubのDiscussionsで提案
3. **セキュリティ問題**: プライベートに報告（メールで連絡）

ご協力ありがとうございます！
