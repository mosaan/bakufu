# コレクション操作

bakufuのコレクション操作は、データ処理のための関数型プログラミングパターンを提供します。高階関数を使用して、データの変換、フィルタリング、集約を宣言的なアプローチで実行できます。

## 概要

コレクション操作は、新しいステップタイプ`collection`として実装され、異なる操作モードを提供します：

- **map**: コレクション内の各要素を変換
- **filter**: 条件に一致する要素を選択
- **reduce**: 要素を単一の値に集約
- **pipeline**: 複数の操作を連鎖

## 基本構文

```yaml
- id: "step_name"
  type: "collection"
  operation: "map|filter|reduce|pipeline"
  input: "{{ data_reference }}"
  # 操作固有のパラメータ
```

## Map操作

AI呼び出しやテキスト処理ステップを使用して、コレクション内の各要素を変換します。

### 基本的なMap例

```yaml
- id: "process_items"
  type: "collection"
  operation: "map"
  input: "{{ input.data_list }}"
  steps:
    - id: "transform"
      type: "ai_call"
      prompt: "この項目を処理してください: {{ item }}"
```

### 並行処理付きのMap

```yaml
- id: "parallel_processing"
  type: "collection"
  operation: "map"
  input: "{{ input.items }}"
  concurrency:
    max_parallel: 5
    batch_size: 10
  error_handling:
    on_item_failure: "skip"
    max_retries_per_item: 2
  steps:
    - id: "ai_analysis"
      type: "ai_call"
      prompt: "分析してください: {{ item }}"
```

### Mapステップで利用可能な変数

以下の変数をJinja2テンプレート構文（`{{ variable_name }}`）で参照できます：

- `item`: 処理中の現在の要素
  - 例: `{{ item.name }}` - オブジェクトのプロパティ参照
  - 例: `{{ item[0] }}` - 配列要素の参照
- すべての元の入力パラメータ
  - 例: `{{ input_parameters.config_value }}`
- 前のステップの出力
  - 例: `{{ steps.previous_step_id.output }}`

## Filter操作

指定された条件に一致する要素をコレクションから選択します。

### 基本的なFilter例

```yaml
- id: "filter_large_numbers"
  type: "collection"
  operation: "filter"
  input: "{{ input.numbers }}"
  condition: "{{ item > 50 }}"
```

### Filter条件式

条件式にはJinja2テンプレートで利用可能な以下の表現が使用できます：

- **比較演算子**: `>`, `<`, `>=`, `<=`, `==`, `!=`
- **論理演算子**: `and`, `or`, `not`
- **関数**: `length()`, `upper()`, `lower()`, `startswith()`, `endswith()`など
- **メンバーシップ**: `in`, `not in`

### 複雑な条件でのFilter

```yaml
- id: "filter_valid_users"
  type: "collection"
  operation: "filter"
  input: "{{ input.users }}"
  condition: "{{ item.age >= 18 and item.status == 'active' }}"
  error_handling:
    on_condition_error: "skip_item"
```

### Filter条件で利用可能な変数

以下の変数をJinja2テンプレート構文で参照できます：

- `item`: 評価中の現在の要素
  - 例: `{{ item.age >= 18 }}` - 数値比較
  - 例: `{{ item.name.startswith('A') }}` - 文字列操作
- すべての元の入力パラメータ
  - 例: `{{ item.score > input_parameters.min_score }}`
- 前のステップの出力
  - 例: `{{ item.id in steps.valid_ids.output }}`

## Reduce操作

アキュムレータパターンを使用して、コレクション要素を単一の値に集約します。

### 基本的なReduce例

```yaml
- id: "calculate_sum"
  type: "collection"
  operation: "reduce"
  input: "{{ input.numbers }}"
  initial_value: 0
  accumulator_var: "acc"
  item_var: "current"
  steps:
    - id: "add"
      type: "text_process"
      method: "replace"
      input: "{{ acc + current }}"
      replacements: []
```

### AI処理付きのReduce

```yaml
- id: "summarize_reviews"
  type: "collection"
  operation: "reduce"
  input: "{{ input.reviews }}"
  initial_value: ""
  accumulator_var: "summary"
  item_var: "review"
  steps:
    - id: "combine_summaries"
      type: "ai_call"
      prompt: |
        現在の要約: {{ summary }}
        新しいレビュー: {{ review }}
        
        新しいレビューを含む更新された要約を作成してください。
```

