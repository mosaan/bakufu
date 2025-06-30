# MCP（Model Context Protocol）統合

bakufuのModel Context Protocol統合機能について説明します。MCPを使用することで、作成したワークフローをClaude DesktopやCursorなどのMCP対応アプリケーション内でツールとして実行できます。

## MCPとは？

Model Context Protocol（MCP）は、AIアプリケーションが外部データソースやツールと安全に接続できるオープンスタンダードです。bakufuのMCP統合により、ワークフローはあらゆるMCP対応クライアントから呼び出し可能な再利用可能ツールになります。

## 主要機能

- **動的ワークフロー登録**: 指定ディレクトリ内のワークフローファイル（.yml/.yaml）を自動検出・登録
- **MCP Sampling Mode**: GitHub CopilotのLLMをMCP Sampling API経由で利用（APIキー不要）
- **デュアルモード運用**: 従来のLLMプロバイダーとMCP Samplingの切り替え対応
- **統合入力処理**: `@file:`と`@value:`プレフィックスによる柔軟な入力処理
- **自動パラメータ検証**: ワークフロー定義に基づく入力パラメータの型チェックと必須項目検証
- **実行時統計**: AI使用量（API呼び出し回数、トークン数、コスト）とパフォーマンス情報
- **包括的エラーハンドリング**: 詳細なエラーメッセージと実行ログ

## セットアップ

### 1. MCPサーバーの起動

#### GitHub Copilot Sampling Mode（推奨）
APIキー不要でGitHub CopilotのLLMを使用：

```bash
# GitHub Copilot Sampling Mode
bakufu-mcp --workflow-dir examples/ja/basic --config bakufu.yml --sampling-mode --verbose

# 最小構成
bakufu-mcp --workflow-dir examples/ja/basic --sampling-mode
```

#### 従来のLLMプロバイダーモード
Gemini、OpenAIなどのAPIキーを使用：

```bash
# 基本的な使用方法
bakufu-mcp --workflow-dir examples/en/basic

# 設定ファイル指定
bakufu-mcp --workflow-dir /path/to/workflows --config /path/to/bakufu.yml

# 詳細ログ出力
bakufu-mcp --workflow-dir examples/en/basic --verbose
```

### 2. MCP Client設定

#### VS Code（GitHub Copilot統合）
`.vscode/mcp.json`設定例：

```json
{
  "servers": {
    "bakufu-mcp-sampling": {
      "command": "uv",
      "args": [
        "run",
        "bakufu-mcp",
        "--workflow-dir",
        "examples/ja/basic",
        "--config",
        "bakufu.yml",
        "--sampling-mode",
        "--verbose"
      ],
      "cwd": "/path/to/bakufu"
    }
  }
}
```

#### Claude Desktop設定

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**Sampling Mode（推奨）:**
```json
{
  "mcpServers": {
    "bakufu-sampling": {
      "command": "bakufu-mcp",
      "args": [
        "--workflow-dir", "/path/to/your/workflows",
        "--config", "/path/to/bakufu.yml",
        "--sampling-mode"
      ]
    }
  }
}
```

**従来モード（APIキー使用）:**
```json
{
  "mcpServers": {
    "bakufu": {
      "command": "bakufu-mcp",
      "args": [
        "--workflow-dir", "/path/to/your/workflows",
        "--config", "/path/to/bakufu.yml"
      ],
      "env": {
        "GOOGLE_API_KEY": "your_google_api_key",
        "OPENAI_API_KEY": "your_openai_api_key"
      }
    }
  }
}
```

### 3. APIキー設定（従来モードのみ）

Sampling Modeを使用する場合は不要です。従来モードでLLMプロバイダーを使用する場合のみ設定してください。

Create a `bakufu.yml` config file:

```yaml
default_provider: "gemini/gemini-2.0-flash"
provider_settings:
  gemini:
    api_key: "${GOOGLE_API_KEY}"  # Set this environment variable
```

または環境変数を設定：
```bash
export GOOGLE_API_KEY="your_api_key_here"
```

### 4. MCP Clientの再起動

設定保存後、MCPクライアント（Claude Desktop、VS Codeなど）を再起動してください。bakufuワークフローがツールとして利用可能になります。

