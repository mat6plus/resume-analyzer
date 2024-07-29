from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import JobPosting, Resume, Analysis, UserProfile
from .forms import *
from .tasks import *
from .utils import calculate_match_percentage, extract_keywords, generate_suggestions
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
def resume_upload(request, job_posting_id):
    job_posting = get_object_or_404(JobPosting, id=job_posting_id, user=request.user)
    if request.method == "POST":
        form = ResumeForm(request.POST, request.FILES)
        if form.is_valid():
            resume = form.save(commit=False)
            resume.user = request.user
            resume.save()
            return redirect("main:analysis", job_posting_id=job_posting.id, resume_id=resume.id)
    else:
        form = ResumeForm()
    return render(request, "main/resume_upload.html", {"form": form, "job_posting": job_posting})



@login_required
def job_posting_input(request):
    if request.method == "POST":
        form = JobPostingForm(request.POST, request.FILES)
        if form.is_valid():
            job_posting = form.save(commit=False)
            job_posting.user = request.user
            job_posting.save()

            resume = Resume(user=request.user, file=request.FILES['resume'])
            resume.save()

            analysis = Analysis.objects.create(
                user=request.user,
                job_posting=job_posting,
                resume=resume,
                status='pending'
            )

            crawl_job_posting_task.delay(job_posting.id)
            analyze_resume_job_task.delay(analysis.id)
            return JsonResponse({
                'status': 'success',
                'message': 'Analysis has been initiated. Please wait for the results.',
                'job_title': job_posting.title,
                'company': job_posting.company,
                'analysis_id': analysis.id
            })
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors})
    else:
        form = JobPostingForm()
    return render(request, "main/job_posting_input.html", {"form": form})

@login_required
def get_analysis_status(request, analysis_id):
    analysis = Analysis.objects.get(id=analysis_id)
    return JsonResponse({
        "status": analysis.status,
        "progress": analysis.progress,
        "match_percentage": analysis.match_percentage,
        "suggestions": analysis.suggestions
    })

@login_required
def analysis_results(request, analysis_id):
    analysis = get_object_or_404(Analysis, id=analysis_id, user=request.user)
    
    context = {
        'analysis': analysis,
        'job_posting': analysis.job_posting,
        'resume': analysis.resume,
        'match_percentage': analysis.match_percentage,
        'suggestions': analysis.suggestions.split('\n') if analysis.suggestions else [],
        'keywords': analysis.job_posting.keywords[:10],  # Display top 10 keywords
    }

    return render(request, 'main/analysis_results.html', context)

@login_required
def analysis(request, job_posting_id, resume_id):
    job_posting = get_object_or_404(JobPosting, id=job_posting_id, user=request.user)
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    analysis, created = Analysis.objects.get_or_create(
        user=request.user,
        job_posting=job_posting,
        resume=resume,
        defaults={'status': 'pending'}
    )
    if created:
        analyze_resume_job_task.delay(analysis.id)
    return render(request, "main/analysis.html", {
        "job_posting": job_posting,
        "resume": resume,
        "analysis": analysis
    })

@login_required
def user_profile(request):
    analyses = Analysis.objects.filter(user=request.user).select_related('job_posting', 'resume')
    context = {
        'analyses': [
            {
                'job_title': analysis.job_posting.title,
                'company': analysis.job_posting.company,
                'match_percentage': analysis.match_percentage,
                'job_posting_id': analysis.job_posting.id,
                'resume_id': analysis.resume.id,
                'created_at': analysis.created_at,
            }
            for analysis in analyses
        ],
        'user_data': request.user
    }
    return render(request, 'main/user_profile.html', context)

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
    return JsonResponse({
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "bio": profile.bio
    })

@login_required
@csrf_exempt
@require_POST
def start_analysis(request, analysis_id):
    analysis = get_object_or_404(Analysis, id=analysis_id, user=request.user)
    if analysis.status not in ['in_progress', 'completed']:
        analysis.status = 'in_progress'
        analysis.save()
        analyze_resume_job_task.delay(analysis.id)
        return JsonResponse({"status": "started"})
    return JsonResponse({"status": "already_in_progress"}, status=400)

@login_required
@csrf_exempt
@require_POST
def stop_analysis(request, analysis_id):
    analysis = get_object_or_404(Analysis, id=analysis_id, user=request.user)
    if analysis.status == 'in_progress':
        analysis.status = 'stopped'
        analysis.save()
        return JsonResponse({"status": "stopped"})
    return JsonResponse({"status": "not_in_progress"}, status=400)


    
def email_confirmation_sent_view(request):
    return render(request, 'account/email_confirmation_sent.html', {
        'signup_url': '/register/',
        'login_url': '/login/',
    })