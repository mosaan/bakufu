# bakufu ワークフローサンプル集

このディレクトリには、bakufuの機能を学習し、実際のプロジェクトで活用するためのサンプルワークフローが含まれています。

## 📂 カテゴリ別サンプル

### 🔰 basic/ - 基本的なワークフロー
- **hello-world.yml** - 最初の動作確認用
- **text-summarizer.yml** - テキスト要約の基本例

### ⚡ ai-map-call/ - 並列AI処理
- **long-text-summarizer.yml** - 長文の段落別並列要約
- **review-sentiment-analysis.yml** - レビューの並列感情分析

### 📝 text-processing/ - テキスト処理
- **json-extractor.yml** - JSONデータの抽出・整形
- **markdown-processor.yml** - Markdown文書の分析・要約
- **advanced-text-processing.yml** - 高度なテキスト処理デモンストレーション
- **basic-text-methods-demo.yml** - 基本テキスト処理メソッドデモンストレーション

### 📄 content-creation/ - コンテンツ作成
- **blog-writer.yml** - SEO最適化されたブログ記事生成
- **email-template.yml** - ビジネスメール文面作成

### 📊 data-analysis/ - データ分析
- **simple-analytics.yml** - CSV データの基本分析
- **log-analyzer.yml** - アプリケーションログ解析

## 🚀 クイックスタート

### 1. 最初の実行
```bash
# Hello Worldワークフローで動作確認
bakufu run examples/basic/hello-world.yml --input '{"name": "太郎"}'

# 文書要約を試す
bakufu run examples/basic/text-summarizer.yml --input '{"text": "長いテキスト...", "max_length": 150}'
```

### 2. コンテンツ作成
```bash
# ブログ記事作成
bakufu run examples/content-creation/blog-writer.yml --input '{"theme": "AI活用術"}'

# ビジネスメール作成
bakufu run examples/content-creation/email-template.yml --input '{"purpose": "問い合わせ", "recipient": "取引先"}'
```

### 3. AI Map Call (並列処理)
```bash
# レビュー感情分析
bakufu run examples/ai-map-call/review-sentiment-analysis.yml --input '{"reviews": ["とても良い商品です！", "品質に不満があります"], "product_name": "テスト商品"}'

# 長文要約
bakufu run examples/ai-map-call/long-text-summarizer.yml --input '{"long_text": "非常に長いテキストの内容...", "target_summary_length": 200}'
```

### 4. データ分析
```bash
# CSVデータ分析
bakufu run examples/data-analysis/simple-analytics.yml --input '{"csv_data": "name,age,score\n太郎,25,85\n花子,30,92"}'

# ログ解析
bakufu run examples/data-analysis/log-analyzer.yml --input '{"log_data": "2024-01-01 10:00:00 INFO Start\n2024-01-01 10:01:00 ERROR Connection failed"}'
```

## 設定例

### 基本設定
```bash
# API キーの設定
export GOOGLE_API_KEY="your_gemini_api_key"
export OPENAI_API_KEY="your_openai_api_key"

# 初期設定
bakufu config init
```

## ヘルプ
```bash
bakufu --help
bakufu run --help
bakufu validate examples/basic/hello-world.yml
```