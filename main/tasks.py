from celery import shared_task
from django.core.cache import cache
from .models import JobPosting, Resume, Analysis
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
import os

logger = logging.getLogger(__name__)

@shared_task
def crawl_job_posting_task(job_posting_id):
    job_posting = JobPosting.objects.get(id=job_posting_id)
    job_posting.status = 'crawling'
    job_posting.save()

    try:
        response = requests.get(job_posting.url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")

        job_description = soup.find("div", class_="job-description")
        if not job_description:
            job_description = soup.find("p", class_="job-description") or soup.find("section", id="job-details")

        if job_description:
            job_posting.content = job_description.get_text()
            job_posting.keywords = extract_keywords(job_posting.content)
            job_posting.status = 'completed'
        else:
            logger.error(f"Job description not found for job posting {job_posting_id}. HTML content: {soup.prettify()}")
            job_posting.status = 'failed'

        job_posting.save()

        analysis = Analysis.objects.filter(job_posting_id=job_posting_id).first()
        if analysis:
            analyze_resume_job_task.delay(analysis.id)

    except Exception as e:
        job_posting.status = 'failed'
        logger.error(f"Error crawling job posting {job_posting_id}: {str(e)}")
        job_posting.save()

@shared_task
def analyze_resume_job_task(analysis_id):
    analysis = Analysis.objects.get(id=analysis_id)
    analysis.status = 'in_progress'
    analysis.save()

    try:
        job_posting = analysis.job_posting
        resume = analysis.resume

        resume_text = extract_text_from_resume(resume.file)
        job_description = job_posting.content

        # Calculate match percentage
        match_percentage = calculate_match_percentage(job_description, resume_text)

        # Generate suggestions
        suggestions = generate_suggestions(job_description, resume_text)

        analysis.match_percentage = match_percentage
        analysis.suggestions = suggestions
        analysis.status = 'completed'
    except Exception as e:
        analysis.status = 'failed'
        logger.error(f"Error analyzing resume {analysis_id}: {str(e)}")

    analysis.save()
    
def calculate_match_percentage(job_description, resume_text):
    job_keywords = set(extract_keywords(job_description))
    resume_keywords = set(extract_keywords(resume_text))
    
    matching_keywords = job_keywords.intersection(resume_keywords)
    match_percentage = (len(matching_keywords) / len(job_keywords)) * 100 if job_keywords else 0
    
    return round(match_percentage, 2)

def generate_suggestions(job_description, resume_text):
    job_keywords = set(extract_keywords(job_description))
    resume_keywords = set(extract_keywords(resume_text))
    
    missing_keywords = job_keywords - resume_keywords
    
    suggestions = []
    if missing_keywords:
        suggestions.append(f"Consider adding the following keywords to your resume: {', '.join(missing_keywords)}")
    
    if len(resume_keywords) < 10:
        suggestions.append("Your resume might benefit from more detailed information about your skills and experiences.")
    
    return suggestions

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