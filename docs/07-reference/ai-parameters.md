# AI Parameters Reference

BakufuはLiteLLMを使用してAI呼び出しを抽象化しており、LiteLLMが提供するすべてのパラメータを`ai_params`フィールドで透過的に利用できます。

## 基本概念

### パラメータの設定方法

AIパラメータは以下の3つの方法で設定できます：

1. **プロバイダー設定** (`config.yml`) - 全体のデフォルト値
2. **ai_paramsフィールド** - ステップレベルの設定
3. **明示的パラメータ** - よく使用される重要パラメータ

### パラメータの優先順位

設定の優先順位は以下の通りです（後から設定されたものが優先）：

1. プロバイダー設定（`config.yml`）
2. `ai_params`フィールド
3. 明示的パラメータ（`temperature`, `max_tokens`等）

```yaml
# 例：パラメータの優先順位
- id: "example_step"
  type: "ai_call"
  prompt: "分析してください"
  temperature: 0.7          # 最優先（明示的パラメータ）
  ai_params:
    temperature: 0.5        # 上書きされる
    top_p: 0.9             # 有効（明示的パラメータなし）
```

## 明示的パラメータ vs ai_params

### 明示的パラメータ（推奨）

以下のパラメータは明示的に定義されており、型チェックとバリデーションが提供されます：

#### `temperature` (float, 0.0-2.0)
創造性とランダム性を制御します。

```yaml
- id: "creative_writing"
  type: "ai_call"
  prompt: "創作小説を書いて"
  temperature: 1.2          # 創造的な出力

- id: "data_analysis"
  type: "ai_call"
  prompt: "データを分析して"
  temperature: 0.1          # 決定論的な出力
```

#### `max_tokens` (integer, > 0)
生成される最大トークン数を制御します。

```yaml
- id: "summary"
  type: "ai_call"
  prompt: "要約してください"
  max_tokens: 200           # 短い要約

- id: "detailed_analysis"
  type: "ai_call"
  prompt: "詳細分析してください"
  max_tokens: 2000          # 長い分析
```

#### `max_auto_retry_attempts` (integer, >= 0)
Bakufu固有のAuto-Continuation機能の再試行回数です。

```yaml
- id: "long_content"
  type: "ai_call"
  prompt: "長い文書を生成"
  max_auto_retry_attempts: 3  # 最大3回まで継続
```

### ai_paramsフィールド

その他のLiteLLMパラメータは`ai_params`で設定します：

```yaml
- id: "advanced_step"
  type: "ai_call"
  prompt: "分析してください"
  ai_params:
    # サンプリング制御
    top_p: 0.9
    presence_penalty: 0.6
    frequency_penalty: 0.3
    
    # 出力制御
    stop: ["END", "---"]
    logit_bias: {"token_id": -100}
    seed: 42
```

## 主要なai_paramsパラメータ

### サンプリング制御

#### `top_p` (float, 0.0-1.0)
累積確率による語彙制限。temperatureと組み合わせて使用。

```yaml
ai_params:
  top_p: 0.9              # 上位90%の語彙のみ使用
  temperature: 0.8        # 適度なランダム性
```

#### `presence_penalty` / `frequency_penalty` (float, -2.0-2.0)
繰り返しを制御するペナルティ。

```yaml
ai_params:
  presence_penalty: 0.6   # 新しいトピックを促進
  frequency_penalty: 0.3  # 繰り返し語句を削減
```

### 構造化出力

#### `response_format`
JSON形式での出力を強制します（OpenAI互換モデル）。

```yaml
# 単純なJSON出力
ai_params:
  response_format:
    type: "json_object"

# JSON Schemaでの構造化出力
ai_params:
  response_format:
    type: "json_schema"
    json_schema:
      name: "analysis_result"
      schema:
        type: "object"
        properties:
          sentiment: 
            type: "string"
            enum: ["positive", "negative", "neutral"]
          confidence:
            type: "number"
            minimum: 0.0
            maximum: 1.0
        required: ["sentiment", "confidence"]
```

### Function Calling

#### `tools` / `tool_choice`
関数呼び出し機能を設定します。

```yaml
ai_params:
  tools:
    - type: "function"
      function:
        name: "get_weather"
        description: "指定された都市の天気を取得"
        parameters:
          type: "object"
          properties:
            city:
              type: "string"
              description: "都市名"
            country:
              type: "string"
              description: "国名"
          required: ["city"]
  tool_choice: "auto"       # 自動選択
```

### 出力制御

#### `stop`
生成を停止する文字列を指定します。

```yaml
ai_params:
  stop: ["END", "---", "\n\n---"]
```

#### `logit_bias`
特定のトークンの出力確率を調整します。

```yaml
ai_params:
  logit_bias:
    "50256": -100          # 特定のトークンを禁止
    "1234": 10             # 特定のトークンを促進
```

#### `seed`
再現可能な出力のためのシード値。

```yaml
ai_params:
  seed: 42                 # 決定論的な出力
```

