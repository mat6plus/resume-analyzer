from django.urls import path
from . import views

app_name = "main"

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("job-posting-input/", views.job_posting_input, name="job_posting_input"),
    path(
        "resume-upload/<int:job_posting_id>/", views.resume_upload, name="resume_upload"
    ),
    path(
        "analysis/<int:job_posting_id>/<int:resume_id>/",
        views.analysis,
        name="analysis",
    ),
    path(
        "get-analysis-status/<int:analysis_id>/",
        views.get_analysis_status,
        name="get_analysis_status",
    ),
    path(
        "analysis-results/<int:analysis_id>/",
        views.analysis_results,
        name="analysis_results",
    ),
    path("cover_letter/<int:analysis_id>/", views.cover_letter, name="cover_letter"),
    path("user-profile/", views.user_profile, name="user_profile"),
    path("update-profile/", views.update_profile, name="update_profile"),
    path("start-analysis/", views.start_analysis, name="start_analysis"),
    path("stop-analysis/<int:analysis_id>/", views.stop_analysis, name="stop_analysis"),
    path("clear-history/", views.clear_history, name="clear_history"),
    path(
        "email-confirmation-sent/",
        views.email_confirmation_sent_view,
        name="email_confirmation_sent",
    ),
]
