# AI Map Call Examples

A collection of workflow samples using the AI Map Call feature. AI Map Call is a functionality that executes AI processing in parallel for each element of an array, enabling efficient processing of large amounts of data while avoiding LLM context length limitations.

## 📁 Sample Workflows

### 1. Long Text Parallel Summarization (`long-text-summarizer.yml`)

**Purpose**: Efficient summarization of long articles or documents

**Features**:
- Split long text into paragraph units
- AI summarization of each paragraph in parallel
- Integration of paragraph summaries to generate final summary
- Processing statistics display

**Usage Example**:
```bash
bakufu run examples/en/ai-map-call/long-text-summarizer.yml \
  --input '{"long_text": "Content of long article...", "target_summary_length": 300}'
```

### 2. Review Sentiment Analysis (`review-sentiment-analysis.yml`)

**Purpose**: Batch sentiment analysis and aggregation of product reviews

**Features**:
- Parallel sentiment analysis of multiple reviews
- Structured result output in JSON format
- Automatic aggregation of sentiment distribution and evaluation statistics
- Markdown report generation

**Usage Example**:
```bash
bakufu run examples/en/ai-map-call/review-sentiment-analysis.yml \
  --input '{
    "reviews": [
      "Great product! Very satisfied with both quality and price.",
      "Shipping was too slow. Product is average but service was disappointing.",
      "Performance as expected. Good value for money."
    ],
    "product_name": "Wireless Earphones X"
  }'
```

## 🔧 Key Features of AI Map Call

### Parallel Execution Control

```yaml
concurrency:
  max_parallel: 3        # Concurrent execution count (1-10)
  batch_size: 10         # Batch size
  delay_between_batches: 1.0  # Delay between batches (seconds)
```

### Error Handling

```yaml
error_handling:
  on_item_failure: "skip"    # skip/stop/retry
  max_retries_per_item: 2    # Retry count per item
```

### _item Placeholder

Each array element can be referenced with `{{ _item }}`:

```yaml
prompt: |
  Theme: {{ input.theme }}
  Target: {{ _item }}
  
  Please analyze the above content.
```

## 💡 Usage Tips

### 1. Performance Optimization

- `max_parallel`: Adjust according to provider rate limits
- `batch_size`: Consider balance with memory usage
- `delay_between_batches`: Set appropriate delays to avoid API limits

### 2. Error Management

- Use `on_item_failure: "retry"` for critical processing
- Use `on_item_failure: "skip"` for large data to allow partial failures
- Use `max_retries_per_item` to prevent excessive retries

### 3. Cost Management

- Set `temperature` lower for consistent results
- Control output volume with `max_tokens`
- Optimize API call count by adjusting batch size

## 🚀 Application Ideas

- **Multi-language Translation**: Split text into sentences for parallel translation
- **Log Analysis**: Parallel classification and anomaly detection of log entries
- **Code Analysis**: Parallel quality checks for file collections
- **Data Transformation**: Parallel format conversion of CSV rows
- **Content Generation**: Parallel customization of templates

AI Map Call makes AI processing of large amounts of data, which was previously difficult to handle, practical.