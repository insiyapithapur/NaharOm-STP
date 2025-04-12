from django.contrib import admin
from .models import ApiStatus


@admin.register(ApiStatus)
class ApiStatusAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "api_name",
        "api_provider",
        "is_enabled",
        "description",
        "alternate_api",
    )
    list_editable = ("is_enabled",)
    search_fields = ("api_name", "api_provider")
    list_filter = ("is_enabled", "api_provider")
