#!/bin/bash

SCRIPT_DIR=$(dirname "$0")
# Set environment variable with absolute path
export BAKUFU_CONFIG="../bakufu-example-setting.yml"
echo "Using bakufu config: $BAKUFU_CONFIG"
pushd "$SCRIPT_DIR"

uv run bakufu config test

# bakufu examples execution test script
# This script runs each workflow for actual testing

echo "🚀 bakufu examples workflow execution test"
echo "========================================"

# basic directory tests
echo ""
echo "📁 basic directory tests"
echo "--------------------"

echo "1. hello-world.yml (using default values)"
uv run bakufu run basic/hello-world.yml --verbose

echo ""
echo "2. text-summarizer.yml"
uv run bakufu run basic/text-summarizer.yml \
  --input '{"text": "This is test text. This is a sample for summarizing long sentences. bakufu is a very convenient workflow tool that can automate various tasks using AI."}' \
  --verbose

# content-creation directory tests
echo ""
echo "📁 content-creation directory tests"
echo "--------------------"

echo "3. blog-writer.yml"
uv run bakufu run content-creation/blog-writer.yml \
  --input '{"theme": "Effective Methods for AI Utilization"}' \
  --verbose

echo ""
echo "4. email-template.yml"
uv run bakufu run content-creation/email-template.yml \
  --input '{"purpose": "new product proposal", "recipient": "business partner"}' \
  --verbose

# data-analysis directory tests
echo ""
echo "📁 data-analysis directory tests"
echo "--------------------"

echo "5. simple-analytics.yml"
uv run bakufu run data-analysis/simple-analytics.yml \
  --input '{"csv_data": "name,age,score\nJohn,25,85\nJane,30,92\nBob,22,78\nAlice,28,95"}' \
  --verbose

echo ""
echo "6. log-analyzer.yml"
uv run bakufu run data-analysis/log-analyzer.yml \
  --input '{"log_data": "2024-01-15 10:30:45 INFO Starting application\n2024-01-15 10:30:46 ERROR Database connection failed\n2024-01-15 10:30:47 INFO Retrying connection\n2024-01-15 10:30:48 INFO Connected to database\n2024-01-15 10:31:00 ERROR User authentication failed for user123"}' \
  --verbose

# text-processing directory tests
echo ""
echo "📁 text-processing directory tests"
echo "--------------------"

echo "7. json-extractor.yml"
uv run bakufu run text-processing/json-extractor.yml \
  --input '{"text": "The result was {\"name\": \"John Doe\", \"age\": 30, \"city\": \"New York\"}."}' \
  --verbose

echo ""
echo "8. markdown-processor.yml"
uv run bakufu run text-processing/markdown-processor.yml \
  --input '{"markdown_text": "# Introduction\nThis is a test document.\n\n## Section 1\nDetailed explanation goes here.\n\n## Section 2\nAdditional information."}' \
  --verbose

# ai-map-call directory tests
echo ""
echo "📁 ai-map-call directory tests"
echo "--------------------"

echo "9. review-sentiment-analysis.yml"
uv run bakufu run ai-map-call/review-sentiment-analysis.yml \
  --input '{
    "reviews": [
      "Great product! Very satisfied with both quality and price.",
      "Shipping was too slow. Product is average but service was disappointing.",
      "Performance as expected. Good value for money.",
      "Excellent build quality and features. Highly recommended!"
    ],
    "product_name": "Wireless Earphones Pro"
  }' \
  --verbose

echo ""
echo "10. long-text-summarizer.yml"
uv run bakufu run ai-map-call/long-text-summarizer.yml \
  --input '{"long_text": "Artificial Intelligence (AI) has become one of the most transformative technologies of the 21st century. From machine learning algorithms that power recommendation systems to natural language processing models that enable human-computer interaction, AI is reshaping industries and society.\n\nThe development of AI can be traced back to the 1950s when Alan Turing proposed the famous Turing Test. However, it was not until recent decades that computational power and data availability reached levels sufficient for practical AI applications.\n\nToday, AI applications span numerous domains including healthcare, finance, transportation, and entertainment. In healthcare, AI assists in medical diagnosis and drug discovery. In finance, algorithmic trading and fraud detection rely heavily on AI technologies.\n\nDespite these advances, AI also presents challenges including ethical considerations, job displacement concerns, and the need for regulatory frameworks. As we move forward, it is crucial to develop AI responsibly and ensure its benefits are distributed equitably across society.", "target_summary_length": 150}' \
  --verbose

# collection-operations directory tests  
echo ""
echo "📁 collection-operations directory tests"
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
      "This product is amazing! Great quality and fast shipping.",
      "Not impressed. Poor build quality and overpriced.",
      "Decent product for the price. Would recommend."
    ]
  }' \
  --verbose

echo ""
echo "13. pipeline-example.yml"
uv run bakufu run collection-operations/pipeline-example.yml \
  --input '{"scores": [45, 67, 89, 92, 78, 34, 88, 91, 76, 55, 83, 94], "passing_grade": 70}' \
  --verbose

# conditional operations tests
echo ""
echo "📁 conditional operations tests (root examples/)"
echo "--------------------"

echo "14. conditional_workflow.yaml"
uv run bakufu run ../conditional_workflow.yaml \
  --input '{
    "user_score": 92,
    "user_name": "Alice",
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
echo "✅ All workflow tests completed"
echo ""
echo "🔍 Additional test examples:"
echo "--------------------"
echo "# JSON extraction with field path specification"
echo 'uv run bakufu run text-processing/json-extractor.yml --input '"'"'{"text": "The result was {\"name\": \"John Doe\", \"age\": 30, \"city\": \"New York\"}.", "field_path": "name"}'"'"' --verbose'

echo ""
echo "# CSV analysis with analysis focus specification"
echo 'uv run bakufu run data-analysis/simple-analytics.yml --input '"'"'{"csv_data": "product,sales,profit\nProduct A,1000,200\nProduct B,1500,300\nProduct C,800,150", "analysis_focus": "correlation analysis between sales and profit"}'"'"' --verbose'

echo ""
echo "# Blog article creation with parameter specification"
echo 'uv run bakufu run content-creation/blog-writer.yml --input '"'"'{"theme": "Improving Remote Work Productivity", "target_audience": "middle management in small and medium enterprises", "word_count": 2000}'"'"' --verbose'

echo ""
echo "# Text summarization with character count specification"
echo 'uv run bakufu run basic/text-summarizer.yml --input '"'"'{"text": "Artificial Intelligence (AI) is a technology that enables machines to mimic human intelligence. AI is built by combining various technologies such as machine learning, deep learning, and natural language processing. In recent years, the development of AI has led to revolutionary advances in many fields, including image recognition, speech recognition, and automatic translation.", "max_length": 50}'"'"' --verbose'

echo ""
echo "📝 Dry run (validation only) execution examples:"
echo "--------------------"
echo "# Dry run for any workflow"
echo "uv run bakufu run basic/hello-world.yml --dry-run --verbose"
echo "uv run bakufu validate basic/hello-world.yml --verbose --template-check"

echo ""
echo "🕒 Jinja2 standard datetime manipulation features:"
echo "--------------------"
echo "# Data analysis reports use standard Jinja2 now() function"
echo "# {{ now().strftime('%Y-%m-%d %H:%M') }} - format current time"
echo "# {{ now().year }} - current year"
echo "# {{ now().month }} - current month"
echo "# {{ now().day }} - current day"
echo "# Leverage Jinja2 standard datetime operations, not custom filters"

popd