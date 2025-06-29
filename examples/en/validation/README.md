# AI Output Validation Examples

This directory contains examples demonstrating the AI output validation features in Bakufu. These examples show how to ensure structured, reliable outputs from AI models using various validation strategies.

## Examples

### 1. JSON Schema Validation (`json-schema-validation.yml`)

Demonstrates basic JSON schema validation for sentiment analysis:

- **Features**: JSON schema validation, retry mechanism, force JSON output
- **Use Case**: Structured sentiment analysis with guaranteed output format
- **Schema**: Validates sentiment (enum), confidence (0-1 range), and summary (min length)

**Usage:**
```bash
bakufu run json-schema-validation.yml --text "I love this product! It works perfectly."
```

### 2. AI Map Call Validation (`ai-map-validation.yml`)

Shows validation in parallel AI map operations for processing multiple reviews:

- **Features**: Parallel validation, error handling, aggregation
- **Use Case**: Batch processing of product reviews with structured output
- **Validation**: Individual review analysis + overall summary validation

**Usage:**
```bash
bakufu run ai-map-validation.yml --product_reviews '["Great product!", "Not so good", "Amazing quality"]'
```

### 3. Output Recovery (`output-recovery.yml`)

Demonstrates recovery from messy AI outputs using pattern extraction:

- **Features**: Pattern-based JSON extraction, partial success handling
- **Use Case**: Extracting structured data from verbose AI responses
- **Recovery**: Uses regex to extract JSON from markdown code blocks

**Usage:**
```bash
bakufu run output-recovery.yml --data_request "Extract top 5 programming languages with popularity data"
```

## Validation Configuration Options

### Schema Validation
```yaml
validation:
  schema:
    type: object
    required: [field1, field2]
    properties:
      field1: { type: string }
      field2: { type: number, minimum: 0 }
```

### Retry Configuration
```yaml
validation:
  max_retries: 3
  retry_prompt: "Custom retry instructions..."
  force_json_output: true
```

### Output Recovery
```yaml
validation:
  allow_partial_success: true
  extract_json_pattern: '```json\s*(\{.*?\})\s*```'
```

### Pydantic Model Validation
```yaml
validation:
  pydantic_model: "MyDataModel"  # References a Pydantic class
  max_retries: 2
```

### Custom Validation
```yaml
validation:
  custom_validator: "my_custom_validator"  # References a custom function
  criteria:
    min_length: 100
    required_keywords: ["important", "keyword"]
```

## Key Benefits

1. **Reliability**: Ensures AI outputs match expected structure
2. **Robustness**: Automatic retry with improved prompts
3. **Flexibility**: Multiple validation strategies (schema, Pydantic, custom)
4. **Recovery**: Intelligent extraction from messy outputs
5. **Performance**: Validation in parallel map operations

## Best Practices

1. **Start Simple**: Begin with basic JSON schema validation
2. **Appropriate Retries**: Use 1-3 retries to balance reliability and cost
3. **Clear Schemas**: Define precise, minimal required fields
4. **Recovery Patterns**: Use regex patterns for common AI output formats
5. **Error Handling**: Configure appropriate failure strategies for your use case