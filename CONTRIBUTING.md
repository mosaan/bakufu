# Contributing to bakufu

Thank you for contributing to bakufu! This document explains how to contribute to the project.

## 🚀 Getting Started

### Development Environment Setup

1. **Install uv**
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Fork and Clone the Repository**
   ```bash
   git clone https://github.com/mosaan/bakufu.git
   cd bakufu
   ```

3. **Install Dependencies**
   ```bash
   # Install with development dependencies
   uv sync --all-extra
   ```

4. **Verify Installation**
   ```bash
   # Run tests
   uv run pytest
   
   # Code quality checks
   uv run ruff format
   uv run ruff check
   uv run mypy bakufu
   ```

## 🛠️ Development Workflow

### Maintaining Code Quality

After implementing new features or making changes to existing code, always execute the following steps:

```bash
# 1. Code formatting
uv run ruff format

# 2. Lint check
uv run ruff check

# 3. Fix auto-fixable issues
uv run ruff check --fix

# 4. Type check
uv run mypy bakufu

# 5. Run tests (with coverage)
uv run pytest --cov=bakufu --cov-report=html --cov-report=term

# 6. Run all checks (recommended)
uv run ruff format && uv run ruff check && uv run mypy bakufu && uv run pytest --cov=bakufu
```

### Test Coverage Requirements

- **Overall Coverage**: 80% or higher
- **New Features**: 90% or higher
- **Core Features**: 95% or higher

If coverage falls below the threshold, please create additional tests.

### Branch Strategy

- `main` - Stable release branch
- `feature/feature-name` - New feature development
- `fix/fix-description` - Bug fixes
- `docs/update-description` - Documentation updates

```bash
# Examples of creating new feature branches
git checkout -b feature/new-text-processor
git checkout -b fix/template-error-handling
git checkout -b docs/update-readme
```

## 📝 Types of Contributions

### 🐛 Bug Reports

If you find a bug, please report it on [GitHub Issues](https://github.com/mosaan/bakufu/issues).

**Required Information**:
- bakufu version
- Python version
- OS and version
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error messages (if any)

**Issue Template**:
```markdown
## Environment
- bakufu version: 
- Python version: 
- OS: 

## Problem Description
(Brief description)

## Steps to Reproduce
1. 
2. 
3. 

## Expected Behavior
(What you expected to happen)

## Actual Behavior
(What actually happened)

## Error Messages
```
(Paste error messages if any)
```
```

### ✨ Feature Requests

Please submit new feature proposals on [GitHub Issues](https://github.com/mosaan/bakufu/issues).

**Considerations**:
- Necessity and use cases for the feature
- Consistency with existing features
- Implementation complexity
- Performance impact

### 🔧 Code Contributions

## 📋 Pull Request Guidelines

### Pre-PR Checklist

- [ ] Issue association completed
- [ ] Code quality checks passed (ruff + mypy)
- [ ] Tests added and run (coverage verified)
- [ ] Documentation updated (if necessary)
- [ ] CHANGELOG.md updated (if breaking changes)

### PR Title

Please use the following format:

```
<type>: <description>

# Examples
feat: Add JSON validation for text_process steps
fix: Handle template rendering errors properly
docs: Update API documentation for AI providers
test: Add integration tests for workflow execution
refactor: Simplify error handling in execution engine
```

**Types**:
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation update
- `test` - Test addition/modification
- `refactor` - Refactoring
- `perf` - Performance improvement
- `style` - Code style fix
- `ci` - CI/CD related

### PR Description

```markdown
## Overview
(Brief description of changes)

## Changes
- Change 1
- Change 2

## Testing
- [ ] Unit tests added
- [ ] Integration tests verified
- [ ] Manual testing performed

## Related Issues
Closes #123

## Breaking Changes
(List if any)

## Screenshots
(If UI changes)
```

## 🙏 Acknowledgments

Thank you for contributing to the bakufu project. Your contributions help more people benefit from AI-powered workflow automation.

If you have any questions, please feel free to let us know through Issues or Discussions!