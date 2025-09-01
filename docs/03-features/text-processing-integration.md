# テキスト処理機能の統合

Bakufuでは、入力ファイル処理とワークフロー中の文テキスト処理が統合された共通のライブラリを使用しています。これにより、一貫性のあるデータ処理と豊富な形式サポートが実現されています。

## 概要

Bakufuのテキスト処理機能は以下の特徴を持ちます：

- **統一されたアーキテクチャ**: 入力処理とワークフロー内処理で同一のライブラリを使用
- **豊富な形式サポート**: JSON、YAML、CSV、TSV、プレーンテキストに対応
- **カスタマイズ可能**: 区切り文字、エンコーディング、エラーハンドリングの設定が可能
- **高い信頼性**: 包括的なテストとエラーハンドリング

## 新機能: CSV/TSV/YAML解析ステップ

### CSV解析 (`csv_parse`)

CSV形式のテキストを構造化データに変換します。

```yaml
- id: parse_sales_data
  type: text_process
  method: csv_parse
  input: |
    name,age,city
    John,30,NYC
    Jane,25,LA
  delimiter: ","  # オプション：カスタム区切り文字
```

**出力例**:
```json
[
  {"name": "John", "age": "30", "city": "NYC"},
  {"name": "Jane", "age": "25", "city": "LA"}
]
```

**主要機能**:
- 自動区切り文字検出
- カスタム区切り文字対応（`;`, `|`, `\t` など）
- 引用符で囲まれたフィールドのサポート
- ヘッダー行の自動処理

### TSV解析 (`tsv_parse`)

タブ区切り値（TSV）形式のテキストを解析します。

```yaml
- id: parse_product_data
  type: text_process
  method: tsv_parse
  input: |
    product	price	category
    Laptop	1299.99	Electronics
    Book	19.99	Education
```

**出力例**:
```json
[
  {"product": "Laptop", "price": "1299.99", "category": "Electronics"},
  {"product": "Book", "price": "19.99", "category": "Education"}
]
```

### YAML解析 (`yaml_parse`)

YAML形式のテキストを構造化データに変換します。

```yaml
- id: parse_config
  type: text_process
  method: yaml_parse
  input: |
    database:
      host: localhost
      port: 5432
    features:
      - auth
      - logging
```

**出力例**:
```json
{
  "database": {
    "host": "localhost", 
    "port": 5432
  },
  "features": ["auth", "logging"]
}
```

**サポート機能**:
- ネストした構造
- 配列とオブジェクト
- コメント
- マルチライン文字列
- アンカーとエイリアス

## 新機能: Jinja2テンプレート形式化（format）

### テンプレート形式化 (`format`)

**概要**:
`format`メソッドは、Jinja2テンプレートエンジンを使用してテキストを動的に生成する新しい機能です。AI呼び出しを使わずに、純粋なテンプレート処理でテキストを形式化できます。

**基本的な使用法**:
```yaml
- id: simple_greeting
  type: text_process
  method: format
  template: "Hello {{ user_name }}! You are {{ user_age }} years old."
  input: "dummy"  # format メソッドでは使用されないが、基底クラスで必須
```

**出力例**:
```
Hello TestUser! You are 25 years old.
```

### 主要機能

#### 1. 条件分岐
```yaml
- id: conditional_message
  type: text_process
  method: format
  template: |
    {% if user_age >= 18 %}
    Welcome, {{ user_name }}! You are an adult.
    {% else %}
    Hi {{ user_name }}! You are still a minor.
    {% endif %}
  input: "dummy"
```

#### 2. ループ処理
```yaml
- id: product_list
  type: text_process
  method: format
  template: |
    Product Report:
    {% for item in products %}
    {{ loop.index }}. {{ item.name }} - {{ item.price }}円
    {% endfor %}
  input: "dummy"
```

#### 3. ステップ結果の参照
```yaml
- id: step_reference_example
  type: text_process
  method: format
  template: |
    Processing Results:
    - Data count: {{ steps.previous_step.result | length }}
    - First item: {{ steps.previous_step.result[0].name }}
  input: "dummy"
```

#### 4. 高度なフィルタリング
```yaml
- id: advanced_formatting
  type: text_process
  method: format
  template: |
    {% set expensive_items = products | selectattr('price', '>', 10000) | list %}
    {% set cheap_items = products | selectattr('price', '<=', 10000) | list %}
    
    Expensive Items ({{ expensive_items | length }}):
    {% for item in expensive_items %}
    - {{ item.name }}: {{ item.price }}円
    {% endfor %}
    
    Affordable Items ({{ cheap_items | length }}):
    {% for item in cheap_items %}
    - {{ item.name }}: {{ item.price }}円
    {% endfor %}
  input: "dummy"
```

### 利用可能なJinja2機能

#### 変数とデータアクセス
- `{{ variable }}` - 変数の値を出力
- `{{ dict.key }}` - 辞書のキーアクセス
- `{{ list[0] }}` - リストの要素アクセス
- `{{ steps.step_id.result }}` - 他のステップの結果を参照

#### 制御構造
- `{% if condition %}...{% endif %}` - 条件分岐
- `{% for item in items %}...{% endfor %}` - ループ処理
- `{% set variable = value %}` - 変数設定

#### フィルタ
- `{{ text | upper }}` - 大文字変換
- `{{ text | lower }}` - 小文字変換
- `{{ text | title }}` - タイトルケース変換
- `{{ list | length }}` - リストの長さ
- `{{ list | first }}` - リストの最初の要素
- `{{ list | last }}` - リストの最後の要素
- `{{ list | sum }}` - リストの合計
- `{{ list | sum(attribute='price') }}` - 属性の合計
- `{{ list | selectattr('price', '>', 1000) }}` - 条件でフィルタ
- `{{ list | groupby('category') }}` - グループ化
- `{{ data | tojson }}` - JSON形式で出力

