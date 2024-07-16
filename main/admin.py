# admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import JobPosting, Resume, Analysis


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "user", "created_at", "url_link")
    list_filter = ("company", "created_at")
    search_fields = ("title", "company", "user__username")
    readonly_fields = ("created_at",)
    fieldsets = (
        (None, {"fields": ("user", "title", "company", "url", "content")}),
        (
            "Advanced options",
            {
                "classes": ("collapse",),
                "fields": ("keywords", "created_at"),
            },
        ),
    )

    def url_link(self, obj):
        return format_html("<a href='{url}' target='_blank'>{url}</a>", url=obj.url)

    url_link.short_description = "URL"


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "updated_at", "file_link")
    list_filter = ("created_at", "updated_at")
    search_fields = ("user__username",)
    readonly_fields = ("created_at", "updated_at")

    def file_link(self, obj):
        return format_html(
            "<a href='{url}' target='_blank'>Download</a>", url=obj.file.url
        )

    file_link.short_description = "Resume File"


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ("user", "job_posting", "resume", "match_percentage", "created_at")
    list_filter = ("created_at", "match_percentage")
    search_fields = ("user__username", "job_posting__title", "job_posting__company")
    readonly_fields = ("created_at",)
    fieldsets = (
        (None, {"fields": ("user", "job_posting", "resume", "match_percentage")}),
        (
            "Suggestions",
            {
                "fields": ("suggestions",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at",),
            },
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("user", "job_posting", "resume")
        )
