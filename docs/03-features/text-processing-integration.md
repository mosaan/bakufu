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