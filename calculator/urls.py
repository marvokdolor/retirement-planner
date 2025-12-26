from django.urls import path
from . import views
from . import htmx_views

app_name = 'calculator'

urlpatterns = [
    # Main calculator pages
    path('', views.retirement_calculator, name='retirement_calculator'),
    path('multi-phase/', views.multi_phase_calculator, name='multi_phase_calculator'),
    path('multi-phase/<int:scenario_id>/', views.multi_phase_calculator, name='load_scenario'),
    path('about/', views.about, name='about'),

    # Authentication
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),

    # Original simple calculator HTMX endpoint (backwards compatibility)
    path('calculate/', htmx_views.calculate_htmx, name='calculate_htmx'),

    # Multi-phase calculator HTMX endpoints
    path('calculate/accumulation/', htmx_views.calculate_accumulation, name='calculate_accumulation'),
    path('calculate/phased-retirement/', htmx_views.calculate_phased_retirement, name='calculate_phased_retirement'),
    path('calculate/active-retirement/', htmx_views.calculate_active_retirement, name='calculate_active_retirement'),
    path('calculate/late-retirement/', htmx_views.calculate_late_retirement, name='calculate_late_retirement'),

    # Scenario save HTMX endpoint
    path('scenarios/save/', htmx_views.save_scenario, name='save_scenario'),

    # Monte Carlo simulation HTMX endpoints
    path('monte-carlo/accumulation/', htmx_views.monte_carlo_accumulation, name='monte_carlo_accumulation'),
    path('monte-carlo/withdrawal/', htmx_views.monte_carlo_withdrawal, name='monte_carlo_withdrawal'),

    # Scenario CRUD endpoints (RESTful)
    path('scenarios/', views.ScenarioListView.as_view(), name='scenario_list'),
    path('scenarios/new/', views.ScenarioCreateView.as_view(), name='scenario_create'),
    path('scenarios/<int:pk>/edit/', views.ScenarioUpdateView.as_view(), name='scenario_update'),
    path('scenarios/<int:pk>/delete/', views.ScenarioDeleteView.as_view(), name='scenario_delete'),
    path('scenarios/<int:scenario_id>/email/', views.email_scenario, name='email_scenario'),

    # Scenario comparison
    path('scenarios/compare/', views.compare_scenarios, name='scenario_compare'),

    # What-if scenario analysis
    path('scenarios/<int:scenario_id>/what-if/', views.what_if_comparison, name='what_if_comparison'),
    path('what-if/calculate/', htmx_views.what_if_calculate, name='what_if_calculate'),

    # PDF report generation
    path('scenarios/<int:scenario_id>/pdf/', views.generate_pdf_report, name='generate_pdf_report'),
    path('pdf/current/', views.generate_pdf_from_current, name='generate_pdf_from_current'),
]
