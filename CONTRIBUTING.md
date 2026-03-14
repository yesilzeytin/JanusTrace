# Contributing to JanusTrace

First off, thank you for considering contributing to JanusTrace! I would be glad if you'd be interested in contributing.

## Where do I go from here?

If you've noticed a bug or have a request for a pull request, you can open an issue on GitHub. 

## Development Setup

1. **Fork & Clone**: Fork the repository and clone it to your local machine.
2. **Setup Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   pip install -r requirements.txt
   ```
3. **Install Testing Tools**: 
   ```bash
   pip install pytest pytest-cov
   ```

## Testing Protocol

JanusTrace is developed using **Test-Driven Development (TDD)** principles. 
Every bug fix or new feature must be accompanied by an automated test. 

We use `pytest` as our automated test runner. All tests are located in the `/tests` folder.

**Running the test suite:**
```bash
pytest tests/ -v
```

**Running tests with coverage:**
```bash
pytest tests/ --cov=trace_framework -v
```

If you add a new feature, please create a new test file or append to an existing test module. We mandate 100% pass rates on our test suite for all PRs.

## Pull Request Process

1. Ensure all tests pass.
2. Update the `CHANGELOG.md` file with details of changes.
3. Keep your PR scope limited to one specific bug fix or feature.
4. If exposing new APIs, please add clear module-level and function-level docstrings.
