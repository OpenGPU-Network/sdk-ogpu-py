# Contributing to OpenGPU SDK

We welcome contributions to the OpenGPU SDK! This guide will help you get started.

## 🚀 Quick Start

1. **Fork the repository** on GitHub
2. **Clone and setup**:
   ```bash
   git clone https://github.com/your-username/sdk-ogpu-py.git
   cd sdk-ogpu-py
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   ```

3. **Create a branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Make changes and test**:
   ```bash
   pytest tests/
   ```

5. **Submit a pull request**

## 🛠️ Development

### Code Quality

Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

Format and check code:
```bash
black ogpu/
isort ogpu/
flake8 ogpu/
pytest tests/
```

### Documentation

Build docs locally:
```bash
mkdocs serve
```

Visit `http://localhost:8000` to preview changes.

## 📝 Guidelines

### Code Style
- Follow **PEP 8**
- Use **type hints**
- Write **clear docstrings**
- Include **tests** for new features

### Commit Messages
- Use clear, descriptive messages
- Start with action verb (Add, Fix, Update, etc.)
- Keep first line under 50 characters

## 🐛 Bug Reports

Include:
- **Description** of the bug
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, SDK version)
- **Error messages** or stack traces

## 💡 Feature Requests

Include:
- **Problem description**
- **Proposed solution**
- **Use case** and examples
- **Alternative approaches** considered

## 🔄 Pull Request Process

### Before Submitting
- ✅ All tests pass
- ✅ Code is formatted (black, isort)
- ✅ No linting errors (flake8)
- ✅ Documentation updated if needed
- ✅ CHANGELOG.md updated for user-facing changes

### PR Template
```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe how you tested your changes.

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-reviewed code
- [ ] Added/updated tests
- [ ] Updated documentation
- [ ] All tests pass
```

## 🎯 Areas for Contribution

**High Priority:**
- Performance optimizations
- Enhanced error handling
- More examples and tutorials
- Integration tests

**Documentation:**
- Video tutorials
- Advanced use cases
- Troubleshooting guides

## 📞 Getting Help

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community discussion
- **Documentation**: Guides and API reference

Thank you for contributing! 🚀
