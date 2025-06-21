# Contributing to StealthFlow

Welcome to the StealthFlow project! We appreciate your contributions and this guide will help you contribute to the project in the best way possible.

## Table of Contents

- [Quick Start](#quick-start)
- [How to Contribute](#how-to-contribute)
- [Code Standards](#code-standards)
- [Review Process](#review-process)
- [Types of Contributions](#types-of-contributions)
- [Bug Reports](#bug-reports)
- [Feature Requests](#feature-requests)
- [Testing](#testing)
- [Documentation](#documentation)

## Quick Start

### Prerequisites

- Python 3.8+
- Git
- Basic knowledge of networking and internet protocols
- Familiarity with Docker (for server development)

### Setting up Development Environment

1. **Fork the Project**
   ```bash
   # Fork from GitHub UI, then:
   git clone https://github.com/YOUR_USERNAME/stealthflow.git
   cd stealthflow
   ```

2. **Setup Python Environment**
   ```bash
   python -m venv venv
   
   # Windows:
   venv\Scripts\activate
   
   # macOS/Linux:
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Run Tests**
   ```bash
   python -m pytest tests/ -v
   ```

## How to Contribute

### 1. Create an Issue

Before starting work, create an issue to discuss your changes:
- **Bug Reports**: Use the bug report template
- **Feature Requests**: Use the feature request template
- **Documentation**: Create a documentation improvement issue

### 2. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 3. Make Changes

- Follow coding standards
- Write tests for new features
- Update documentation as needed
- Ensure all tests pass

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add new feature description"
```

Follow conventional commit format:
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Test additions/changes
- `chore:` - Maintenance tasks

### 5. Push and Create Pull Request

```bash
git push origin your-branch-name
```

Then create a Pull Request through GitHub interface.

## Code Standards

### Python Code Style

- Follow PEP 8 guidelines
- Use type hints for function parameters and return values
- Maximum line length: 88 characters
- Use descriptive variable and function names

### Example Good Code:

```python
async def validate_proxy_connection(
    proxy_url: str, 
    timeout: int = 10
) -> bool:
    """
    Validate proxy connection availability.
    
    Args:
        proxy_url: The proxy URL to validate
        timeout: Connection timeout in seconds
        
    Returns:
        True if proxy is accessible, False otherwise
    """
    try:
        # Implementation here
        return True
    except Exception as e:
        logger.error(f"Proxy validation failed: {e}")
        return False
```

## Review Process

### Pull Request Requirements

- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance impact is considered

## Types of Contributions

### 1. Bug Fixes
- Fix reported issues
- Add regression tests
- Update documentation if needed

### 2. New Features
- Implement new functionality
- Add comprehensive tests
- Update documentation
- Consider backward compatibility

### 3. Performance Improvements
- Optimize existing code
- Add benchmarks
- Document performance gains

### 4. Documentation
- Improve existing docs
- Add missing documentation
- Fix typos and clarity issues

### 5. Security Improvements
- Fix security vulnerabilities
- Improve security practices
- Add security tests

## Bug Reports

When reporting bugs, include:

**Environment:**
- OS and version
- Python version
- StealthFlow version
- Relevant dependencies

**Bug Description:**
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Error messages/logs

## Feature Requests

For new features, provide:

**Use Case:**
- Why is this feature needed?
- What problem does it solve?
- How would you use it?

**Proposed Solution:**
- High-level description
- API design (if applicable)
- Alternative approaches considered

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=stealthflow

# Run specific test file
python -m pytest tests/test_client.py

# Run with verbose output
python -m pytest -v
```

### Writing Tests

- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies
- Use fixtures for common setup

## Documentation

### Documentation Types

1. **Code Documentation**: Docstrings and comments
2. **API Documentation**: Function/class documentation
3. **User Guides**: How-to guides for users
4. **Developer Guides**: Setup and contribution guides

### Writing Guidelines

- Use clear, concise language
- Include code examples
- Keep documentation up-to-date
- Use proper Markdown formatting

## Security

### Security Considerations

- Never commit secrets or credentials
- Validate all user inputs
- Use secure communication protocols
- Follow OWASP guidelines

### Reporting Security Issues

For security vulnerabilities:
1. **DO NOT** create a public issue
2. Email security@stealthflow.org
3. Include detailed description
4. Provide steps to reproduce
5. Suggest fixes if possible

## Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Maintain professional communication

### Getting Help

- Check existing issues and documentation
- Ask questions in GitHub Discussions
- Join our community channels

## License

By contributing to StealthFlow, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to StealthFlow! Your efforts help make internet freedom accessible to everyone.
