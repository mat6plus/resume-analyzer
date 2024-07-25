from django.urls import path
from . import views

app_name = "main"

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("job_posting_input/", views.job_posting_input, name="job_posting_input"),
    path(
        "resume_upload/<int:job_posting_id>/", views.resume_upload, name="resume_upload"
    ),
    path(
        "analysis/<int:job_posting_id>/<int:resume_id>/",
        views.analysis,
        name="analysis",
    ),
    path("user_profile/", views.user_profile, name="user_profile"),
    path("update-profile/", views.update_profile, name="update_profile"),
    path(
        "crawl_progress/<int:job_posting_id>/",
        views.crawl_progress,
        name="crawl_progress",
    ),
    path('email-confirmation-sent/', views.email_confirmation_sent_view, name='email_confirmation_sent'),
    path(
        "analysis_progress/<int:job_posting_id>/<int:resume_id>/",
        views.analysis_progress,
        name="analysis_progress",
    ),
    path(
        "get_analysis_results/<int:job_posting_id>/<int:resume_id>/",
        views.get_analysis_results,
        name="get_analysis_results",
    ),
    path("new_analysis/", views.new_analysis, name="new_analysis"),
]
