from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models import Avg
from .models import JobPosting, Resume, Analysis, UserProfile
from celery import chain
from transformers import pipeline
import requests
from .forms import *
from .tasks import *
from .utils import *
import logging
import json

logger = logging.getLogger(__name__)


def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = UserRegisterForm()
    return render(request, "main/signup.html", {"form": form})


@login_required
def home(request):
    return render(request, "main/home.html")


@login_required
def job_posting_input(request):
    if request.method == "POST":
        form = JobPostingForm(request.POST)
        if form.is_valid():
            job_posting = form.save(commit=False)
            job_posting.user = request.user
            job_posting.save()
            return redirect("resume_upload", job_posting_id=job_posting.id)
    else:
        form = JobPostingForm()
    return render(request, "main/job_posting_input.html", {"form": form})


@login_required
def resume_upload(request, job_posting_id):
    job_posting = get_object_or_404(JobPosting, id=job_posting_id, user=request.user)
    if request.method == "POST":
        form = ResumeForm(request.POST, request.FILES)
        if form.is_valid():
            resume = form.save(commit=False)
            resume.user = request.user
            resume.save()

            analysis = Analysis.objects.create(
                user=request.user,
                job_posting=job_posting,
                resume=resume,
                status="pending",
            )

            analyze_resume_job_task.delay(analysis.id)
            return redirect("analysis_results", analysis_id=analysis.id)
    else:
        form = ResumeForm()
    return render(
        request, "main/resume_upload.html", {"form": form, "job_posting": job_posting}
    )


@login_required
def analysis(request, job_posting_id, resume_id):
    job_posting = get_object_or_404(JobPosting, id=job_posting_id, user=request.user)
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    analysis, created = Analysis.objects.get_or_create(
        user=request.user,
        job_posting=job_posting,
        resume=resume,
        defaults={"status": "pending"},
    )
    if created:
        analyze_resume_job_task.delay(analysis.id)
    return render(
        request,
        "main/analysis.html",
        {"job_posting": job_posting, "resume": resume, "analysis": analysis},
    )


@login_required
def get_analysis_status(request, analysis_id):
    try:
        analysis = Analysis.objects.get(id=analysis_id, user=request.user)
        return JsonResponse(
            {
                "status": analysis.status,
                "progress": analysis.progress,
                "matchPercentage": analysis.match_percentage,
                "suggestions": (
                    analysis.suggestions.split("\n") if analysis.suggestions else []
                ),
            }
        )
    except Analysis.DoesNotExist:
        print(f"Analysis not found for analysis_id: {analysis_id}")
        return JsonResponse({"error": "Analysis not found"}, status=404)
    except Exception as e:
        print(f"Error in get_analysis_status view: {str(e)}")
        return JsonResponse({"error": "An unexpected error occurred"}, status=500)


@login_required
def analysis_results(request, analysis_id):
    try:
        analysis = get_object_or_404(Analysis, id=analysis_id, user=request.user)
        job_posting = analysis.job_posting
        resume = analysis.resume

        context = {
            "analysis": analysis,
            "job_posting": job_posting,
            "resume": resume,
            "match_percentage": analysis.match_percentage,
            "suggestions": (
                analysis.suggestions.split("\n") if analysis.suggestions else []
            ),
            "cover_letter": analysis.cover_letter,
            "rewrite_suggestion": analysis.rewrite_suggestion,
        }

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(context)
        else:
            return render(request, "main/analysis_results.html", context)

    except Analysis.DoesNotExist:
        # Display a user-friendly message or redirect the user
        return render(request, "main/analysis_not_found.html", status=404)


