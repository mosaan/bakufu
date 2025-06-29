# 基本設定

bakufuのAIプロバイダー設定と基本的な設定ファイルの作成方法について説明します。

## 設定ファイルの作成

bakufuを使用するには設定ファイル（`bakufu.yml`）が必要です。以下のコマンドで基本設定ファイルを作成できます：

```bash
bakufu config init
```

これにより、デフォルトでGemini 2.0 Flashを使用する設定ファイルが生成されます。

## AIプロバイダー設定

bakufuはLiteLLMを基盤として使用しているため、LiteLLMがサポートする多数のAIプロバイダーを利用できます。詳細な対応プロバイダー一覧については、[LiteLLMのドキュメント](https://docs.litellm.ai/docs/providers)を参照してください。

## 設定方法

### 1. 設定ファイルでの直接指定

設定ファイル内でAPIキーを直接指定：

```yaml
ai_providers:
  primary:
    provider: "gemini/gemini-2.0-flash"
    api_key: "your-actual-api-key"
    temperature: 0.7
    timeout: 30.0
    max_retries: 3
```

### 2. 環境変数の参照（オプション）

環境変数を使用してAPIキーを設定することも可能です。設定ファイルで環境変数を参照する方法：

```yaml
ai_providers:
  primary:
    provider: "gemini/gemini-2.0-flash"
    api_key: "${GOOGLE_API_KEY}"
    temperature: 0.7
    timeout: 30.0
    max_retries: 3
```

### 環境変数の設定

Google GeminiのAPIキーを環境変数で設定：

**Linux/macOS**:
```bash
export GOOGLE_API_KEY="your-google-api-key"
```

**Windows**:
```cmd
set GOOGLE_API_KEY=your-google-api-key
```
## 基本的な設定パラメータ

| パラメータ | 説明 | デフォルト値 |
|-----------|------|-------------|
| `provider` | 使用するAIモデル | `gemini/gemini-2.0-flash` |
| `api_key` | APIキー | 環境変数参照 |
| `temperature` | 出力のランダム性（0.0-2.0） | `0.7` |
| `timeout` | タイムアウト時間（秒） | `30.0` |
| `max_retries` | 最大リトライ回数 | `3` |

## 次のステップ

基本設定が完了したら、[最初のワークフロー](first-workflow.md)を作成してbakufuを実際に使ってみましょう。

---

📖 [はじめに目次に戻る](README.md)