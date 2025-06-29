# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2025-06-19

### Added
- 🎯 **Real-time Progress Display System** - Comprehensive progress monitoring for workflow execution
  - Visual progress bars for AI Map Call processing with Rich library
  - Real-time item count display (completed/total, e.g., "48/50")
  - Current processing item information
  - Live error count and retry statistics
  - Success rate monitoring with percentage display
  - API call count, token usage, and cost tracking
- 🖥️ **Environment-aware Output** - Automatic detection and optimized display for different environments
  - Interactive mode: Rich progress bars with visual indicators
  - CI/CD mode: Structured logging for automation pipelines
  - Test mode: Minimal output to avoid interference
  - JSON/YAML output: Suppressed progress display for clean structured output
- 📊 **Workflow-level Progress Tracking** - Overall workflow execution monitoring
  - Step-by-step progression display
  - Elapsed time and ETA estimation
  - Comprehensive execution statistics
- 🔤 **Basic Text Processing Methods (v1.1.0)** - Four new fundamental text processing methods
  - `split` - Split strings with custom separators and maximum split limits
  - `extract_between_marker` - Extract text between specified begin/end markers with single or multiple extraction modes
  - `select_item` - Select array elements by index, slice notation, or conditional expressions with support for JSON arrays and CSV strings
  - `parse_as_json` - Parse JSON with optional schema validation, metadata generation, and validation result references

### Enhanced
- 🚀 **AI Map Call Processor** - Enhanced with progress callback system
- 🔧 **Execution Engine** - Integrated workflow-level progress tracking
- 🎨 **CLI Interface** - Enhanced with ProgressManager initialization and event handling
- 📊 **JSON Processing** - Enhanced JSON parsing with schema validation support using jsonschema library
- 🔧 **Array Processing** - Improved array handling with flexible input formats (arrays, JSON strings, CSV strings)
- 📝 **Documentation** - Comprehensive documentation updates with detailed examples and API references

### Fixed
- 🐛 **Structured Output Format Tests** - Fixed JSON/YAML output corruption due to progress message interference
- 🔧 **Duplicate Progress Messages** - Resolved double workflow initialization causing duplicate progress messages

### Technical
- Added new `bakufu.core.progress` module with comprehensive progress management
- Implemented `ProgressManager` class for orchestrating all progress displays
- Created progress data models: `WorkflowProgressData`, `AIMapProgressData`, `AIMapUpdateData`
- Added environment detection system for optimal output format selection
- Enhanced AI Map Call processor with real-time progress callbacks
- Updated execution engine with workflow-level progress integration
- Refactored complex methods to reduce cyclomatic complexity and improve maintainability
- Added proper type annotations and mypy compliance with types-jsonschema
- Implemented comprehensive error handling with detailed suggestions
- Created demonstration workflows showcasing new functionality
- Comprehensive test suite with 53+ new tests achieving 87.90% overall coverage

## [0.2.0] - 2025-06-16

### Enhanced
- 🔧 **Refactored text processing architecture** - Applied polymorphism to eliminate switch-like code smell
- 📚 **Improved code maintainability** - Split TextProcessStep into method-specific classes
- 🎯 **Better type safety** - Each text processing method now has its own dedicated class
- 🧪 **Updated test structure** - Comprehensive test coverage for new class hierarchy

### Technical
- Split `TextProcessStep` into specialized classes: `RegexExtractStep`, `ReplaceStep`, `JsonParseStep`, `MarkdownSplitStep`
- Implemented factory pattern for text processor instantiation
- Updated execution engine to handle new class structure
- Maintained backward compatibility with existing workflow files

## [0.1.0] - 2025-06-16 (Initial Development)

### Added
- 🚀 Core "straight-line" workflow execution engine
- 🤖 Various AI provider integration with LiteLLM
- 📝 Basic text processing methods (regex_extract, replace, json_parse, markdown_split)
- 🎨 Jinja2 template engine with few globals (now)
- 📚 Comprehensive sample workflow collection (7 workflows across 4 categories)

### Technical Foundation
- 🐍 Python 3.12+ support with modern type annotations
- 🛠️ uv-based dependency management
- 🔍 Complete type safety with mypy
- 🎯 Code quality enforcement with ruff
- 📊 Test coverage monitoring

### Infrastructure
- 📁 Organized project structure
- 🔧 Development environment setup with CLAUDE.md
- 📖 Technical specifications and implementation notes
- 🎯 Error handling specifications
- 👥 User experience design documentation

---

## Categories

- **Added**: New features
- **Changed**: Changes in existing functionality  
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Vulnerability fixes
- **Enhanced**: Improvements to existing features
- **Technical**: Internal technical changes