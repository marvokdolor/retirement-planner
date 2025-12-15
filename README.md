# Retirement Planner

A Django-based multi-phase retirement calculator with user authentication, scenario management, and accessibility features.

🌐 **Live Demo**: [retirement.mkdolor.com](https://retirement.mkdolor.com)

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Future Enhancements](#future-enhancements)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Multi-Phase Planning**: Calculate across 4 retirement phases (accumulation, phased retirement, active retirement, late retirement)
- **User Authentication**: Secure registration and login
- **Scenario Management**: Save, load, compare, and email retirement plans
- **HTMX-Powered**: Dynamic calculations without page reloads
- **Fully Accessible**: ARIA support, keyboard navigation, screen reader friendly
- **Production Ready**: Security headers, caching, error handling

## Quick Start

### Prerequisites

- Python 3.13+
- Node.js 18+ (for Tailwind CSS)

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
# Terminal 1 - Django
python manage.py runserver

# Terminal 2 - Tailwind
python manage.py tailwind start
```

Visit: http://127.0.0.1:8000/

## Tech Stack

- **Backend**: Django 5.1, django-htmx 1.21
- **Frontend**: HTMX 2.0.4, Tailwind CSS v4, Alpine.js 3.x
- **Database**: SQLite (dev), PostgreSQL (production)
- **Deployment**: Railway with Gunicorn

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

```bash
python manage.py test
```

## Future Enhancements

### High Priority
- [ ] User profile edit page
- [ ] Form state persistence
- [ ] Social Security tracking

### Medium Priority
- [ ] Export to PDF/Excel
- [ ] Interactive charts
- [ ] What-if modeling

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
