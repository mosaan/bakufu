#!/bin/bash

SCRIPT_DIR=$(dirname "$0")
# 環境変数を絶対パスで設定
export BAKUFU_CONFIG="../bakufu-example-setting.yml"
echo "Using bakufu config: $BAKUFU_CONFIG"
pushd "$SCRIPT_DIR"

uv run bakufu config test

# bakufu examples実行テスト用スクリプト
# 各ワークフローを実際に実行してテストします

echo "🚀 bakufu examples ワークフロー実行テスト"
echo "========================================"

# basic ディレクトリのテスト
echo ""
echo "📁 basic ディレクトリのテスト"
echo "--------------------"

echo "1. hello-world.yml (デフォルト値使用)"
uv run bakufu run basic/hello-world.yml --verbose

echo ""
echo "2. text-summarizer.yml"
uv run bakufu run basic/text-summarizer.yml \
  --input '{"text": "これはテストテキストです。長い文章を要約するためのサンプルです。bakufuは非常に便利なワークフローツールで、AIを活用した様々なタスクを自動化できます。"}' \
  --verbose

# content-creation ディレクトリのテスト
echo ""
echo "📁 content-creation ディレクトリのテスト"
echo "--------------------"

echo "3. blog-writer.yml"
uv run bakufu run content-creation/blog-writer.yml \
  --input '{"theme": "AI活用の効果的な方法"}' \
  --verbose

echo ""
echo "4. email-template.yml"
uv run bakufu run content-creation/email-template.yml \
  --input '{"purpose": "新商品の提案", "recipient": "取引先"}' \
  --verbose

# data-analysis ディレクトリのテスト
echo ""
echo "📁 data-analysis ディレクトリのテスト"
echo "--------------------"

echo "5. simple-analytics.yml"
uv run bakufu run data-analysis/simple-analytics.yml \
  --input '{"csv_data": "name,age,score\nTaro,25,85\nHanako,30,92\nJiro,22,78\nSakura,28,95"}' \
  --verbose

echo ""
echo "6. log-analyzer.yml"
uv run bakufu run data-analysis/log-analyzer.yml \
  --input '{"log_data": "2024-01-15 10:30:45 INFO Starting application\n2024-01-15 10:30:46 ERROR Database connection failed\n2024-01-15 10:30:47 INFO Retrying connection\n2024-01-15 10:30:48 INFO Connected to database\n2024-01-15 10:31:00 ERROR User authentication failed for user123"}' \
  --verbose

# text-processing ディレクトリのテスト
echo ""
echo "📁 text-processing ディレクトリのテスト"
echo "--------------------"

echo "7. json-extractor.yml"
uv run bakufu run text-processing/json-extractor.yml \
  --input '{"text": "結果は {\"name\": \"田中太郎\", \"age\": 30, \"city\": \"東京\"} でした。"}' \
  --verbose

echo ""
echo "8. markdown-processor.yml"
uv run bakufu run text-processing/markdown-processor.yml \
  --input '{"markdown_text": "# はじめに\nこれはテストドキュメントです。\n\n## セクション1\n詳細な説明をここに記載します。\n\n## セクション2\n追加の情報です。"}' \
  --verbose

# ai-map-call ディレクトリのテスト
echo ""
echo "📁 ai-map-call ディレクトリのテスト"
echo "--------------------"

echo "9. review-sentiment-analysis.yml"
uv run bakufu run ai-map-call/review-sentiment-analysis.yml \
  --input '{
    "reviews": [
      "とても良い商品でした！品質も価格も満足です。",
      "配送が遅すぎる。商品は普通だが対応に不満。",
      "期待通りの性能。コスパは良いと思います。",
      "優れた作りと機能。強くお勧めします！"
    ],
    "product_name": "ワイヤレスイヤホンPro"
  }' \
  --verbose

echo ""
echo "10. long-text-summarizer.yml"
uv run bakufu run ai-map-call/long-text-summarizer.yml \
  --input '{"long_text": "人工知能（AI）は21世紀で最も変革的な技術の一つとなっています。推薦システムを支える機械学習アルゴリズムから、人間とコンピューターの相互作用を可能にする自然言語処理モデルまで、AIは産業と社会を再構築しています。\n\nAIの発展は、アラン・チューリングが有名なチューリングテストを提案した1950年代にさかのぼることができます。しかし、実用的なAIアプリケーションに十分な計算能力とデータの可用性に達したのは、最近の数十年になってからです。\n\n今日、AIアプリケーションは医療、金融、交通、エンターテインメントなど多数の領域にわたっています。医療では、AIは医療診断と薬物発見を支援します。金融では、アルゴリズム取引と不正検出がAI技術に大きく依存しています。\n\nこれらの進歩にもかかわらず、AIは倫理的考慮事項、雇用置換の懸念、規制フレームワークの必要性などの課題も提示しています。今後に向けて、AIを責任を持って開発し、その利益が社会全体に公平に分配されることを確実にすることが重要です。", "target_summary_length": 150}' \
  --verbose

