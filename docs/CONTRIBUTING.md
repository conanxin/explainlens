# Contributing to ExplainLens

Thank you for your interest in contributing!

## How to Contribute

### Reporting Issues

- Use the GitHub Issues tracker
- Describe the bug or feature request clearly
- Include steps to reproduce for bugs
- Mention your Python version and OS

### Running Tests

```bash
pip install pytest
python -m pytest
```

All tests must pass before submitting a PR.

### Code Style

- Follow PEP 8
- Use type hints where practical
- Keep functions short and focused
- Add docstrings for public functions

### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests: `python -m pytest`
5. Commit: `git commit -m "Add my feature"`
6. Push: `git push origin feature/my-feature`
7. Open a Pull Request

### Adding New Features

- For new analyzers: extend `analyzer.py` or add a new module
- For new exporters: add to `exporters.py`
- For new visual metaphors: add to `prompts.py`
- Always add corresponding tests

### Documentation

- Update README.md if adding user-facing features
- Add docstrings to new public functions
- Update docs/ if needed
