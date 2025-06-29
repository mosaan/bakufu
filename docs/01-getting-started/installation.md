# インストール

bakufuを初めて使用する方向けの入門ガイドです。インストールから最初のワークフロー実行まで、ステップバイステップで説明します。

## bakufuとは

bakufu（瀑布）は、AIを活用したワークフロー自動化ツールです。名前は、連続的なAI呼び出しの流れをウォーターフォール開発プロセスになぞらえたものです。YAMLファイルでワークフローを定義し、複数のAIプロバイダーやテキスト処理機能を組み合わせて、以下のような作業を自動化できます：

- **コンテンツ作成**: ブログ記事、メール文面、ドキュメント生成
- **データ分析**: ログ解析、CSV分析、レポート生成  
- **テキスト処理**: 要約、翻訳、フォーマット変換
- **情報抽出**: JSONパース、正規表現マッチング、構造化

## 主な特徴

- 🤖 **複数AIプロバイダー対応**: Gemini、GPT、Claudeを統合
- 📝 **豊富なテキスト処理**: 正規表現、JSON、Markdown対応
- 🎨 **テンプレート機能**: Jinja2による動的ワークフロー
- ⚡ **高性能**: 並列実行とエラーハンドリング
- 🔧 **柔軟な設定**: プロバイダー別の詳細調整

## システム要件

- **Python**: 3.12以上

## インストール

現在、bakufuは開発段階のため、GitHubリポジトリから直接インストールします：

```bash
# 開発版をインストール
uv tool install git+https://github.com/mosaan/bakufu.git
```

### インストールの確認

```bash
# バージョン確認
bakufu --version

# ヘルプ表示
bakufu --help
```

## 設定ファイルの作成

bakufuを使用するには設定ファイルが必要です。以下のコマンドで基本設定ファイルを作成できます：

```bash
# 基本設定ファイルを作成
bakufu config init
```

`bakufu config init`により、デフォルトでGemini 2.0 Flashを使用する設定ファイルが生成されます。生成された設定ファイルでは環境変数`GOOGLE_API_KEY`を参照してGeminiのモデルを呼び出すため、Google GeminiのAPIキーを環境変数で設定する必要があります。

## APIキー設定

`bakufu config init`で生成される設定ファイルは環境変数`GOOGLE_API_KEY`を参照するため、以下のように設定してください：

**Linux/macOSの場合**:
```bash
export GOOGLE_API_KEY="your_gemini_api_key"
```

**Windowsの場合**:
```cmd
set GOOGLE_API_KEY=your_gemini_api_key
```


## 最初のワークフロー実行

### Hello Worldサンプル

```bash
# Hello Worldサンプルを実行
bakufu run examples/ja/basic/hello-world.yml --input '{"name": "太郎"}'
```

### 基本的なコマンド

```bash
# ワークフローの実行
bakufu run <workflow.yml> --input '<JSON>'

# ファイルから入力データ全体を入力
bakufu run <workflow.yml> --input-file input.json

# ワークフローの構文チェック
bakufu validate <workflow.yml>

# ドライランモード（API呼び出しなし）
bakufu run <workflow.yml> --input '{}' --dry-run

# 出力形式を指定
bakufu run <workflow.yml> --input '{}' --output json
bakufu run <workflow.yml> --input '{}' --output yaml

# ヘルプ表示
bakufu --help
bakufu run --help
```

完全なコマンドリファレンスについては、**[CLIコマンドリファレンス](../07-reference/cli-commands.md)**を参照してください。

## 次のステップ

基本的な使い方を理解したら、以下のガイドに進んでください：

- **[基本設定](configuration.md)** - より詳細な設定方法
- **[最初のワークフロー](first-workflow.md)** - 自分だけのワークフローを作成

---

📖 [はじめに目次に戻る](README.md)