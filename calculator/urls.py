from django.urls import path
from . import views
from . import htmx_views

app_name = 'calculator'

urlpatterns = [
    # Main calculator pages
    path('', views.retirement_calculator, name='retirement_calculator'),
    path('multi-phase/', views.multi_phase_calculator, name='multi_phase_calculator'),

    # Original simple calculator HTMX endpoint (backwards compatibility)
    path('calculate/', htmx_views.calculate_htmx, name='calculate_htmx'),

    # Multi-phase calculator HTMX endpoints
    path('calculate/accumulation/', htmx_views.calculate_accumulation, name='calculate_accumulation'),
    path('calculate/phased-retirement/', htmx_views.calculate_phased_retirement, name='calculate_phased_retirement'),
    path('calculate/active-retirement/', htmx_views.calculate_active_retirement, name='calculate_active_retirement'),
    path('calculate/late-retirement/', htmx_views.calculate_late_retirement, name='calculate_late_retirement'),

    # Scenario CRUD endpoints (RESTful)
    path('scenarios/', views.ScenarioListView.as_view(), name='scenario_list'),
    path('scenarios/new/', views.ScenarioCreateView.as_view(), name='scenario_create'),
    path('scenarios/<int:pk>/edit/', views.ScenarioUpdateView.as_view(), name='scenario_update'),
    path('scenarios/<int:pk>/delete/', views.ScenarioDeleteView.as_view(), name='scenario_delete'),
]
