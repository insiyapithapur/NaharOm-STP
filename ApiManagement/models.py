from django.db import models


class ApiStatus(models.Model):
    api_name = models.CharField(max_length=255, unique=True)
    is_enabled = models.BooleanField(default=True)
    api_provider = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    alternate_api = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alternates",
    )

    def __str__(self):
        return self.api_name