### Reduceステップで利用可能な変数

- カスタムアキュムレータ変数（デフォルト: `acc`）
- カスタム項目変数（デフォルト: `item`）
- すべての元の入力パラメータ
- 前のステップの出力

## エラーハンドリング

コレクション操作は、柔軟なエラーハンドリング戦略をサポートします：

### 項目レベルのエラーハンドリング

```yaml
error_handling:
  on_item_failure: "skip"     # skip, stop, retry
  max_retries_per_item: 3
  preserve_errors: true
```

### 条件評価エラー（Filter）

```yaml
error_handling:
  on_condition_error: "skip_item"  # skip_item, stop, default_false
```

## 結果構造

コレクション操作は、以下の構造の`CollectionResult`オブジェクトを返します：

```python
{
  "output": [...],              # 実際の結果データ
  "operation": "map",           # 実行された操作
  "input_count": 10,            # 入力要素数
  "output_count": 8,            # 出力要素数
  "processing_stats": {         # 処理統計
    "processing_time": 2.5,
    "operation": "map",
    "input_count": 10,
    "output_count": 8
  },
  "errors": []                  # 発生したエラー
}
```

### テンプレートでの結果アクセス

```yaml
# メイン出力にアクセス
- id: "next_step"
  type: "ai_call"
  prompt: "これらの結果を処理してください: {{ steps.collection_step }}"

# メタデータにアクセス
- id: "summary"
  type: "ai_call"
  prompt: |
    {{ steps.collection_step.input_count }} 項目を処理しました
    {{ steps.collection_step.output_count }} 件の結果を取得
    操作: {{ steps.collection_step.operation }}
```

## パフォーマンス考慮事項

### 並列実行

Map操作は、パフォーマンス向上のために並列実行をサポートします：

```yaml
concurrency:
  max_parallel: 8        # 最大同時実行操作数
  batch_size: 20         # バッチあたりの項目数
```

### メモリ使用量

- 大きなコレクションはバッチで処理されます
- 非常に大きなデータセットには`chunk_size`を使用
- メモリ使用量を減らすためにパイプライン操作を検討

### AIプロバイダー制限

- 同時実行設定でレート制限を尊重
- 大きなデータセットにはバッチ処理を使用
- 信頼性のためにリトライ戦略を実装

## ai_map_callからの移行

コレクション操作の`map`は、既存の`ai_map_call`ステップを一般化します：

### 旧ai_map_call

```yaml
- id: "process_array"
  type: "ai_map_call"
  input_array: "{{ input.items }}"
  prompt: "処理: {{ _item }}"
```

### 新しいmap操作

```yaml
- id: "process_array"
  type: "collection"
  operation: "map"
  input: "{{ input.items }}"
  steps:
    - id: "process"
      type: "ai_call"
      prompt: "処理: {{ item }}"
```

### 主要な違い

- 変数名: `_item` → `item`
- 複数ステップでより柔軟
- より良いエラーハンドリングオプション
- テキスト処理ステップをサポート

## ベストプラクティス

1. **説明的なステップIDを使用**: ワークフローを自己文書化
2. **エラーを適切に処理**: 適切なエラーハンドリング戦略を設定
3. **同時実行を最適化**: 速度とリソース制限のバランス
4. **小さなデータセットでテスト**: 大きなコレクションを処理する前にロジックを検証
5. **複雑な変換にはパイプラインを使用**: 可読性のために操作を連鎖
6. **パフォーマンスを監視**: 最適化のために処理統計を使用

## 例

完全な動作例については、`examples/collection-operations/`ディレクトリを参照してください：

- `filter-example.yml`: 条件による基本的なフィルタリング
- `map-example.yml`: AI搭載データ変換

## アーキテクチャ決定

従来の制御フローではなく高階関数を使用してコレクション操作を実装することの選択は、[ADR-012](../../dev-docs/adr/adr-012-higher-order-functions-over-control-flow.md)に文書化されています。

---

📖 [機能リファレンス目次に戻る](README.md)