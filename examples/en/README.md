# bakufu Workflow Sample Collection

This directory contains sample workflows to learn bakufu functionality and utilize it in actual projects.

## 📂 Category-wise Samples

### 🔰 basic/ - Basic Workflows
- **hello-world.yml** - Initial functionality check
- **text-summarizer.yml** - Basic text summarization example

### ⚡ ai-map-call/ - Parallel AI Processing
- **long-text-summarizer.yml** - Parallel summarization of long text by paragraphs
- **review-sentiment-analysis.yml** - Parallel sentiment analysis of reviews

### 📝 text-processing/ - Text Processing
- **json-extractor.yml** - JSON data extraction and formatting
- **markdown-processor.yml** - Markdown document analysis and summarization
- **advanced-text-processing.yml** - Advanced text processing demonstration
- **basic-text-methods-demo.yml** - Basic text methods demonstration

### 📄 content-creation/ - Content Creation
- **blog-writer.yml** - SEO-optimized blog post generation
- **email-template.yml** - Business email template creation

### 📊 data-analysis/ - Data Analysis
- **simple-analytics.yml** - Basic CSV data analysis
- **log-analyzer.yml** - Application log analysis

## 🚀 Quick Start

### 1. First Execution
```bash
# Check functionality with Hello World workflow
bakufu run examples/basic/hello-world.yml --input '{"name": "John"}'

# Try document summarization
bakufu run examples/basic/text-summarizer.yml --input '{"text": "Long text...", "max_length": 150}'
```

### 2. Content Creation
```bash
# Blog post creation
bakufu run examples/content-creation/blog-writer.yml --input '{"theme": "AI Best Practices"}'

# Business email creation
bakufu run examples/content-creation/email-template.yml --input '{"purpose": "inquiry", "recipient": "business partner"}'
```

### 3. AI Map Call (Parallel Processing)
```bash
# Review sentiment analysis
bakufu run examples/ai-map-call/review-sentiment-analysis.yml --input '{"reviews": ["Great product!", "Disappointing quality"], "product_name": "Test Product"}'

# Long text summarization
bakufu run examples/ai-map-call/long-text-summarizer.yml --input '{"long_text": "Very long text content...", "target_summary_length": 200}'
```

### 4. Data Analysis
```bash
# CSV data analysis
bakufu run examples/data-analysis/simple-analytics.yml --input '{"csv_data": "name,age,score\nJohn,25,85\nJane,30,92"}'

# Log analysis
bakufu run examples/data-analysis/log-analyzer.yml --input '{"log_data": "2024-01-01 10:00:00 INFO Start\n2024-01-01 10:01:00 ERROR Connection failed"}'
```

## Configuration Examples

### Basic Configuration
```bash
# Set API keys
export GOOGLE_API_KEY="your_gemini_api_key"
export OPENAI_API_KEY="your_openai_api_key"

# Initial setup
bakufu config init
```

## Help
```bash
bakufu --help
bakufu run --help
bakufu validate examples/basic/hello-world.yml
```
