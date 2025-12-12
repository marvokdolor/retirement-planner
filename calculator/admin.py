from django.contrib import admin
from .models import Scenario


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    """Custom admin for Scenario model with enhanced features."""

    list_display = ['name', 'created_at', 'updated_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']  # Add date filters
    actions = ['duplicate_scenarios']  # Custom bulk action

    def duplicate_scenarios(self, request, queryset):
        """Duplicate selected scenarios with 'Copy of' prefix."""
        duplicated_count = 0
        for scenario in queryset:
            # Create a copy with modified name
            scenario.pk = None  # This makes save() create a new object
            scenario.name = f"Copy of {scenario.name}"
            scenario.save()
            duplicated_count += 1

        self.message_user(
            request,
            f"Successfully duplicated {duplicated_count} scenario(s)."
        )

    duplicate_scenarios.short_description = "Duplicate selected scenarios"
