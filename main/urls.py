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
    path(
        "analysis_results/<int:job_posting_id>/<int:resume_id>/",
        views.analysis_results,
        name="analysis_results",
    ),
    path("user_profile/", views.user_profile, name="user_profile"),
    path("update-profile/", views.update_profile, name="update_profile"),
    path('email-confirmation-sent/', views.email_confirmation_sent_view, name='email_confirmation_sent'),
    path(
        "start_analysis/<int:job_posting_id>/",
        views.start_analysis,
        name="start_analysis",
    ),
    path(
        "stop_analysis/<int:analysis_id>/",
        views.stop_analysis,
        name="stop_analysis",
    ),
]