# collection-operations ディレクトリのテスト
echo ""
echo "📁 collection-operations ディレクトリのテスト"
echo "--------------------"

echo "11. filter-example.yml"
uv run bakufu run collection-operations/filter-example.yml \
  --input '{"numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "threshold": 5}' \
  --verbose

echo ""
echo "12. map-example.yml"
uv run bakufu run collection-operations/map-example.yml \
  --input '{
    "reviews": [
      "この商品は素晴らしい！品質が良く配送も早い。",
      "あまり感心しない。品質が悪く高すぎる。",
      "価格に見合った普通の商品。おすすめできる。"
    ]
  }' \
  --verbose

echo ""
echo "13. pipeline-example.yml"
uv run bakufu run collection-operations/pipeline-example.yml \
  --input '{"scores": [45, 67, 89, 92, 78, 34, 88, 91, 76, 55, 83, 94], "passing_grade": 70}' \
  --verbose

# 条件分岐操作のテスト
echo ""
echo "📁 条件分岐操作のテスト (root examples/)"
echo "--------------------"

echo "14. conditional_workflow.yaml"
uv run bakufu run ../conditional_workflow.yaml \
  --input '{
    "user_score": 92,
    "user_name": "太郎",
    "enable_bonus": true
  }' \
  --verbose

echo ""
echo "15. conditional_error_handling.yaml"
uv run bakufu run ../conditional_error_handling.yaml \
  --input '{
    "input_data": {"optional_value": 75},
    "enable_strict_mode": false
  }' \
  --verbose

echo ""
echo "✅ すべてのワークフローテストが完了しました"
echo ""
echo "🔍 追加テスト例:"
echo "--------------------"
echo "# JSON抽出でフィールドパス指定"
echo 'uv run bakufu run text-processing/json-extractor.yml --input '"'"'{"text": "結果は {\"name\": \"田中太郎\", \"age\": 30, \"city\": \"東京\"} でした。", "field_path": "name"}'"'"' --verbose'

echo ""
echo "# CSV分析で分析フォーカス指定"
echo 'uv run bakufu run data-analysis/simple-analytics.yml --input '"'"'{"csv_data": "product,sales,profit\nProduct A,1000,200\nProduct B,1500,300\nProduct C,800,150", "analysis_focus": "売上と利益の相関分析"}'"'"' --verbose'

echo ""
echo "# ブログ記事作成でパラメータ指定"
echo 'uv run bakufu run content-creation/blog-writer.yml --input '"'"'{"theme": "リモートワークの生産性向上", "target_audience": "中小企業の管理職", "word_count": 2000}'"'"' --verbose'

echo ""
echo "# テキスト要約で文字数指定"
echo 'uv run bakufu run basic/text-summarizer.yml --input '"'"'{"text": "人工知能（AI）は、機械が人間の知能を模倣することを可能にする技術です。AIは機械学習、深層学習、自然言語処理など、さまざまな技術を組み合わせて構築されています。近年、AIの発展により、画像認識、音声認識、自動翻訳など、多くの分野で革新的な進歩が見られています。", "max_length": 50}'"'"' --verbose'

echo ""
echo "📝 ドライラン（検証のみ）実行例:"
echo "--------------------"
echo "# 任意のワークフローでドライラン"
echo "uv run bakufu run basic/hello-world.yml --dry-run --verbose"
echo "uv run bakufu validate basic/hello-world.yml --verbose --template-check"

echo ""
echo "🕒 Jinja2標準の日時操作機能:"
echo "--------------------"
echo "# データ分析レポートでは標準的なJinja2のnow()関数を使用"
echo "# {{ now().strftime('%Y-%m-%d %H:%M') }} - 現在時刻をフォーマット"
echo "# {{ now().year }} - 現在の年"
echo "# {{ now().month }} - 現在の月"
echo "# {{ now().day }} - 現在の日"
echo "# カスタムフィルターではなく、Jinja2標準の日時操作を活用"

popd