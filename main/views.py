from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.http import JsonResponse
from django.core.cache import cache
from django.views.decorators.http import require_POST
from .models import JobPosting, Resume, Analysis
from .forms import JobPostingForm, ResumeForm, UserRegisterForm
from bs4 import BeautifulSoup
import requests
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
import docx2txt
import logging
import threading

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
    return render(request, "register.html", {"form": form})


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

            if job_posting.url:
                threading.Thread(
                    target=crawl_job_posting, args=(job_posting.id,)
                ).start()
            else:
                job_posting.keywords = extract_keywords(job_posting.content)
                job_posting.save()

            return redirect("resume_upload", job_posting_id=job_posting.id)
    else:
        form = JobPostingForm()
    return render(request, "main/job_posting_input.html", {"form": form})


@login_required
def resume_upload(request, job_posting_id):
    job_posting = JobPosting.objects.get(id=job_posting_id)
    if request.method == "POST":
        form = ResumeForm(request.POST, request.FILES)
        if form.is_valid():
            resume = form.save(commit=False)
            resume.user = request.user
            resume.save()
            try:
                resume.content = extract_text_from_resume(resume.file)
                resume.save()
                return redirect(
                    "analysis", job_posting_id=job_posting.id, resume_id=resume.id
                )
            except Exception as e:
                logger.error(f"Error extracting text from resume: {str(e)}")
                form.add_error(
                    "file",
                    "Unable to process the resume. Please check the file and try again.",
                )
    else:
        form = ResumeForm()
    return render(
        request, "main/resume_upload.html", {"form": form, "job_posting": job_posting}
    )


@login_required
def analysis(request, job_posting_id, resume_id):
    job_posting = JobPosting.objects.get(id=job_posting_id)
    resume = Resume.objects.get(id=resume_id)

    threading.Thread(
        target=analyze_resume_job, args=(job_posting.id, resume.id)
    ).start()

    return render(
        request,
        "main/analysis_results.html",
        {"job_posting": job_posting, "resume": resume},
    )


@login_required
def user_profile(request):
    analyses = Analysis.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "main/user_profile.html", {"analyses": analyses})


def crawl_job_posting(job_posting_id):
    job_posting = JobPosting.objects.get(id=job_posting_id)
    cache.set(f"crawl_progress_{job_posting_id}", 0, timeout=300)

    try:
        response = requests.get(job_posting.url)
        soup = BeautifulSoup(response.content, "html.parser")

        job_description = soup.find("div", class_="job-description").get_text()
        job_posting.content = job_description
        job_posting.keywords = extract_keywords(job_description)
        job_posting.save()

        cache.set(f"crawl_progress_{job_posting_id}", 100, timeout=300)
    except Exception as e:
        logger.error(f"Error crawling job posting: {str(e)}")
        cache.set(f"crawl_progress_{job_posting_id}", -1, timeout=300)


def extract_keywords(text):
    vectorizer = TfidfVectorizer(stop_words="english", max_features=50)
    tfidf_matrix = vectorizer.fit_transform([text])
    feature_names = vectorizer.get_feature_names_out()

    return [feature_names[i] for i in tfidf_matrix.sum(axis=0).argsort()[0, -20:]]


def extract_text_from_resume(file):
    file_extension = os.path.splitext(file.name)[1].lower()

    if file_extension == ".pdf":
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    elif file_extension in [".doc", ".docx"]:
        text = docx2txt.process(file)
    else:
        raise ValueError("Unsupported file format")

    return text


def analyze_resume_job(job_posting_id, resume_id):
    cache.set(f"analysis_progress_{job_posting_id}_{resume_id}", 0, timeout=300)

    try:
        job_posting = JobPosting.objects.get(id=job_posting_id)
        resume = Resume.objects.get(id=resume_id)

        resume_tokens = word_tokenize(resume.content.lower())
        job_tokens = word_tokenize(" ".join(job_posting.keywords).lower())

        stop_words = set(stopwords.words("english"))
        resume_tokens = [word for word in resume_tokens if word not in stop_words]
        job_tokens = [word for word in job_tokens if word not in stop_words]

        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(
            [" ".join(resume_tokens), " ".join(job_tokens)]
        )
        cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

        missing_keywords = set(job_tokens) - set(resume_tokens)
        suggestions = f"Consider adding the following keywords to your resume: {', '.join(missing_keywords)}"

        analysis = Analysis.objects.create(
            user=resume.user,
            job_posting=job_posting,
            resume=resume,
            match_percentage=cosine_sim * 100,
            suggestions=suggestions,
        )

        cache.set(f"analysis_progress_{job_posting_id}_{resume_id}", 100, timeout=300)
    except Exception as e:
        logger.error(f"Error analyzing resume: {str(e)}")
        cache.set(f"analysis_progress_{job_posting_id}_{resume_id}", -1, timeout=300)


@login_required
@require_POST
def crawl_progress(request, job_posting_id):
    progress = cache.get(f"crawl_progress_{job_posting_id}", 0)
    return JsonResponse({"progress": progress})


@login_required
@require_POST
def analysis_progress(request, job_posting_id, resume_id):
    progress = cache.get(f"analysis_progress_{job_posting_id}_{resume_id}", 0)
    return JsonResponse({"progress": progress})


@login_required
def get_analysis_results(request, job_posting_id, resume_id):
    try:
        analysis = Analysis.objects.get(
            job_posting_id=job_posting_id, resume_id=resume_id
        )
        return JsonResponse(
            {
                "match_percentage": analysis.match_percentage,
                "suggestions": analysis.suggestions,
            }
        )
    except Analysis.DoesNotExist:
        return JsonResponse({"error": "Analysis not found"}, status=404)


@login_required
def new_analysis(request):
    return redirect("job_posting_input")
