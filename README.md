# Retirement Planner

A Django-based multi-phase retirement calculator with dynamic HTMX updates and modern UI.

## Features

- **Multi-Phase Planning**: Calculate across 4 retirement phases
  - Accumulation (building wealth)
  - Phased Retirement (semi-retirement transition)
  - Active Retirement (early retirement years)
  - Late Retirement (legacy & long-term care)
- **HTMX-Powered**: Dynamic updates without page reloads
- **Modern UI**: Tailwind CSS with smooth animations
- **Responsive Design**: Works on desktop and mobile

## Quick Start

### Prerequisites

- Python 3.13+
- Node.js 18+ (for Tailwind)

### Installation

```bash
# Clone the repository
git clone https://github.com/marvokdolor/retirement-planner.git
cd retirement-planner

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env  # Edit with your SECRET_KEY

# Run migrations
python manage.py migrate

# Install Tailwind dependencies
python manage.py tailwind install
```

### Running the Application

**Terminal 1 - Django:**
```bash
source venv/bin/activate
python manage.py runserver
```

**Terminal 2 - Tailwind (hot reload):**
```bash
source venv/bin/activate
python manage.py tailwind start
```

Visit: http://127.0.0.1:8000/calculator/multi-phase/

## Tech Stack

- **Backend**: Django 6.0, django-htmx
- **Frontend**: HTMX 2.0, Tailwind CSS v4
- **Database**: SQLite (development)

## Project Structure

```
calculator/
├── phase_forms.py          # Forms for 4 phases
├── phase_calculator.py     # Calculation logic
├── htmx_views.py          # HTMX endpoints
└── templates/calculator/
    ├── multi_phase_calculator.html
    └── partials/           # HTMX response fragments
```

## Key Calculations

### Phase 1: Accumulation
- Compound interest with employer matching
- Salary increase adjustments
- Future value projections

### Phase 2: Phased Retirement
- Part-time income tracking
- Withdrawal vs contribution balance
- Portfolio growth during transition

### Phase 3: Active Retirement
- Inflation-adjusted expenses
- Social Security & pension income
- Portfolio sustainability checks

### Phase 4: Late Retirement
- Long-term care cost analysis
- Insurance coverage calculations
- Legacy planning

## Development

### Run Tests
```bash
python manage.py test
```

### Create Superuser (for admin access)
```bash
python manage.py createsuperuser
```

### Collect Static Files (production)
```bash
python manage.py collectstatic
```

## Environment Variables

Create a `.env` file:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Never commit `.env` to version control!**

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is open source and available under the [MIT License](LICENSE).

## Acknowledgments

Built with Django, HTMX, and Tailwind CSS.
