# ワークフロー仕様リファレンス

Bakufuワークフローファイルの完全な技術仕様とAPI仕様です。

## ワークフロー定義

### 基本構造

```yaml
name: string                    # ワークフロー名（必須）
description: string            # 説明（オプション）
version: string               # バージョン（デフォルト: "1.0"）

input_parameters:             # 入力パラメータ定義（オプション）
  - name: string              # パラメータ名
    type: string              # データ型
    required: boolean         # 必須フラグ
    description: string       # 説明
    default: any             # デフォルト値

steps:                       # ワークフローステップ（必須、最低1つ）
  - id: string               # ステップID（一意）
    type: "ai_call" | "ai_map_call" | "text_process" | "collection" | "conditional"  # ステップタイプ
    description: string      # 説明（オプション）
    on_error: "stop" | "continue" | "skip_remaining"  # エラー時の動作

output:                      # 出力形式（オプション）
  format: "text" | "json" | "yaml"
  template: string          # 出力テンプレート
```

### 入力パラメータ型

| 型        | 説明         | 例                 |
| --------- | ------------ | ------------------ |
| `string`  | 文字列       | `"Hello World"`    |
| `integer` | 整数         | `42`               |
| `float`   | 浮動小数点数 | `3.14`             |
| `boolean` | 真偽値       | `true`, `false`    |
| `array`   | 配列         | `["a", "b", "c"]`  |
| `object`  | オブジェクト | `{"key": "value"}` |

## ステップ型

### Conditional ステップ

条件に基づいてワークフローの分岐を制御します。

```yaml
- id: "conditional_step"
  type: "conditional"
  description: "条件分岐処理"
  
  # 基本的な if-else 構造
  condition: string              # Jinja2条件式（必須）
  if_true: [steps]              # 条件がtrueの場合のステップ（オプション）
  if_false: [steps]             # 条件がfalseの場合のステップ（オプション）
  
  # または複数分岐構造
  conditions:                   # 複数条件配列（conditionの代替）
    - condition: string         # Jinja2条件式
      name: string             # 分岐名（オプション）
      default: boolean         # デフォルト分岐フラグ（オプション）
      steps: [steps]           # 実行ステップ
  
  # エラーハンドリング
  on_condition_error: "stop" | "continue" | "skip_remaining"  # 条件評価エラー時の動作
```

**基本的な if-else 例**:
```yaml
- id: "score_check"
  type: "conditional"
  condition: "{{ user_score >= 80 }}"
  if_true:
    - id: "success_message"
      type: "ai_call"
      prompt: "Generate congratulations for high score: {{ user_score }}"
  if_false:
    - id: "improvement_message"
      type: "ai_call"
      prompt: "Generate encouragement for score: {{ user_score }}"
```

**複数分岐例**:
```yaml
- id: "grade_classification"
  type: "conditional"
  conditions:
    - condition: "{{ score >= 95 }}"
      name: "excellent"
      steps:
        - id: "excellence_certificate"
          type: "ai_call"
          prompt: "Create excellence certificate"
    
    - condition: "{{ score >= 80 }}"
      name: "good"
      steps:
        - id: "good_performance"
          type: "ai_call"
          prompt: "Acknowledge good performance"
    
    - condition: ""
      name: "needs_improvement"
      default: true
      steps:
        - id: "improvement_plan"
          type: "ai_call"
          prompt: "Create improvement plan"
```

**結果アクセス**:
```yaml
# ConditionalResultオブジェクトのプロパティ
{{ steps.conditional_step.output }}            # 実行された分岐の出力
{{ steps.conditional_step.condition_result }}  # 条件評価結果（boolean | null）
{{ steps.conditional_step.executed_branch }}   # 実行された分岐名
{{ steps.conditional_step.evaluation_error }}  # 評価エラーメッセージ（string | null）
```

**エラーハンドリング戦略**:
- `stop` (デフォルト): 条件評価エラー時にワークフロー停止
- `continue`: 条件をfalseとして処理し、if_false分岐を実行
- `skip_remaining`: このステップをスキップして次のステップに進む

### AI Call ステップ

AI プロバイダーを呼び出してテキスト生成を行います。

```yaml
- id: "ai_step"
  type: "ai_call"
  description: "AI による処理"
  prompt: string              # プロンプトテンプレート（必須）
  provider: string           # プロバイダー指定（オプション）
  model: string             # モデル指定（オプション）
  temperature: float        # 0.0-2.0（オプション）
  max_tokens: integer       # 最大トークン数（オプション）
  on_error: "stop" | "continue" | "skip_remaining"
```

