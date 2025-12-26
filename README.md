# Retirement Planner

A Django-based multi-phase retirement calculator with user authentication, scenario management, and accessibility features.

🌐 **Live Demo**: [retirement.mkdolor.com](https://retirement.mkdolor.com)

## Table of Contents

-   [Features](#features)
-   [Quick Start](#quick-start)
-   [Tech Stack](#tech-stack)
-   [Project Structure](#project-structure)
-   [Testing](#testing)
-   [Future Enhancements](#future-enhancements)
-   [Contributing](#contributing)
-   [License](#license)

## Features

-   **Multi-Phase Planning**: Calculate across 4 retirement phases (accumulation, phased retirement, active retirement, late retirement)
-   **User Authentication**: Secure registration, login, and password reset with email fallback
-   **Scenario Management**: Save, load, and compare retirement plans with form state persistence
-   **Monte Carlo Simulations**: 10,000-iteration probabilistic analysis with interactive Plotly charts
-   **HTMX-Powered**: Dynamic calculations without page reloads
-   **Mobile-Responsive**: Adaptive font sizing and layouts from mobile to desktop
-   **Fully Accessible**: ARIA support, keyboard navigation, screen reader friendly
-   **Comprehensive Testing**: 65% test coverage with 59 tests (HTMX views, forms, integration)
-   **Production Ready**: Security headers, email fallback, error handling

## Quick Start

### Prerequisites

-   Python 3.13+
-   Node.js 18+ (for Tailwind CSS)

### Installation

```bash
# Clone and setup
git clone https://github.com/marvokdolor/retirement-planner.git
cd retirement-planner
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env  # Edit with your SECRET_KEY

# Initialize
python manage.py migrate
python manage.py tailwind install
```

### Running Locally

```bash
# Terminal 1 - Django (automatically uses development settings)
python manage.py runserver

# Terminal 2 - Tailwind (only needed in development)
python manage.py tailwind start
```

Visit: http://127.0.0.1:8000/

### Environment-Specific Settings

This project uses separate settings files for different environments:

-   **Development**: `retirement_planner/settings/development.py`

    -   Includes Django Tailwind for CSS development
    -   Debug Toolbar enabled
    -   Browser auto-reload on file changes
    -   More verbose logging
    -   Default when running `manage.py`

-   **Production**: `retirement_planner/settings/production.py`
    -   Tailwind disabled (uses pre-compiled CSS)
    -   Enhanced security (HSTS, secure cookies, XSS protection)
    -   SMTP email backend
    -   Less verbose logging
    -   Used automatically in production (via wsgi.py)

**To explicitly use a specific settings file:**

```bash
# Development
python manage.py runserver --settings=retirement_planner.settings.development

# Production
python manage.py check --settings=retirement_planner.settings.production
```

## Tech Stack

-   **Backend**: Django 5.1, django-htmx 1.21
-   **Frontend**: HTMX 2.0.4, Tailwind CSS v4, Alpine.js 3.x
-   **Database**: SQLite (dev), PostgreSQL (production)
-   **Deployment**: Railway with Gunicorn

## Project Structure

```
calculator/
├── models.py               # Scenario model
├── views.py                # Main views
├── htmx_views.py           # HTMX endpoints
├── forms.py                # Forms & validation
├── phase_forms.py          # Multi-phase forms
├── phase_calculator.py     # Calculation engine
├── tests.py                # Test suite
└── templates/              # HTML templates

templates/
├── base.html               # Base template
├── 404.html, 500.html      # Error pages
└── registration/           # Auth templates
```

## Testing

Run the comprehensive test suite (59 tests, ~65% coverage):

```bash
python manage.py test
```

Test coverage includes:
- HTMX views (19 tests)
- Phase forms validation (27 tests)
- Integration workflows (13 tests)
- Monte Carlo simulations
- PDF generation
- User profiles

## Future Enhancements

### Recently Completed ✅

-   [x] User profile edit page
-   [x] Form state persistence across phase tabs
-   [x] Interactive charts - Monte Carlo simulations with Plotly
-   [x] Mobile-responsive design
-   [x] Password reset with email fallback
-   [x] Comprehensive test suite

### High Priority

-   [ ] What-if scenario modeling
-   [ ] Email scenario reports
-   [ ] Export to Excel

### Medium Priority

-   [ ] PDF export improvements (currently on hold - accuracy fixes needed)
-   [ ] Social Security income tracking
-   [ ] Long Term Care Insurance planning

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

Quick steps: Fork → Create branch → Write tests → Submit PR

## License

GNU General Public License v3.0 - See [LICENSE](LICENSE)

**TL;DR**: Free to use/modify/distribute, but derivatives must remain open source.

## Acknowledgments

Built with [Django](https://www.djangoproject.com/), [HTMX](https://htmx.org/), [Tailwind CSS](https://tailwindcss.com/), and [Claude Code](https://claude.ai/claude-code)

---

**Disclaimer**: Educational tool only. Not financial advice. Consult a qualified advisor.
