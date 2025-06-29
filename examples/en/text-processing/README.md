# Text Processing Workflows

This directory contains workflows for automating various text processing tasks. Enhanced with powerful new features in v1.1.0.

## 🆕 New in v1.1.0 - Basic Text Processing Methods

Four fundamental text processing methods have been added to provide essential text manipulation capabilities:

- **New Methods**: `split`, `extract_between_marker`, `select_item`, `parse_as_json`
- **Enhanced**: Comprehensive schema validation, metadata generation, flexible input formats
- **Improved**: Better error handling, detailed validation results, performance optimizations

## 📁 Included Workflows

### json-extractor.yml
**Purpose**: Extract and format JSON data from text  
**Features**:
- Extract JSON from text
- Retrieve specified fields
- Display structured data

**Usage Example**:
```bash
bakufu run examples/text-processing/json-extractor.yml --input '{
  "text": "User data: {\"name\": \"John Smith\", \"age\": 30, \"city\": \"New York\"}",
  "field_path": "name"
}'
```

### markdown-processor.yml
**Purpose**: Analysis and processing of Markdown documents  
**Features**:
- Section splitting
- Structure analysis
- Section-wise summary generation
- Table of contents creation

**Usage Example**:
```bash
bakufu run examples/text-processing/markdown-processor.yml --input '{
  "markdown_text": "# Overview\n\nProject overview...\n\n## Details\n\nDetailed explanation...",
  "summary_length": 80
}'
```

### basic-text-methods-demo.yml **(New in v1.1.0)**
**Purpose**: Comprehensive demonstration of new v1.1.0 basic text processing methods  
**Features**:
- String splitting with custom separators and limits
- Text extraction between specific markers (XML, HTML, etc.)
- Array element selection by index, slice, or condition
- JSON parsing with validation and metadata generation
- Integration of multiple text processing methods

**Usage Example**:
```bash
bakufu run examples/en/text-processing/basic-text-methods-demo.yml --input '{
  "csv_data": "apple,banana,orange,grape,kiwi",
  "xml_content": "<products><item><name>Laptop</name><price>999</price></item></products>",
  "json_data": "{\"users\": [{\"name\": \"Alice\", \"age\": 30}]}"
}'
```

## 💡 Use Cases

### v1.1.0 Basic Text Processing
- **Data Processing**: CSV and structured text parsing with flexible splitting
- **Content Extraction**: Extracting specific content from XML/HTML documents
- **Array Operations**: Selecting and filtering array elements programmatically
- **JSON Validation**: Parsing and validating JSON data with schema support

### Existing Features
- **Document Management**: Creating summaries of long manuals
- **Data Extraction**: Extracting necessary information from API responses
- **Content Analysis**: Structural analysis of blog posts and reports
- **Document Conversion**: Format conversion and organization
- **Log Analysis**: Processing and analyzing system logs with structured data extraction

## 🔧 New Methods Reference

### split
Splits strings using custom separators with optional maximum split limits.
```yaml
method: "split"
separator: ","
max_splits: 3
```

### extract_between_marker  
Extracts text between specified begin/end markers with single or multiple extraction modes.
```yaml
method: "extract_between_marker"
begin: "<name>"
end: "</name>"
extract_all: true
```

### select_item
Selects array elements by index, slice notation, or conditional expressions.
```yaml
method: "select_item"
index: 0  # or slice: "1:3" or condition: "len(item) > 5"
```

### parse_as_json
Parses JSON with optional schema validation and metadata generation.
```yaml
method: "parse_as_json"
schema_file: "schema.json"
format_output: true
```
