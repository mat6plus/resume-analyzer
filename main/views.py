from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.http import JsonResponse
from collections import Counter
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import JobPosting, Resume, Analysis, UserProfile
from .forms import JobPostingForm, ResumeForm, UserRegisterForm
from .tasks import crawl_job_posting_task, analyze_resume_job_task
from django.core.cache import cache
import json
import logging
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

nltk.data.path.append(settings.NLTK_DATA)
nltk.download("punkt")
nltk.download("stopwords")


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
            return JsonResponse({
                'status': 'success',
                'job_posting_id': job_posting.id,
                'analysis_id': analysis.id
            })
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors})
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
            return redirect("main:analysis", job_posting_id=job_posting.id, resume_id=resume.id)
    else:
        form = ResumeForm()
    return render(request, "main/resume_upload.html", {"form": form, "job_posting": job_posting})


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
@require_POST
def stop_analysis(request, analysis_id):
    analysis = get_object_or_404(Analysis, id=analysis_id, user=request.user)
    if analysis.status == 'in_progress':
        analysis.status = 'stopped'
        analysis.save()
        return JsonResponse({"status": "stopped"})
    return JsonResponse({"status": "not_in_progress"}, status=400)

@login_required
def get_analysis_status(request, analysis_id):
    analysis = get_object_or_404(Analysis, id=analysis_id, user=request.user)
    return JsonResponse({
        "status": analysis.status,
        "progress": analysis.progress,
        "match_percentage": analysis.match_percentage,
        "suggestions": analysis.suggestions
    })

@login_required
def get_analysis_results(request, job_posting_id, resume_id):
    job_posting = get_object_or_404(JobPosting, id=job_posting_id, user=request.user)
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    analysis, created = Analysis.objects.get_or_create(
        user=request.user,
        job_posting=job_posting,
        resume=resume,
        defaults={'status': 'pending'}
    )
    
    # Calculate match percentage
    match_percentage = calculate_match_percentage(job_posting, resume)
    
    # Generate suggestions
    suggestions = generate_suggestions(job_posting, resume)
    
    return render(request, "main/analysis_results.html", {
        "job_posting": job_posting,
        "resume": resume,
        "analysis": analysis,
        "match_percentage": match_percentage,
        "suggestions": suggestions
    })

def calculate_match_percentage(job_posting, resume):
    # Tokenize job posting and resume text
    job_description_tokens = word_tokenize(job_posting.description.lower())
    resume_content_tokens = word_tokenize(resume.content.lower())
    
    # Remove stop words
    stop_words = set(stopwords.words('english'))
    job_description_tokens = [word for word in job_description_tokens if word.isalnum() and word not in stop_words]
    resume_content_tokens = [word for word in resume_content_tokens if word.isalnum() and word not in stop_words]
    
    # Count occurrences of words
    job_counter = Counter(job_description_tokens)
    resume_counter = Counter(resume_content_tokens)
    
    # Calculate total keywords in job description
    total_keywords = len(job_counter)
    
    # Calculate matched keywords
    matched_keywords = sum((resume_counter[word] for word in job_counter))
    
    # Calculate match percentage
    if total_keywords == 0:
        return 0  # Avoid division by zero
    match_percentage = (matched_keywords / total_keywords) * 100
    return round(match_percentage, 2)

def generate_suggestions(job_posting, resume):
    # Tokenize job posting and resume text
    job_description_tokens = word_tokenize(job_posting.description.lower())
    resume_content_tokens = word_tokenize(resume.content.lower())
    
    # Remove stop words
    stop_words = set(stopwords.words('english'))
    job_description_tokens = [word for word in job_description_tokens if word.isalnum() and word not in stop_words]
    resume_content_tokens = [word for word in resume_content_tokens if word.isalnum() and word not in stop_words]
    
    # Identify missing keywords
    job_keywords_set = set(job_description_tokens)
    resume_keywords_set = set(resume_content_tokens)
    
    missing_keywords = job_keywords_set - resume_keywords_set
    
    # Generate suggestions based on missing keywords
    suggestions = []
    if missing_keywords:
        suggestions.append("Consider adding the following keywords to your resume: " + ", ".join(missing_keywords))
    
    # Example suggestions based on common areas for improvement
    if len(resume_content_tokens) < 300:
        suggestions.append("Your resume could benefit from additional content or details.")
    
    if "lead" not in resume_content_tokens:
        suggestions.append("Highlight any leadership experiences if applicable.")

    return suggestions



@login_required
def user_profile(request):
    analyses = Analysis.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "main/user_profile.html", {"analyses": analyses})


@login_required
@csrf_exempt
@require_POST
def crawl_progress(request, job_posting_id):
    job_posting = get_object_or_404(JobPosting, id=job_posting_id, user=request.user)
    return JsonResponse({"progress": job_posting.crawl_progress})


def email_confirmation_sent_view(request):
    return render(request, 'account/email_confirmation_sent.html', {
        'signup_url': '/register/',
        'login_url': '/login/',
    })

