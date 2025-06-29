# Content Creation Workflows

This directory contains workflows for automatically generating high-quality content.

## 📁 Included Workflows

### blog-writer.yml
**Purpose**: Automatic generation of SEO-optimized blog posts  
**Features**:
- Keyword research
- Structure planning
- Generation of introduction, body, and conclusion
- Metadata addition

**Usage Example**:
```bash
bakufu run examples/content-creation/blog-writer.yml --input '{
  "theme": "Improving Remote Work Productivity",
  "target_audience": "IT company managers",
  "word_count": 2000
}'
```

### email-template.yml
**Purpose**: Automatic creation of purpose-specific business email templates  
**Features**:
- Context analysis
- Appropriate formality level selection
- Generation of subject line, greeting, body, and closing
- Business etiquette compliance

**Usage Example**:
```bash
bakufu run examples/content-creation/email-template.yml --input '{
  "purpose": "New service proposal",
  "recipient": "Existing client",
  "tone": "Professional and courteous",
  "key_points": "Cost reduction benefits, implementation schedule, support system"
}'
```

## 💡 Use Cases

### Marketing
- Blog post mass production
- Social media post creation
- Press release drafting

### Business Communication
- Proposal email creation
- Customer communication letters
- Internal communication emails

### Content Strategy
- SEO content planning
- User guide creation
- FAQ document generation

## 🎯 Optimization Points

1. **Clear Target Definition**: Set specific reader demographics
2. **Keyword Strategy**: SEO-conscious keyword selection
3. **Consistent Style**: Adjust to match brand tone
4. **Structured Layout**: Reader-friendly heading structure