@login_required
def user_profile(request):
    analyses = (
        Analysis.objects.filter(user=request.user)
        .select_related("job_posting", "resume")
        .order_by("-created_at")
    )

    # Search functionality
    search_query = request.GET.get("search", "")
    if search_query:
        analyses = analyses.filter(
            Q(job_posting__title__icontains=search_query)
            | Q(job_posting__company__icontains=search_query)
        )

    # Filtering
    filter_by = request.GET.get("filter", "")
    if filter_by == "high_match":
        analyses = analyses.filter(match_percentage__gte=75)
    elif filter_by == "low_match":
        analyses = analyses.filter(match_percentage__lt=50)

    total_analyses = analyses.count()
    average_match_percentage = analyses.aggregate(Avg("match_percentage"))[
        "match_percentage__avg"
    ]
    latest_match_percentage = (
        analyses.first().match_percentage if analyses.exists() else None
    )

    paginator = Paginator(analyses, 5)  # Show 5 analyses per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "user_data": {
            "name": f"{request.user.first_name} {request.user.last_name}",
            "email": request.user.email,
            "bio": request.user.profile.bio if hasattr(request.user, "profile") else "",
        },
        "total_analyses": total_analyses,
        "average_match_percentage": average_match_percentage,
        "latest_match_percentage": latest_match_percentage,
        "search_query": search_query,
        "filter_by": filter_by,
    }
    return render(request, "main/user_profile.html", context)


@login_required
@require_POST
def update_profile(request):
    data = json.loads(request.body)
    user = request.user
    user.first_name = data.get("first_name", user.first_name)
    user.last_name = data.get("last_name", user.last_name)
    user.email = data.get("email", user.email)
    profile = user.profile
    profile.bio = data.get("bio", profile.bio)
    user.save()
    profile.save()
    return JsonResponse(
        {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "bio": profile.bio,
        }
    )


@login_required
@csrf_exempt
@require_POST
def start_analysis(request):
    form = JobPostingForm(request.POST, request.FILES)
    if form.is_valid():
        try:
            job_posting = form.save(commit=False)
            job_posting.user = request.user
            job_posting.status = "pending"
            job_posting.save()

            resume = Resume(user=request.user, file=request.FILES["resume"])
            resume.save()

            analysis = Analysis.objects.create(
                user=request.user,
                job_posting=job_posting,
                resume=resume,
                status="pending",
                progress=0,
            )

            # Queue the analysis task
            analyze_resume_job_task.delay(analysis.id)

            return JsonResponse(
                {
                    "status": "success",
                    "message": "Analysis started successfully",
                    "analysis_id": analysis.id,
                    "job_title": job_posting.job_name,
                    "company": job_posting.company_name,
                }
            )
        except Exception as e:
            logger.error(f"Error starting analysis: {str(e)}")
            return JsonResponse(
                {"status": "error", "message": f"An error occurred: {str(e)}"},
                status=500,
            )
    else:
        return JsonResponse(
            {"status": "error", "message": "Invalid form data", "errors": form.errors},
            status=400,
        )


@login_required
@csrf_exempt
@require_POST
def stop_analysis(request, analysis_id):
    try:
        analysis = Analysis.objects.get(id=analysis_id, user=request.user)
        if analysis.status == "in_progress":
            analysis.status = "stopped"
            analysis.save()
            return JsonResponse({"status": "stopped"})
        else:
            return JsonResponse({"status": "not_in_progress"}, status=400)
    except Analysis.DoesNotExist:
        print(f"Analysis not found for analysis_id: {analysis_id}")
        return JsonResponse({"error": "Analysis not found"}, status=404)
    except Exception as e:
        print(f"Error in stop_analysis view: {str(e)}")
        return JsonResponse({"error": "An unexpected error occurred"}, status=500)


def email_confirmation_sent_view(request):
    return render(
        request,
        "account/email_confirmation_sent.html",
        {
            "signup_url": "/register/",
            "login_url": "/login/",
        },
    )


@login_required
def cover_letter(request, analysis_id):
    analysis = get_object_or_404(Analysis, id=analysis_id, user=request.user)
    context = {"cover_letter": analysis.cover_letter}

    if request.headers.get("HX-Request"):
        return render(request, "main/partials/cover_letter.html", context)

    return render(request, "main/cover_letter.html", context)


@login_required
@require_POST
def clear_history(request):
    try:
        Analysis.objects.filter(user=request.user).delete()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})