## 利用可能なツール

MCPサーバー起動時に以下のツールが自動登録されます：

### `list_available_workflows`
ディレクトリ内のすべてのワークフローを一覧表示します。各ワークフローの以下の情報を含みます：
- ワークフロー名と説明
- 入力パラメータの詳細（名前、型、必須/オプション、デフォルト値）

### 動的ワークフローツール
各ワークフローは`execute_<ワークフロー名>`として登録されます：

#### ツール名の生成規則
- ワークフロー名を小文字に変換
- スペースとハイフンをアンダースコアに置換
- 英数字とアンダースコア以外の文字を除去
- 先頭に`execute_`を付加

例：`Hello World - First Workflow` → `execute_hello_world__first_workflow`

#### 引数の仕様
各ツールは、単一の`input`引数（JSON形式）を受け取ります：

- **引数名**: `input`（固定）
- **型**: JSONオブジェクト（辞書形式）
- **内容**: ワークフロー定義の`input_parameters`で定義されたパラメータを含むオブジェクト

例えば、以下のワークフロー定義：
```yaml
name: "Text Summarizer"
input_parameters:
  - name: text
    type: string
    required: true
    description: "要約対象のテキスト"
  - name: max_length
    type: integer
    required: false
    default: 200
    description: "要約の最大文字数"
```

は、`execute_text_summarizer`ツールとして登録され、以下の形式で呼び出します：
```json
{
  "text": "要約したいテキストの内容",
  "max_length": 150
}
```

## 統合入力形式

MCP統合では、パラメータ値に特別なプレフィックスを使って高度な入力処理が可能です：

### `@file:` プレフィックス
ファイルからコンテンツを読み込み、指定した形式で解析します。

#### 書式
```
@file:ファイルパス:形式:エンコーディング
```

- **ファイルパス**: 読み込むファイルのパス（必須）
- **形式**: `text`（デフォルト）、`json`、`yaml`、`csv`（オプション）
- **エンコーディング**: `utf-8`（デフォルト）、`shift_jis`など（オプション）

#### 例
```
@file:/path/to/file.txt                    # プレーンテキスト（UTF-8）
@file:/path/to/data.json:json              # JSON形式で解析
@file:/path/to/data.yaml:yaml              # YAML形式で解析
@file:/path/to/data.csv:csv                # CSV形式で解析
@file:/path/to/file.txt:text:shift_jis     # Shift_JISテキスト
```

### `@value:` プレフィックス
JSON文字列を解析してオブジェクトに変換します。

#### 書式
```
@value:JSON文字列
```

#### 例
```
@value:{"key": "value", "number": 42}      # オブジェクト
@value:["item1", "item2", "item3"]         # 配列
@value:"simple string"                     # 文字列
@value:42                                  # 数値
@value:true                                # 真偽値
```

### 使用例

MCPクライアント（Claude Desktop、MCP Inspectorなど）では、ツールの`input`引数にJSONオブジェクトを渡します：

**1. 通常の値（推奨）:**
```json
{
  "text": "これは要約したい長いテキストです...",
  "max_length": 200
}
```

**2. オプション引数省略（デフォルト値適用）:**
```json
{
  "text": "これは要約したい長いテキストです..."
}
```
※ `max_length`は自動的にデフォルト値（200）が適用されます

**3. @value:プレフィックス（JSON値の解析）:**
```json
{
  "text": "@value:\"これは要約したい長いテキストです...\"",
  "max_length": "@value:150"
}
```

**4. @file:プレフィックス（ファイルから読み込み）:**
```json
{
  "text": "@file:/path/to/input.txt",
  "max_length": "@value:200"
}
```

**5. 複合例（ファイル読み込み + JSON解析）:**
```json
{
  "theme": "@file:/path/to/theme.json:json",
  "target_audience": "@value:\"データサイエンティスト\"",
  "word_count": "@value:1500"
}
```

## GitHub Copilot統合での使用例

Sampling Modeを使用してGitHub Copilot Chat内でbakufuワークフローを実行：

### 基本的な使用方法

**MCP Test Workflow:**
```
@bakufu-mcp-sampling execute_mcp_test {"message": "GitHub Copilotからこんにちは！"}
```

