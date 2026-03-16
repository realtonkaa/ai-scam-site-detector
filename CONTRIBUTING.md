# Contributing to AI Scam Site Detector

Thank you for your interest in contributing. This project aims to help people identify AI-generated spam and scam websites.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/ai-scam-site-detector`
3. Create a virtual environment: `python -m venv venv && source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a new branch: `git checkout -b feature/your-feature-name`

## Development Guidelines

### Code Style
- Follow PEP 8 guidelines
- Use 4 spaces for indentation
- Keep lines under 100 characters
- Add type hints to all function signatures
- Write docstrings for all public functions and classes

### Adding New Detection Signals
When adding a new detection signal, follow this pattern:

1. Add the detection logic to the appropriate analyzer module in `src/`
2. Return a signal dict with these keys:
   - `name`: snake_case identifier
   - `triggered`: bool
   - `confidence`: float between 0.0 and 1.0
   - `detail`: human-readable explanation
3. Write tests covering both triggered and non-triggered cases
4. Update `CATEGORY_WEIGHTS` in `scorer.py` if adding a new category

### Tests
- All new code must have tests
- Aim for meaningful test coverage, not just coverage percentage
- Use the fixtures in `tests/fixtures/` for consistent test data
- Run `make test` before submitting a pull request

### Pull Request Process
1. Ensure all tests pass: `make test`
2. Update the README if you added new features
3. Write a clear PR description explaining what and why
4. Reference any related issues

## Reporting Issues
When reporting bugs, include:
- Python version
- Steps to reproduce
- Expected vs actual behavior
- Sample URL that triggers the issue (if safe to share)

## Code of Conduct
- Be respectful and constructive in all communications
- Focus on the technical merits of contributions
- This tool is for defensive purposes only - do not use it to build better scam sites

## License
By contributing, you agree that your contributions will be licensed under the MIT License.
