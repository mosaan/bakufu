# AI Map Call サンプル

AI Map Call 機能を使用したワークフローのサンプル集です。AI Map Call は配列の各要素に対して並列でAI処理を実行する機能で、LLMのコンテキスト長制限を回避しながら大量データを効率的に処理できます。

## 📁 サンプルワークフロー

### 1. 長文AI並列要約 (`long-text-summarizer.yml`)

**用途**: 長文記事やドキュメントの効率的な要約

**特徴**:
- 長文を段落単位で分割
- 各段落を並列でAI要約
- 段落要約を統合して最終要約を生成
- 処理統計の表示

**使用例**:
```bash
bakufu run examples/ja/ai-map-call/long-text-summarizer.yml \
  --input '{"long_text": "長い記事の内容...", "target_summary_length": 300}'
```

### 2. レビュー感情分析 (`review-sentiment-analysis.yml`)

**用途**: 商品レビューの一括感情分析と集計

**特徴**:
- 複数レビューの並列感情分析
- JSON形式での構造化結果出力
- 感情分布と評価統計の自動集計
- Markdownレポート生成

**使用例**:
```bash
bakufu run examples/ja/ai-map-call/review-sentiment-analysis.yml \
  --input '{
    "reviews": [
      "とても良い商品でした！品質も価格も満足です。",
      "配送が遅すぎる。商品は普通だが対応に不満。",
      "期待通りの性能。コスパは良いと思います。"
    ],
    "product_name": "ワイヤレスイヤホンX"
  }'
```

## 🔧 AI Map Call の主要機能

### 並列実行制御

```yaml
concurrency:
  max_parallel: 3        # 同時実行数（1-10）
  batch_size: 10         # バッチサイズ
  delay_between_batches: 1.0  # バッチ間遅延（秒）
```

### エラーハンドリング

```yaml
error_handling:
  on_item_failure: "skip"    # skip/stop/retry
  max_retries_per_item: 2    # 要素ごとのリトライ回数
```

### _itemプレースホルダー

配列の各要素を `{{ _item }}` で参照できます：

```yaml
prompt: |
  テーマ: {{ input.theme }}
  対象: {{ _item }}
  
  上記の内容を分析してください。
```

## 💡 活用のヒント

### 1. パフォーマンス最適化

- `max_parallel`: プロバイダーのレート制限に応じて調整
- `batch_size`: メモリ使用量とのバランスを考慮
- `delay_between_batches`: API制限回避のため適切な遅延を設定

### 2. エラー対策

- 重要な処理では `on_item_failure: "retry"`
- 大量データでは `on_item_failure: "skip"` で部分失敗を許容
- `max_retries_per_item` で過度なリトライを防止

### 3. コスト管理

- `temperature` を低めに設定して一貫した結果を取得
- `max_tokens` で出力量を制御
- バッチサイズを調整してAPI呼び出し数を最適化

## 🚀 応用アイデア

- **多言語翻訳**: 文章を文単位で分割して並列翻訳
- **ログ分析**: ログエントリの並列分類・異常検知
- **コード解析**: ファイル群の並列品質チェック
- **データ変換**: CSV行の並列フォーマット変換
- **コンテンツ生成**: テンプレートの並列カスタマイズ

AI Map Call により、従来は処理困難だった大量データのAI処理が実用的になります。