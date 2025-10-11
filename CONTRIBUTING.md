# Contributing to Model Fetcher

Thank you for your interest in contributing to Model Fetcher! This document provides guidelines for contributing to the project.

## Branching Workflow

This project uses a structured branching workflow to maintain code quality and ensure proper review processes.

### Branch Structure

- **`main`** - Production-ready code. This branch is protected and deployable at all times.
- **`dev`** - Integration branch for development. All feature branches merge here first.
- **`feature/*`** - Individual feature branches for new functionality.
- **`fix/*`** - Bug fix branches.

### Development Workflow

#### 1. Creating a Feature Branch

Start all new work from the latest `dev` branch:

```bash
# Ensure you have the latest dev branch
git checkout dev
git pull origin dev

# Create a new feature branch
git checkout -b feature/your-feature-name
```

#### 2. Making Changes

- Write clear, concise commit messages
- Follow the existing code style (use `black` and `ruff`)
- Add tests for new functionality
- Update documentation as needed

#### 3. Testing Your Changes

Before submitting a PR, ensure all tests pass:

```bash
# Run tests
pytest

# Format code
black src/

# Lint code
ruff check src/
```

#### 4. Submitting a Pull Request

**Step 1: Merge to `dev` branch**

All feature branches must first be merged to `dev`:

```bash
# Push your feature branch
git push origin feature/your-feature-name

# Create a PR targeting 'dev' branch
gh pr create --base dev --title "Add your feature" --body "Description of changes"
```

**Step 2: From `dev` to `main` (Maintainers Only)**

Once changes are tested and approved in `dev`, a maintainer will create a PR from `dev` to `main`:

```bash
# Only PRs from 'dev' branch are allowed to merge into 'main'
gh pr create --base main --head dev --title "Release: Feature updates"
```

### Why This Workflow?

This branching strategy provides several benefits:

1. **Quality Control** - All changes go through `dev` first, allowing for integration testing
2. **Stable Main Branch** - `main` always contains production-ready code
3. **Clear Review Process** - Changes are reviewed twice: once into `dev`, once into `main`
4. **Easy Rollback** - If issues arise, we can quickly revert `main` to a known good state

### Automated Enforcement

A GitHub Actions workflow automatically validates that PRs to `main` come from the `dev` branch. If you attempt to create a PR directly from a feature branch to `main`, the workflow will fail with instructions.

## Code Style

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Write docstrings for public functions and classes
- Keep functions focused and single-purpose

### Formatting

Use `black` for code formatting:

```bash
black src/
```

### Linting

Use `ruff` for linting:

```bash
ruff check src/
```

## Testing

- Write tests for all new functionality
- Maintain or improve code coverage
- Ensure all tests pass before submitting a PR

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_file.py

# Run with coverage
pytest --cov=src/fetcher
```

## Adding New Providers

To add support for a new AI model provider:

1. Create a new file in `src/fetcher/providers/`
2. Subclass `BaseProvider` from `base.py`
3. Implement the `name` property and `fetch_models()` method
4. Add provider initialization in `src/fetcher/fetcher.py`
5. Optionally add CLI support in `src/fetcher/cli.py`
6. Add tests in `tests/`
7. Update documentation

See the existing providers (OpenRouter, Anthropic, OpenAI, Google) for examples.

## Documentation

- Update `README.md` for user-facing changes
- Update `CLAUDE.md` for development/architectural changes
- Add docstrings to new functions and classes
- Update the `--help` text in CLI commands if needed

## Making the Branch Check Required (Repository Admins)

To enforce the branch validation as a required status check:

1. Go to **Settings** → **Branches**
2. Edit the branch protection rule for `main`
3. Enable **Require status checks to pass before merging**
4. Search for and select **Validate PR Source Branch**
5. Enable **Require branches to be up to date before merging**
6. Save changes

This ensures that the validation workflow must pass before any PR can be merged to `main`.

## Questions or Issues?

If you have questions or run into issues:

- Check existing issues on GitHub
- Review the documentation in `README.md` and `CLAUDE.md`
- Open a new issue with a clear description of the problem
- For security issues, please report privately

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Model Fetcher!