## プロバイダー別対応状況

### OpenAI / OpenAI互換
- **完全対応**: すべてのパラメータが利用可能
- **特徴**: response_format, tools, function calling等

### Anthropic (Claude)
- **基本対応**: temperature, max_tokens, stop等
- **独自パラメータ**: top_k（ai_paramsで指定可能）
- **非対応**: response_format（JSON出力は別の方法で制御）

### Google (Gemini)
- **基本対応**: temperature, max_tokens等
- **独自パラメータ**: safety_settings, generation_config等
- **Function Calling**: tools対応

### その他プロバイダー
LiteLLMがサポートするすべてのプロバイダーで、そのプロバイダーが対応するパラメータを利用可能です。

## 実用例

### センチメント分析（構造化出力）

```yaml
- id: "sentiment_analysis"
  type: "ai_call"
  prompt: |
    以下のテキストのセンチメントを分析してください：
    {{ input.text }}
  ai_params:
    response_format:
      type: "json_schema"
      json_schema:
        name: "sentiment_result"
        schema:
          type: "object"
          properties:
            sentiment:
              type: "string"
              enum: ["positive", "negative", "neutral"]
            confidence:
              type: "number"
              minimum: 0.0
              maximum: 1.0
            keywords:
              type: "array"
              items:
                type: "string"
          required: ["sentiment", "confidence"]
```

### 創作的なコンテンツ生成

```yaml
- id: "creative_content"
  type: "ai_call"
  prompt: "{{ input.theme }}をテーマにした短編小説を書いて"
  temperature: 1.1
  ai_params:
    top_p: 0.95
    presence_penalty: 0.7
    frequency_penalty: 0.3
    stop: ["THE END", "終わり"]
    max_tokens: 1500
```

### 技術文書の要約（決定論的）

```yaml
- id: "technical_summary"
  type: "ai_call"
  prompt: |
    以下の技術文書を要約してください：
    {{ input.document }}
  temperature: 0.2
  max_tokens: 500
  ai_params:
    top_p: 0.8
    seed: 42                # 再現可能な結果
    stop: ["---", "まとめ："]
```

### Function Calling例

```yaml
- id: "weather_assistant"
  type: "ai_call"
  prompt: "ユーザーの質問に天気APIを使って答えてください：{{ input.question }}"
  ai_params:
    tools:
      - type: "function"
        function:
          name: "get_current_weather"
          description: "指定された都市の現在の天気を取得"
          parameters:
            type: "object"
            properties:
              location:
                type: "string"
                description: "都市名（例：東京、大阪）"
              unit:
                type: "string"
                enum: ["celsius", "fahrenheit"]
                description: "温度の単位"
            required: ["location"]
    tool_choice: "auto"
```

## ベストプラクティス

### 1. パラメータ選択の指針

- **頻繁に使用**: 明示的パラメータ（temperature, max_tokens）
- **高度な制御**: ai_paramsフィールド
- **プロバイダー固有**: ai_paramsフィールド

### 2. 型安全性の活用

```yaml
# ✅ 推奨：明示的パラメータで型チェック
temperature: 0.7
max_tokens: 1000

# ❌ 避ける：ai_paramsで基本パラメータ
ai_params:
  temperature: 0.7        # 型チェックなし
  max_tokens: 1000        # 型チェックなし
```

### 3. パフォーマンス考慮

```yaml
# 決定論的な処理
temperature: 0.1
ai_params:
  top_p: 0.8
  seed: 42

# 創造的な処理  
temperature: 1.0
ai_params:
  top_p: 0.95
  presence_penalty: 0.6
```

### 4. エラーハンドリング

```yaml
# 構造化出力での厳密な制御
ai_params:
  response_format:
    type: "json_schema"
    json_schema:
      # 厳密なスキーマ定義
      
# 出力制限での確実な停止
ai_params:
  stop: ["END", "---"]
  max_tokens: 2000
```

## トラブルシューティング

### よくある問題

1. **JSON出力が無効**
   - `response_format`でJSON Schemaを使用
   - プロバイダーの対応状況を確認

2. **パラメータが無視される**
   - プロバイダーの対応状況を確認
   - パラメータの優先順位を確認

3. **予期しない出力**
   - temperatureとtop_pの組み合わせを調整
   - stopパラメータで明示的に制御

### デバッグ方法

```yaml
# デバッグ用の設定
- id: "debug_step"
  type: "ai_call"
  prompt: "テスト"
  temperature: 0.1        # 決定論的
  ai_params:
    seed: 42              # 再現可能
    max_tokens: 100       # 短い出力でテスト
```

## 関連リンク

- [LiteLLM Input Parameters](https://docs.litellm.ai/docs/completion/input)
- [LiteLLM Provider-specific Params](https://docs.litellm.ai/docs/completion/provider_specific_params)
- [ワークフロー仕様書](workflow-specification.md)
- [設定リファレンス](configuration.md)