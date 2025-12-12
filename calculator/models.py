from django.db import models

class Scenario(models.Model):
    """Represents a saved retirement scenario with all phase inputs."""
    name = models.CharField(max_length=200, help_text="Descriptive name for this scenario")
    data = models.JSONField(help_text="All phase inputs stored as JSON")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.name
