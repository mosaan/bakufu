# Collection Operations Workflows

This directory contains workflows demonstrating the powerful collection operations feature that enables functional programming patterns with higher-order functions like map, filter, reduce, and pipeline operations.

## 🆕 Collection Operations Feature

Collection operations provide a declarative way to process arrays and lists of data using functional programming concepts:

- **Map**: Transform each element in a collection using AI or text processing steps
- **Filter**: Select elements that match specific conditions
- **Reduce**: Aggregate elements into a single value through accumulation

## 📁 Included Workflows

### filter-example.yml
**Purpose**: Demonstrate filtering collections based on conditions  
**Features**:
- Filter arrays based on numeric conditions
- Configurable threshold parameters
- Error handling for condition evaluation
- JSON output with statistics

**Usage Example**:
```bash
bakufu run examples/en/collection-operations/filter-example.yml --input '{
  "numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
  "threshold": 5
}'
```

### map-example.yml
**Purpose**: Transform collections using AI-powered sentiment analysis  
**Features**:
- Parallel processing with concurrency control
- AI-powered sentiment analysis for each item
- Batch processing configuration
- Comprehensive error handling
- JSON structured output

**Usage Example**:
```bash
bakufu run examples/en/collection-operations/map-example.yml --input '{
  "reviews": [
    "This product is amazing! Great quality and fast shipping.",
    "Not impressed. Poor build quality and overpriced.",
    "Decent product for the price. Would recommend."
  ]
}'
```


## 💡 Use Cases

### Data Analysis & Processing
- **Batch Processing**: Process large datasets with parallel AI analysis
- **Data Filtering**: Filter datasets based on complex conditions
- **Statistical Analysis**: Aggregate data using reduce operations
- **Data Transformation**: Transform data formats using map operations

### Content Processing
- **Sentiment Analysis**: Analyze sentiment of multiple reviews or comments
- **Content Classification**: Classify multiple documents or texts
- **Content Summarization**: Generate summaries for multiple documents
- **Quality Assessment**: Score and rank multiple content pieces

### Business Workflows
- **Grade Processing**: Convert numerical scores to letter grades
- **Review Analysis**: Analyze customer feedback at scale
- **Data Validation**: Filter and validate data collections
- **Report Generation**: Generate reports from processed data

## 🔧 Collection Operations Reference

### Map Operation
Transform each element in a collection using one or more processing steps.
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
      prompt: "Process this item: {{ item }}"
```

### Filter Operation
Select elements that match specified conditions.
```yaml
- id: "filter_data"
  type: "collection"
  operation: "filter"
  input: "{{ input_array }}"
  condition: "{{ item > threshold }}"
  error_handling:
    on_condition_error: "skip_item"
```

### Reduce Operation
Aggregate elements into a single value through accumulation.
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
      prompt: "Combine {{ acc }} with {{ item }}"
```


## ⚙️ Configuration Options

### Concurrency Control
- `max_parallel`: Maximum number of parallel operations
- `batch_size`: Number of items to process in each batch

### Error Handling
- `on_item_failure`: How to handle item processing failures (stop/skip/retry)
- `on_condition_error`: How to handle condition evaluation errors (stop/skip_item/default_false)

### Performance Optimization
- Use parallel processing for independent operations
- Configure appropriate batch sizes for your data
- Consider memory usage for large datasets