# コレクション操作ワークフロー

このディレクトリには、map、filter、reduce、パイプラインなどの高階関数を使った関数型プログラミングパターンを可能にする、強力なコレクション操作機能のワークフローが含まれています。

## 🆕 コレクション操作機能

コレクション操作は、関数型プログラミングの概念を使用して配列やリストのデータを宣言的に処理する方法を提供します：

- **Map**: AIやテキスト処理ステップを使用してコレクション内の各要素を変換
- **Filter**: 特定の条件に一致する要素を選択
- **Reduce**: 蓄積を通じて要素を単一の値に集約

## 📁 含まれるワークフロー

### filter-example.yml
**目的**: 条件に基づくコレクションのフィルタリングのデモンストレーション  
**機能**:
- 数値条件に基づく配列のフィルタリング
- 設定可能な閾値パラメータ
- 条件評価のエラーハンドリング
- 統計情報付きJSON出力

**使用例**:
```bash
bakufu run examples/ja/collection-operations/filter-example.yml --input '{
  "numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
  "threshold": 5
}'
```

### map-example.yml
**目的**: AI機能を活用した感情分析によるコレクション変換  
**機能**:
- 並行性制御による並列処理
- 各アイテムのAI機能感情分析
- バッチ処理設定
- 包括的なエラーハンドリング
- JSON構造化出力

**使用例**:
```bash
bakufu run examples/ja/collection-operations/map-example.yml --input '{
  "reviews": [
    "この商品は素晴らしい！品質が良く配送も早い。",
    "あまり感心しない。品質が悪く高すぎる。",
    "価格に見合った普通の商品。おすすめできる。"
  ]
}'
```


## 💡 活用シーン

### データ分析・処理
- **バッチ処理**: 並列AI分析による大規模データセットの処理
- **データフィルタリング**: 複雑な条件に基づくデータセットのフィルタリング
- **統計分析**: reduce操作を使用したデータ集約
- **データ変換**: map操作を使用したデータ形式変換

### コンテンツ処理
- **感情分析**: 複数のレビューやコメントの感情分析
- **コンテンツ分類**: 複数の文書やテキストの分類
- **コンテンツ要約**: 複数の文書の要約生成
- **品質評価**: 複数のコンテンツの採点とランキング

### ビジネスワークフロー
- **成績処理**: 数値スコアから文字評価への変換
- **レビュー分析**: 顧客フィードバックの大規模分析
- **データ検証**: データコレクションのフィルタリングと検証
- **レポート生成**: 処理されたデータからのレポート生成

## 🔧 コレクション操作リファレンス

### Map操作
1つ以上の処理ステップを使用してコレクション内の各要素を変換します。
```yaml
- id: "transform_data"
  type: "collection"
  operation: "map"
  input: "{{ input_array }}"
  concurrency:
    max_parallel: 3
    batch_size: 5
  steps:
    - id: "process_item"
      type: "ai_call"
      prompt: "このアイテムを処理: {{ item }}"
```

### Filter操作
指定された条件に一致する要素を選択します。
```yaml
- id: "filter_data"
  type: "collection"
  operation: "filter"
  input: "{{ input_array }}"
  condition: "{{ item > threshold }}"
  error_handling:
    on_condition_error: "skip_item"
```

### Reduce操作
蓄積を通じて要素を単一の値に集約します。
```yaml
- id: "aggregate_data"
  type: "collection"
  operation: "reduce"
  input: "{{ input_array }}"
  initial_value: ""
  accumulator_var: "acc"
  item_var: "item"
  steps:
    - id: "combine"
      type: "ai_call"
      prompt: "{{ acc }}と{{ item }}を結合"
```


## ⚙️ 設定オプション

### 並行性制御
- `max_parallel`: 最大並列操作数
- `batch_size`: 各バッチで処理するアイテム数

### エラーハンドリング
- `on_item_failure`: アイテム処理失敗時の処理方法（stop/skip/retry）
- `on_condition_error`: 条件評価エラー時の処理方法（stop/skip_item/default_false）

### パフォーマンス最適化
- 独立した操作には並列処理を使用
- データに適したバッチサイズを設定
- 大規模データセットではメモリ使用量を考慮