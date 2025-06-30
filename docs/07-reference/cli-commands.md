# CLIコマンドリファレンス

bakufuで利用可能なすべてのコマンドとオプションの詳細リファレンスです。

## 基本構文

```bash
bakufu [グローバルオプション] <コマンド> [コマンドオプション] [引数]
```

## グローバルオプション

| オプション | 説明 |
|-----------|------|
| `--version` | バージョン情報を表示 |
| `--help` | ヘルプを表示 |
| `--config <path>` | 設定ファイルのパスを指定 |

## コマンド一覧

### `run` - ワークフロー実行

```bash
bakufu run <workflow.yml> [オプション]
```

ワークフローファイルを実行します。

#### オプション

| オプション | 説明 | 例 |
|-----------|------|-----|
| `--provider <provider>` | AIプロバイダーを指定 | `--provider gpt-4` |
| `--input <JSON>` | 入力データをJSON形式で指定 | `--input '{"name": "太郎"}'` |
| `--input-file <file>` | ファイルから入力データ全体を読み込み | `--input-file input.json` |
| `--input-file-for <key>=<path>` | ファイルから入力データの一部を読み込み | `--input-file-for content=data.txt` |
| `--output <file>` | 出力ファイルのパスを指定 | `--output result.txt` |
| `--output-format <format>` | 出力形式を指定 (text/json/yaml) | `--output-format json` |
| `--verbose` | 詳細出力を有効化 | |
| `--dry-run` | バリデーションのみ実行（AI呼び出しなし） | |

### `validate` - ワークフロー検証

```bash
bakufu validate <workflow.yml> [オプション]
```

ワークフローファイルの構文をチェックします。

#### オプション

| オプション | 説明 |
|-----------|------|
| `--verbose` | 詳細な検証結果を表示 |
| `--schema-only` | スキーマ検証のみ実行 |
| `--template-check` | テンプレート構文チェックを実行 |

### `config` - 設定管理

```bash
bakufu config <サブコマンド>
```

#### サブコマンド

| サブコマンド | 説明 | オプション |
|-------------|------|-----------|
| `init` | 基本設定ファイルを作成 | `--path <path>`: 設定ファイルの作成先<br>`--global`: グローバル設定として作成 |
| `list` | 現在の設定を表示 | `--path <path>`: 設定ファイルのパス |

## MCP Server Commands

### `bakufu-mcp` - MCP Server起動

```bash
bakufu-mcp [オプション]
```

Model Context Protocol（MCP）サーバーとしてbakufuワークフローを起動します。

#### オプション

| オプション | 説明 | 例 |
|-----------|------|-----|
| `--workflow-dir <path>` | ワークフローディレクトリのパス | `--workflow-dir examples/ja/basic` |
| `--config <path>` | 設定ファイルのパス | `--config bakufu.yml` |
| `--sampling-mode` | MCP Sampling Mode（GitHub Copilot使用） | |
| `--verbose` | 詳細ログ出力を有効化 | |

## 使用例

### 基本的なワークフロー実行

```bash
# JSONで直接入力を指定
bakufu run workflow.yml --input '{"message": "Hello"}'

# ファイルから入力データを読み込み
bakufu run workflow.yml --input-file input.json

# 出力形式を指定
bakufu run workflow.yml --input '{}' --output yaml
```

### ワークフロー検証

```bash
# 構文チェック
bakufu validate workflow.yml
```

### 設定管理

```bash
# 基本設定ファイルを作成
bakufu config init

# グローバル設定として作成
bakufu config init --global

# 指定パスに設定ファイルを作成
bakufu config init --path ./config/bakufu.yml

# 現在の設定を表示
bakufu config list
```

### MCP Server起動

```bash
# GitHub Copilot Sampling Mode（推奨）
bakufu-mcp --workflow-dir examples/ja/basic --config bakufu.yml --sampling-mode --verbose

# 従来モード（APIキー使用）
bakufu-mcp --workflow-dir examples/en/basic --config bakufu.yml --verbose

# 最小構成（Sampling Mode）
bakufu-mcp --workflow-dir examples/ja/basic --sampling-mode
```

---

📖 [リファレンス目次に戻る](README.md)