**Code Review Workflow:**
```
@bakufu-mcp-sampling execute_code_review {
  "code": "def calculate_total(items):\n    total = 0\n    for item in items:\n        total += item.price\n    return total",
  "language": "python"
}
```

**利用可能なワークフロー一覧:**
```
@bakufu-mcp-sampling list_available_workflows
```

### Sampling Mode vs 従来モード比較

| 項目 | Sampling Mode | 従来モード |
|------|---------------|------------|
| LLMプロバイダー | GitHub Copilot | Gemini/OpenAI/etc. |
| APIキー | 不要 | 必要 |
| コスト | Copilotサブスクリプションに含まれる | 使用量課金 |
| パフォーマンス | 良好 | 高い |
| セットアップ複雑度 | 簡単 | 中程度 |
| オフライン対応 | 不可 | 不可 |

## 実行結果とメタデータ

ワークフロー実行時には以下の情報が提供されます：

### 成功時の情報
- **実行結果**: ワークフローの最終出力
- **実行時間**: 秒単位の実行時間
- **AI使用統計**:
  - API呼び出し回数
  - 総トークン数（プロンプト＋完了）
  - 推定コスト（USD）

### エラー時の情報
- **エラーメッセージ**: 具体的なエラー内容
- **実行時間**: エラー発生までの時間
- **コンテキスト情報**: ステップID、ワークフロー名など

## トラブルシューティング

### よくある問題

1. **MCPサーバーが起動しない**
   ```bash
   # 依存関係の確認
   uv sync --all-extra
   
   # ディレクトリの確認
   ls /path/to/workflows/*.yml
   
   # 設定ファイルの確認
   cat bakufu.yml
   ```

2. **ワークフローが検出されない**
   - ワークフローファイルの拡張子が`.yml`または`.yaml`であることを確認
   - ファイルのYAML構文が正しいことを確認
   - `--verbose`フラグでログを確認

3. **ツールがClaude Desktopに表示されない**
   - Claude Desktop設定ファイルのJSON構文を確認
   - 設定ファイルのパスが正しいことを確認
   - Claude Desktopの完全な再起動

4. **ワークフロー実行エラー**
   - **Sampling Mode**: GitHub Copilotが有効でログイン済みかを確認
   - **従来モード**: API キーの環境変数設定を確認
   - 入力パラメータの型と必須項目を確認
   - ワークフロー定義のステップ構文を確認

5. **Sampling Mode特有の問題**
   - GitHub Copilotのライセンスが有効か確認
   - VS CodeでGitHub Copilot拡張機能が有効か確認
   - `--sampling-mode`フラグがMCP設定に含まれているか確認
   - MCPクライアントの再起動を試行

### デバッグログの活用

詳細なログで問題を特定：

```bash
# Sampling Mode
bakufu-mcp --workflow-dir examples/ja/basic --sampling-mode --verbose

# 従来モード
bakufu-mcp --workflow-dir examples/en/basic --verbose
```

ログには以下の情報が含まれます：
- ワークフローファイルの検出と読み込み状況
- 動的ツールの登録状況
- 入力パラメータの検証結果
- ステップ実行の進行状況
- AI プロバイダーとの通信状況

### 設定確認コマンド

```bash
# ワークフローの手動検証
bakufu validate /path/to/workflow.yml

# 設定ファイルの確認
bakufu config list --path /path/to/bakufu.yml

# 個別ワークフローのテスト実行
bakufu run /path/to/workflow.yml --input '{"param": "value"}' --dry-run
```

## アーキテクチャ

bakufuのMCP統合は以下のコンポーネントで構成されています：

- **MCP Server** (`mcp_server.py`): FastMCPベースのサーバー実装
- **MCP Integrator** (`mcp_integration.py`): ワークフローエンジンとMCPの橋渡し
- **Unified Input Processor** (`unified_input.py`): プレフィックス付き入力の処理
- **Workflow Execution Engine**: 既存のbakufuワークフロー実行エンジン

このアーキテクチャにより、既存のワークフロー定義をそのままMCPツールとして公開できます。

---

📖 [統合機能目次に戻る](README.md)