**サポートプロバイダー**:
LiteLLMのサポートするプロバイダーに準拠します。
詳細は [LiteLLMのドキュメント](https://docs.litellm.ai/docs/providers) を参照してください。
デフォルトプロバイダーは `gemini/gemini-2.0-flash` です。

**例**:
```yaml
- id: "summarize"
  type: "ai_call"
  prompt: |
    以下のテキストを200文字以内で要約してください：
    {{ input.text }}
  temperature: 0.3
  max_tokens: 500
```

#### AI出力検証（v1.2.0）

AI Call および AI Map Call ステップに出力検証機能を追加できます。

```yaml
- id: "validated_ai_step"
  type: "ai_call"
  prompt: string
  validation:                    # 検証設定（オプション）
    # 検証方法（いずれか一つを指定）
    schema: object              # JSON Schema
    pydantic_model: string      # Pydanticモデル名
    custom_validator: string    # カスタム関数名
    
    # 再試行設定
    max_retries: integer        # 最大再試行回数（0-10、デフォルト: 3）
    retry_prompt: string        # カスタム再試行プロンプト
    
    # 出力回復
    allow_partial_success: boolean     # 部分的成功を許可（デフォルト: false）
    extract_json_pattern: string      # JSON抽出正規表現パターン
    
    # 出力強制
    force_json_output: boolean         # JSON出力を強制（デフォルト: false）
    json_wrapper_instruction: string  # JSON指示文
    
    # カスタム検証用パラメータ
    criteria: object            # カスタム検証に渡すパラメータ
```

**検証例**:
```yaml
- id: "sentiment_analysis"
  type: "ai_call"
  prompt: |
    テキストの感情分析を行い、JSON形式で回答してください：
    {{ input.text }}
  validation:
    schema:
      type: object
      required: [sentiment, confidence, summary]
      properties:
        sentiment:
          type: string
          enum: [positive, negative, neutral]
        confidence:
          type: number
          minimum: 0
          maximum: 1
        summary:
          type: string
          minLength: 10
    max_retries: 3
    force_json_output: true
```

### Text Process ステップ

テキスト処理機能を実行します。v0.4.0で大幅に拡張されました。

```yaml
- id: "text_step"
  type: "text_process"
  description: "テキスト処理"
  method: string             # 処理方法（下記参照）
  input: string              # 入力テンプレート（必須）
  
  # method 固有パラメータ（使用する方法により異なる）
  pattern: string           # regex_extract用パターン
  flags: array             # 正規表現フラグ
  output_format: "string" | "array"  # 出力形式
  replacements: array      # replace用置換ルール
  separator: string        # split用区切り文字（v0.4.0新機能）
  max_splits: integer      # split最大分割数（v0.4.0新機能）
  index: integer           # select_item用インデックス（v0.4.0新機能）
  slice: string            # select_item用スライス（v0.4.0新機能）
  condition: string        # フィルタ条件（v0.4.0新機能）
```

#### 利用可能なメソッド（v0.4.0対応）

| メソッド | 説明 | バージョン |
|----------|------|------------|
| `regex_extract` | 正規表現抽出 | 既存 |
| `replace` | 文字列置換 | 既存 |
| `json_parse` | JSON解析 | 既存 |
| `markdown_split` | Markdown分割 | 既存（拡張） |
| `fixed_split` | 固定サイズ分割 | 既存 |
| `array_filter` | 配列フィルタリング | 既存 |
| `array_transform` | 配列変換 | 既存 |
| `array_aggregate` | 配列集約 | 既存 |
| `array_sort` | 配列ソート | 既存 |
| `split` | 文字列分割 | **v1.1.0新機能** |
| `extract_between_marker` | マーカー間テキスト抽出 | **v1.1.0新機能** |
| `select_item` | 配列要素選択 | **v1.1.0新機能** |
| `parse_as_json` | JSON解析・検証 | **v1.1.0新機能** |

### AI Map Call ステップ

配列の各要素に対して並列AI処理を実行します。LLMのコンテキスト長制限を回避し、大量データを効率的に処理できます。

```yaml
- id: "ai_map_step"
  type: "ai_map_call"
  description: "配列要素の並列AI処理"
  input_array: string        # 配列参照テンプレート（必須）
  prompt: string             # プロンプトテンプレート（必須、_itemプレースホルダー含む）
  
  # AI設定（オプション）
  provider: string           # AIプロバイダーのオーバーライド
  model: string             # モデルのオーバーライド  
  temperature: float        # 温度パラメータ（0.0-2.0）
  max_tokens: integer       # 最大トークン数
  
  # 並列実行制御
  concurrency:
    max_parallel: integer   # 同時実行数（1-10、デフォルト: 3）
    batch_size: integer     # バッチサイズ（デフォルト: 10）
    delay_between_batches: float  # バッチ間遅延（秒、デフォルト: 1.0）
  
  # エラー処理
  error_handling:
    on_item_failure: "skip" | "stop" | "retry"  # 個別要素失敗時の動作（デフォルト: skip）
    max_retries_per_item: integer  # 要素ごとの最大リトライ回数（デフォルト: 2）
    preserve_failed_items: boolean  # 失敗要素情報の保持（デフォルト: true）
```

#### _itemプレースホルダー

AI Map Callステップでは、配列の各要素を表す特別なプレースホルダー `{{ _item }}` が利用できます。このプレースホルダーは、通常のJinja2テンプレート変数とともに使用できます。

```yaml
prompt: |
  テーマ: {{ input.theme }}
  アイテム: {{ _item }}
  
  上記のアイテムを指定されたテーマの観点から分析してください。
```

### Collection ステップ

配列データに対して集合操作を実行します。

```yaml
- id: "collection_step"
  type: "collection"
  operation: "map" | "filter" | "reduce"  # 操作タイプ（必須）
  input: string              # 入力配列テンプレート（必須）
  
  # map/filter用パラメータ
  steps:                     # サブステップ定義（map用）
    - id: "sub_step"
      type: "ai_call"
      prompt: "{{ item }}"
  
  condition: string          # フィルタ条件（filter用）
  
  # reduce用パラメータ
  accumulator_init: any      # 初期値（reduce用）
  reducer_steps:             # リデューサーステップ（reduce用）
    - id: "reducer"
      type: "text_process"
      method: "replace"
```

## テキスト処理メソッド詳細

### regex_extract メソッド

正規表現を使ってテキストからパターンを抽出します。

```yaml
# 基本的な使用
- id: "extract_dates"
  type: "text_process"
  method: "regex_extract"
  input: "{{ input.text }}"
  pattern: "\\d{4}-\\d{2}-\\d{2}"
  flags: ["MULTILINE"]
  output_format: "array"

# 複数マッチの配列出力
- id: "extract_multiple_dates"
  type: "text_process"
  method: "regex_extract"
  input: "{{ input.text }}"
  pattern: "\\d{4}-\\d{2}-\\d{2}"
  output_format: "array"
```

**フラグ**:
- `IGNORECASE` - 大文字小文字を無視
- `MULTILINE` - 複数行モード
- `DOTALL` - `.` が改行にもマッチ
- `VERBOSE` - 詳細モード

**配列出力例**:
```json
["2024-01-15", "2024-02-20", "2024-03-10"]
```

### json_parse メソッド

JSON 文字列を解析してオブジェクトに変換します。

```yaml
# 基本的なJSON解析
- id: "parse_json"
  type: "text_process"
  method: "json_parse"
  input: "{{ input.json_string }}"
```

解析されたJSONは、テンプレートから通常のオブジェクトとしてアクセスできます。

### split メソッド

文字列を指定した区切り文字で分割します。

```yaml
- id: "split_text"
  type: "text_process"
  method: "split"
  input: "apple,banana,orange"
  separator: ","           # 区切り文字（必須）
  max_splits: 2           # 最大分割数（オプション）
```

**パラメータ**:
- `separator` (string, 必須): 分割に使用する区切り文字
- `max_splits` (integer, オプション): 最大分割数

**出力**: `list[string]` - 分割された文字列の配列

### extract_between_marker メソッド

指定されたマーカー文字列間のテキストを抽出します。

```yaml
- id: "extract_xml_data"
  type: "text_process"
  method: "extract_between_marker"
  input: "<item id='1'><name>Product</name></item>"
  begin: "<name>"          # 開始マーカー（必須）
  end: "</name>"           # 終了マーカー（必須）
  extract_all: false      # 全てのマッチを抽出（オプション、デフォルト: false）
```

**パラメータ**:
- `begin` (string, 必須): 開始マーカー文字列
- `end` (string, 必須): 終了マーカー文字列  
- `extract_all` (boolean, オプション): 全てのマッチを抽出するか（デフォルト: false）

### select_item メソッド

配列から要素を選択します。インデックス、スライス、条件による選択をサポート。

```yaml
# インデックスによる選択
- id: "select_first"
  type: "text_process"
  method: "select_item"
  input: "{{ steps.array_data }}"
  index: 0

# スライスによる選択
- id: "select_range"
  type: "text_process"
  method: "select_item"
  input: "{{ steps.array_data }}"
  slice: "1:4"     # Python スライス記法

# 条件による選択
- id: "select_high_score"
  type: "text_process"
  method: "select_item"
  input: "{{ steps.student_data }}"
  condition: "item.score > 80"
```

### parse_as_json メソッド

JSON解析とスキーマ検証機能を提供し、検証結果のメタデータを他のステップから参照可能です。

```yaml
- id: "parse_json_data"
  type: "text_process"  
  method: "parse_as_json"
  input: '{"users": [{"name": "Alice", "age": 30}]}'
  schema_file: "user_schema.json"    # JSONスキーマファイル（オプション）
  strict_validation: true           # スキーマ検証失敗時にエラー（オプション）
  format_output: true              # 整形された出力（オプション）
```

**パラメータ**:
- `schema_file` (string, オプション): JSONスキーマファイルのパス
- `strict_validation` (boolean, オプション): スキーマ検証失敗時にエラーとするか（デフォルト: false）
- `format_output` (boolean, オプション): JSON出力を整形するか（デフォルト: false）

## テンプレートシステム

### 基本構文

Jinja2テンプレートエンジンを使用しています。

```yaml
# 変数参照
prompt: "Hello {{ input.name }}"

# 条件分岐
prompt: |
  {% if input.level == 'advanced' %}
  高度な質問です：{{ input.question }}
  {% else %}
  基本的な質問です：{{ input.question }}
  {% endif %}

# ループ処理
prompt: |
  以下のアイテムを処理してください：
  {% for item in input.items %}
  - {{ item }}
  {% endfor %}
```

### 利用可能な変数

- `input.*` - 入力パラメータ
- `steps.*` - 前のステップの出力
- `config.*` - 設定値
- `env.*` - 環境変数（設定で許可された場合）

### カスタムフィルタ

```yaml
# 利用可能なフィルタ
{{ text | strip_whitespace }}      # 空白文字除去
{{ text | truncate_words(10) }}    # 単語数で切り詰め
{{ text | escape_quotes }}         # クォート文字エスケープ
{{ data | extract_json }}          # JSON部分抽出
{{ data | tojson }}               # JSON文字列化
{{ array | parse_json_array }}     # JSON配列解析
```

## 設定

### デフォルト設定

```yaml
default_provider: "gemini/gemini-2.0-flash"
timeout_per_step: 60
max_parallel_ai_calls: 3

provider_settings:
  gemini:
    api_key: "${GOOGLE_API_KEY}"
    region: "asia-northeast1"
    timeout: 30
  
  openai:
    api_key: "${OPENAI_API_KEY}"
    organization: "org-xxx"
    timeout: 60
    
  anthropic:
    api_key: "${ANTHROPIC_API_KEY}"
    timeout: 45
```

### 環境変数展開

設定値では `${VAR_NAME}` 形式で環境変数を参照できます：

```yaml
provider_settings:
  gemini:
    api_key: "${GOOGLE_API_KEY}"
    project_id: "${GOOGLE_CLOUD_PROJECT}"
```

## CLI オプション

### bakufu run

```bash
bakufu run workflow.yml [OPTIONS]

# 必須引数
workflow.yml              # ワークフローファイルパス

# オプション
-i, --input TEXT          # 入力データ（JSON）
--input-file PATH         # 入力ファイル
-o, --output-format TYPE  # 出力形式（text/json/yaml）
-v, --verbose            # 詳細出力
--dry-run                # 検証のみ（実行しない）
```

### 入力形式

**JSON 文字列**:
```bash
bakufu run workflow.yml --input '{"name": "太郎", "age": 30}'
```

**ファイル指定**:
```bash
bakufu run workflow.yml --input-file input.json
```

**標準入力**:
```bash
echo '{"text": "sample"}' | bakufu run workflow.yml
```

## ベストプラクティス

### ワークフロー設計

1. **明確な命名**: ステップ ID とワークフロー名は分かりやすく
2. **エラーハンドリング**: 重要でないステップは `on_error: continue`
3. **テンプレート分割**: 長いプロンプトは可読性を考慮
4. **出力形式**: 後続処理を考慮した適切な形式選択

### パフォーマンス

1. **プロバイダー選択**: 用途に応じた最適なモデル選択
2. **タイムアウト設定**: 適切なタイムアウト値の設定
3. **並列実行**: 独立したステップは並列実行を検討
4. **キャッシュ**: 同じ処理の再実行を避ける

### セキュリティ

1. **API キー管理**: 環境変数での管理を徹底
2. **入力検証**: 信頼できない入力の適切な処理
3. **出力制限**: 機密情報の出力を避ける
4. **ログ管理**: 機密情報をログに出力しない

---

📖 [リファレンス目次に戻る](README.md)