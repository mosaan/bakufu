# AI Response Auto-Continuation

Bakufu automatically continues AI responses that are truncated due to token limits, ensuring you get complete content without manual intervention.

## Overview

When an AI provider truncates a response due to `max_tokens` limits (indicated by `finish_reason: "length"`), Bakufu can automatically request continuation of the content. This feature:

- **Detects truncated responses** using `finish_reason` 
- **Automatically continues** the conversation to get complete content
- **Accumulates usage and costs** across all continuation calls
- **Prevents runaway costs** with configurable retry limits
- **Works independently** of existing error retry mechanisms

## Configuration

### Global Configuration

Set the default retry limit in your configuration file:

```yaml
# bakufu.yml
global_config:
  max_auto_retry_attempts: 10  # Default: 10, set to 0 to disable
```

### Step-Level Configuration

Override the global setting for specific AI call steps:

```yaml
steps:
  - id: "long_content_generation"
    type: "ai_call"
    prompt: "Generate a comprehensive report on..."
    max_tokens: 1000
    max_auto_retry_attempts: 15  # Override global setting
```

## How It Works

1. **Initial Request**: Bakufu makes the first AI API call with your prompt
2. **Truncation Detection**: If `finish_reason` is "length" or "max_tokens", content is truncated
3. **Automatic Continuation**: Bakufu creates a conversation context and requests continuation
4. **Content Concatenation**: Responses are seamlessly joined together
5. **Usage Accumulation**: Token usage and costs are summed across all calls
6. **Completion**: Process continues until `finish_reason: "stop"` or retry limit reached

## Example

```yaml
name: "Long Article Generation"

global_config:
  max_auto_retry_attempts: 5

steps:
  - id: "write_article"
    type: "ai_call"
    prompt: |
      Write a detailed 3000-word article about renewable energy.
      Include sections on solar, wind, hydro, and emerging technologies.
    max_tokens: 800  # Intentionally small to trigger continuation
    max_auto_retry_attempts: 10  # Allow more retries for this step
```

## Conversation Structure

When continuing, Bakufu creates a natural conversation flow:

```
1st Call:
User: "Write a detailed article about renewable energy..."

2nd Call (if truncated):
User: "Write a detailed article about renewable energy..."
Assistant: [First part of the response]
User: "Please continue from where you left off."

3rd Call (if still truncated):
User: "Write a detailed article about renewable energy..."  
Assistant: [First part + Second part]
User: "Please continue from where you left off."
```

## Usage and Cost Tracking

Auto-continuation properly accumulates metrics across all API calls:

```
🔍 Step: write_article
  📊 Usage: 2,450 prompt tokens, 1,890 completion tokens (4,340 total)
  💰 Cost: $0.00652 USD
  🔄 API calls: 3 (1 initial + 2 continuations)
```

## Configuration Options

| Setting | Level | Default | Description |
|---------|-------|---------|-------------|
| `max_auto_retry_attempts` | Global | 10 | Maximum continuation attempts globally |
| `max_auto_retry_attempts` | Step | None | Override global setting for specific steps |

## Finish Reason Behavior

| Finish Reason | Auto-Continue? | Description |
|---------------|----------------|-------------|
| `"stop"` | No | Normal completion |
| `"length"` | Yes | Truncated due to max_tokens |
| `"max_tokens"` | Yes | Truncated due to token limit |
| `"content_filter"` | No | Content filtered by provider |
| Other | No | Other termination reasons |

## Best Practices

### 1. Set Appropriate Limits
```yaml
# For cost-sensitive applications
max_auto_retry_attempts: 3

# For content quality prioritization  
max_auto_retry_attempts: 20
```

### 2. Use Step-Level Overrides
```yaml
steps:
  # Critical content - allow more retries
  - id: "important_analysis"
    max_auto_retry_attempts: 15
    
  # Quick summaries - fewer retries
  - id: "brief_summary"  
    max_auto_retry_attempts: 2
```

### 3. Monitor Usage
- Check usage summaries to understand continuation patterns
- Adjust `max_tokens` and retry limits based on content needs
- Consider provider-specific token limits and costs

### 4. Disable When Not Needed
```yaml
# For short responses where truncation is unlikely
steps:
  - id: "simple_classification"
    max_auto_retry_attempts: 0  # Disable auto-continuation
```

## Interaction with Other Features

### Error Retries
Auto-continuation works alongside existing error retry logic:
- Error retries handle API failures, rate limits, etc.
- Auto-continuation handles successful but truncated responses
- Both can occur in the same request if needed

### Output Validation
Auto-continuation works with output validation:
- Validation occurs on the final, complete response
- Intermediate truncated responses are not validated
- Retry limits are independent for each feature

### Streaming
Auto-continuation currently works with non-streaming responses only:
- Streaming calls fall back to complete responses for continuation
- Future versions may support streaming continuation

## Troubleshooting

### High Costs
If auto-continuation is causing high costs:
- Reduce `max_auto_retry_attempts`
- Increase `max_tokens` per call to reduce truncation
- Monitor usage patterns and adjust accordingly

### Incomplete Content
If content is still truncated after retries:
- Increase `max_auto_retry_attempts`
- Check if content filtering is causing early termination
- Consider breaking complex requests into smaller parts

### Repetitive Content
If continuation generates repetitive content:
- This may indicate the AI has exhausted the topic
- Consider reducing retry attempts or rephrasing prompts
- Some providers handle continuation better than others

## Technical Details

### Implementation
- Auto-continuation is implemented in the `AIProvider` layer
- Configuration is passed from `ExecutionEngine` to `AIProvider`
- Usage accumulation occurs in the provider before returning to the engine

### Provider Compatibility
- Works with all LiteLLM-supported providers
- MCP Sampling Provider always returns `finish_reason: "stop"`
- Provider-specific behavior may vary for edge cases