#### マクロ
```yaml
template: |
  {% macro format_price(price) %}
  {% if price >= 10000 %}
  {{ "%.1f"|format(price/10000) }}万円
  {% else %}
  {{ price }}円
  {% endif %}
  {% endmacro %}
  
  Price: {{ format_price(product.price) }}
```

### 実用的な使用例

#### 1. セキュリティチェックリストのバッチ処理
```yaml
- id: security_checklist_batch
  type: text_process
  method: format
  template: |
    Security Checklist Review ({{ (items | length / 3) | round | int }} batches):
    
    {% for batch in items | batch(3) %}
    ## Batch {{ loop.index }}
    {% for item in batch %}
    {{ loop.index }}. {{ item.title }}
       Status: {{ item.status }}
       Priority: {{ item.priority }}
    {% endfor %}
    
    {% endfor %}
  input: "dummy"
```

#### 2. レポート生成
```yaml
- id: monthly_report
  type: text_process
  method: format
  template: |
    # 月次レポート {{ now().strftime('%Y-%m') }}
    
    ## 概要
    - 処理件数: {{ data | length }}
    - 成功率: {{ (data | selectattr('status', 'eq', 'success') | list | length / data | length * 100) | round(1) }}%
    
    ## 詳細
    {% for category, items in data | groupby('category') %}
    ### {{ category | title }}
    {% for item in items %}
    - {{ item.name }}: {{ item.value }}
    {% endfor %}
    {% endfor %}
  input: "dummy"
```

### エラーハンドリング

FormatStepは、テンプレートエラーに対して詳細なエラーメッセージを提供します：

```yaml
# テンプレートエラーの例
- id: invalid_template
  type: text_process
  method: format
  template: "{{ undefined_variable }}"  # エラー: 未定義変数
  input: "dummy"
```

**エラーメッセージ例**:
```
Template rendering error: 'undefined_variable' is undefined
```

### パフォーマンス特性

- **高速処理**: AI呼び出しが不要なため、非常に高速
- **メモリ効率**: テンプレートエンジンによる効率的な処理
- **スケーラビリティ**: 大量のデータ処理に適している

### 適用シーン

1. **データの再構成**: 構造化データの表示形式変換
2. **レポート生成**: 定型的なレポートの自動生成
3. **バッチ処理**: 複数項目をまとめた処理
4. **条件分岐**: 入力データに基づく動的な出力生成
5. **フィルタリング**: 特定の条件でのデータ抽出と表示

### 制限事項

- **AIによる推論は不可**: 純粋なテンプレート処理のみ
- **複雑なロジック**: 複雑なビジネスロジックは不適切
- **外部API呼び出し**: 外部サービスとの連携は不可

FormatStepは、AI処理と組み合わせることで、効率的で柔軟なワークフローを構築できる強力なツールです。

## 入力ファイル処理での使用

これらの機能は、ワークフローの入力ファイル処理でも利用できます：

```yaml
name: data_processing_workflow
description: 複数形式のデータファイルを処理

inputs:
  sales_csv: sales_data.csv
  config_yaml: config.yaml
  products_tsv: products.tsv

steps:
  - id: analyze_sales
    type: ai_call
    prompt: |
      売上データを分析してください：
      {{ inputs.sales_csv | tojson }}
```

## 高度な使用例

### 複数ステップでのデータ変換

```yaml
steps:
  # Step 1: CSV解析
  - id: parse_data
    type: text_process
    method: csv_parse
    input: "{{ raw_csv_data }}"
    delimiter: ";"

  # Step 2: データ変換
  - id: transform_data
    type: text_process
    method: array_transform
    input: "{{ steps.parse_data.output }}"
    transform: |
      {
        "name": item.name,
        "total": (item.quantity|int * item.price|float)|round(2)
      }

  # Step 3: フィルタリング
  - id: filter_high_value
    type: text_process
    method: array_filter
    input: "{{ steps.transform_data.output }}"
    condition: "item.total > 100"
```

### エラーハンドリング

各解析ステップでは、適切なエラーメッセージと修正提案が提供されます：

```yaml
# 無効なCSVデータの場合
- id: parse_invalid_csv
  type: text_process
  method: csv_parse
  input: "name,age\nJohn,30,extra_field"  # フィールド数不一致
  # エラー：「CSV形式エラー：列数が一致しません」
  # 提案：「ヘッダーの存在確認」「区切り文字の確認」
```

## パフォーマンス最適化

- **メモリ効率**: 大きなファイルでもストリーミング処理
- **キャッシュ**: 同一ファイルの重複読み込み回避
- **並列処理**: 複数ファイルの同時処理サポート

## 制限事項と注意点

1. **ファイルサイズ制限**: デフォルト10MB（設定変更可能）
2. **エンコーディング**: UTF-8推奨（他の形式も対応）
3. **メモリ使用量**: 大きなデータセットは分割処理を推奨

## 移行ガイド

既存のワークフローでは、新機能への移行は自動的に行われます。追加の設定は不要です。

### 新機能を活用する場合

```yaml
# 従来の方法
- id: manual_csv_parsing
  type: ai_call
  prompt: |
    このCSVデータを解析してください：
    {{ csv_text }}

# 新しい方法
- id: automatic_csv_parsing
  type: text_process
  method: csv_parse
  input: "{{ csv_text }}"
```

## 関連資料

- [ワークフロー仕様書](../07-reference/workflow-specification.md)
- [実用例集](../06-examples/README.md)
- [テンプレート機能](../04-templates/README.md)