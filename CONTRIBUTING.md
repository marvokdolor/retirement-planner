# Contributing to Retirement Planner

Thank you for your interest in contributing!

## Table of Contents

-   [Code of Conduct](#code-of-conduct)
-   [Getting Started](#getting-started)
-   [Development Workflow](#development-workflow)
-   [Code Style](#code-style)
-   [Testing](#testing)
-   [Pull Request Process](#pull-request-process)
-   [Common Tasks](#common-tasks)
-   [Getting Help](#getting-help)

## Code of Conduct

-   Be respectful and inclusive
-   Welcome newcomers and help them learn
-   Focus on constructive feedback

## Getting Started

### Prerequisites

-   Python 3.13+, Node.js 18+, Git
-   Familiarity with Django, HTMX, Tailwind CSS

### Setup

```bash
# Fork repo, then clone
git clone https://github.com/YOUR-USERNAME/retirement-planner.git
cd retirement-planner
git remote add upstream https://github.com/marvokdolor/retirement-planner.git

# Setup environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your SECRET_KEY
python manage.py migrate
python manage.py tailwind install

# Run servers (separate terminals)
python manage.py runserver
python manage.py tailwind start
```

## Development Workflow

### Test-Driven Development (TDD)

We follow TDD practices for all behavioral changes:

1. **Write a failing test** that defines the desired behavior
2. **Run the test** and confirm it fails (`python manage.py test`)
3. **Write minimal code** to make the test pass
4. **Run the test again** and confirm it passes
5. **Refactor** while keeping tests green
6. **Commit** with a descriptive message

**Exceptions** (write code first, then test):

-   Bug fixes requiring investigation
-   Quick UI/template tweaks
-   Configuration changes

### Branching Strategy

1. **Create a feature branch** from `main`:

    ```bash
    git checkout -b feature/your-feature-name
    # or
    git checkout -b fix/bug-description
    ```

2. **Keep your branch updated:**

    ```bash
    git fetch upstream
    git rebase upstream/main
    ```

3. **Make atomic commits:**
    ```bash
    git add file1.py file2.py
    git commit -m "Add feature X: Brief description"
    ```

### Commit Messages

Follow these guidelines for commit messages:

**Format:**

```
Short summary (50 chars or less)

Longer description if needed explaining:
- What changed
- Why it changed
- Any breaking changes
```

**Examples:**

-   ✅ `Add email scenario feature with SMTP integration`
-   ✅ `Fix accumulation phase validation for edge cases`
-   ✅ `Refactor phase_calculator to use caching decorator`
-   ❌ `Update stuff`
-   ❌ `Fix bug`
-   ❌ `Changes`

### Code Style

**Python:**

-   Follow PEP 8 style guide
-   Use descriptive variable names
-   Add docstrings for functions and classes (PEP 257)
-   Maximum line length: 100 characters
-   Use type hints where helpful

**Django:**

-   Use Django's built-in features (don't reinvent the wheel)
-   Keep views thin, move logic to forms or models
-   Use class-based views for CRUD operations
-   Use function-based views for simple cases

**Templates:**

-   Use Django template inheritance
-   Keep logic minimal in templates
-   Use semantic HTML5 elements
-   Follow accessibility guidelines (ARIA labels, keyboard nav)

**JavaScript:**

-   Minimal JavaScript (rely on HTMX)
-   Use vanilla JS (no jQuery)
-   Comment complex logic
-   Use modern ES6+ syntax

**CSS/Tailwind:**

-   Use Tailwind utility classes
-   Avoid custom CSS unless necessary
-   Group related utilities logically
-   Mobile-first responsive design

## Testing

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test calculator

# Run specific test class
python manage.py test calculator.tests.CalculatorFunctionTests

# Run specific test method
python manage.py test calculator.tests.CalculatorFunctionTests.test_accumulation_basic

# Run with verbose output
python manage.py test --verbosity=2
```

### Writing Tests

Tests should cover:

-   **Calculation accuracy** - Verify mathematical correctness
-   **Form validation** - Test all validation rules
-   **View responses** - Check status codes, templates, context
-   **HTMX behavior** - Verify partial rendering
-   **Edge cases** - Test boundary conditions
-   **Error handling** - Ensure graceful failures

**Test file organization:**

```python
class FeatureNameTests(TestCase):
    """Test FeatureName functionality."""

    def setUp(self):
        """Set up test data."""
        # Common setup code

    def test_specific_behavior(self):
        """Test that specific behavior works correctly."""
        # Arrange
        # Act
        # Assert
```

### Test Coverage

We aim for >80% code coverage. To check coverage:

```bash
# Install coverage (if not already installed)
pip install coverage

# Run tests with coverage
coverage run manage.py test

# View coverage report
coverage report

# Generate HTML report
coverage html
open htmlcov/index.html
```

## Pull Request Process

### Before Submitting

1. **Update your branch:**

    ```bash
    git fetch upstream
    git rebase upstream/main
    ```

2. **Run tests:**

    ```bash
    python manage.py test
    ```

3. **Check for Django issues:**

    ```bash
    python manage.py check --deploy
    ```

4. **Ensure code quality:**
    - No syntax errors
    - No unused imports
    - No commented-out code (unless intentional)
    - All TODO comments are tracked in issues

### Submitting the PR

1. **Push your branch:**

    ```bash
    git push origin feature/your-feature-name
    ```

2. **Create Pull Request** on GitHub with:

    - Clear title describing the change
    - Description explaining:
        - What changed
        - Why it changed
        - How to test it
    - Reference related issues (e.g., "Fixes #123")
    - Screenshots for UI changes

3. **PR Template:**

    ```markdown
    ## Summary

    Brief description of changes

    ## Type of Change

    -   [ ] Bug fix
    -   [ ] New feature
    -   [ ] Breaking change
    -   [ ] Documentation update

    ## Testing

    -   [ ] All tests pass
    -   [ ] Added new tests
    -   [ ] Manual testing completed

    ## Checklist

    -   [ ] Code follows project style guidelines
    -   [ ] Self-review completed
    -   [ ] Comments added for complex logic
    -   [ ] Documentation updated
    -   [ ] No new warnings generated
    ```

### Review Process

-   Maintainers will review your PR
-   Address feedback by pushing new commits
-   Once approved, maintainers will merge
-   Your contribution will be credited in release notes

## Project Structure Guidelines

### When to Create New Files

**Create a new file when:**

-   File exceeds 300 lines
-   Adding a distinct feature domain
-   Clear separation of concerns

**Keep in existing file when:**

-   Logically cohesive functionality
-   Clear section comments exist
-   Easy to navigate

### File Naming Conventions

-   Use descriptive names: `multi_phase_calculator.py` not `calculator2.py`
-   Group related code: `phase_forms.py` for all phase forms
-   Use Django conventions: `views.py`, `models.py`, `forms.py`

### Code Organization

```
calculator/
├── models.py              # Database models
├── views.py               # Standard views (with sections)
├── htmx_views.py          # HTMX-specific views
├── forms.py               # Simple calculator forms
├── phase_forms.py         # Multi-phase forms
├── calculator.py          # Legacy calculator
├── phase_calculator.py    # Multi-phase calculator
├── urls.py                # URL routing
└── tests.py               # All tests (sectioned by feature)
```

## Common Tasks

### Adding a New Feature

1. **Plan the feature:**

    - Define user story
    - Identify required models/views/forms
    - List acceptance criteria

2. **Write tests first (TDD):**

    ```python
    def test_new_feature(self):
        """Test that new feature works correctly."""
        # Test code here
    ```

3. **Implement the feature:**

    - Add model fields if needed
    - Create/update forms
    - Add views
    - Create templates
    - Update URLs

4. **Update documentation:**
    - Add to README if user-facing
    - Update docstrings
    - Add to CHANGELOG

### Fixing a Bug

1. **Write a failing test** that reproduces the bug
2. **Fix the bug** with minimal changes
3. **Verify the test passes**
4. **Check for regressions** (run full test suite)
5. **Document the fix** in commit message

### Adding Tests

1. **Identify untested code:**

    ```bash
    coverage run manage.py test
    coverage report --show-missing
    ```

2. **Write comprehensive tests:**

    - Happy path
    - Edge cases
    - Error conditions

3. **Aim for clarity over cleverness**

## Documentation

### Docstring Style (PEP 257)

```python
def calculate_retirement(data: dict) -> RetirementResults:
    """
    Calculate retirement projections based on input data.

    Args:
        data: Dictionary containing retirement parameters
            - current_age: User's current age
            - retirement_age: Planned retirement age
            - current_savings: Current retirement savings

    Returns:
        RetirementResults object containing:
            - final_portfolio: Projected final balance
            - monthly_income: Sustainable monthly income
            - success_probability: Likelihood of success

    Raises:
        ValidationError: If input data is invalid
        ValueError: If calculations result in negative values

    Example:
        >>> data = {'current_age': 30, 'retirement_age': 65}
        >>> results = calculate_retirement(data)
        >>> print(results.final_portfolio)
        1500000.00
    """
    # Implementation
```

### Inline Comments

-   Comment **why**, not **what**
-   Explain complex algorithms
-   Document workarounds
-   Link to relevant issues/docs

```python
# Use absolute positioning to keep spinner centered during HTMX request
# This prevents layout shift when button text changes
spinner = '<span class="absolute left-1/2">...</span>'
```

## Getting Help

-   **Questions?** Open a GitHub Discussion
-   **Bug found?** Create an Issue with reproduction steps
-   **Feature idea?** Propose in Discussions first
-   **Stuck?** Comment on your PR for guidance

## Recognition

Contributors will be:

-   Listed in release notes
-   Credited in commit messages (Co-Authored-By)
-   Acknowledged in the README
-   Eligible for maintainer status after consistent contributions

## License

By contributing, you agree that your contributions will be licensed under the GNU General Public License v3.0. All contributions must be original work or properly attributed.

---

Thank you for contributing to Retirement Planner! 🎉
