from celery import shared_task
from celery.exceptions import MaxRetriesExceededError, Retry
from django.core.exceptions import ObjectDoesNotExist
from .utils import calculate_match_percentage, generate_suggestions, extract_text_from_resume
from .models import JobPosting, Resume, Analysis
from transformers import pipeline
import time
import requests
import logging


logger = logging.getLogger(__name__)

def update_progress(analysis, progress):
    analysis.progress = progress
    analysis.save()

def check_if_stopped(analysis):
    analysis.refresh_from_db()
    return analysis.status == 'stopped'

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_resume_job_task(self, analysis_id):
    try:
        analysis = Analysis.objects.get(id=analysis_id)
        analysis.status = 'in_progress'
        update_progress(analysis, 10)

        job_posting = analysis.job_posting
        resume = analysis.resume

        if check_if_stopped(analysis):
            analysis.status = 'stopped'
            analysis.save()
            return

        job_description = job_posting.job_description
        resume_text = extract_text_from_resume(resume.file)

        if not job_description.strip() or not resume_text.strip():
            raise ValueError("Job description or resume text is empty after extraction")

        update_progress(analysis, 50)

        if check_if_stopped(analysis):
            analysis.status = 'stopped'
            analysis.save()
            return

        # Calculate match percentage
        match_percentage = calculate_match_percentage(job_description, resume_text)

        # Generate suggestions
        suggestions = generate_suggestions(job_description, resume_text)

        if check_if_stopped(analysis):
            analysis.status = 'stopped'
            analysis.save()
            return

        analysis.match_percentage = match_percentage
        analysis.suggestions = '\n'.join(suggestions) if suggestions else "No suggestions available."
        analysis.status = 'completed'
        update_progress(analysis, 100)

        # Generate cover letter
        generate_cover_letter_task.delay(analysis.id)

        # Suggest resume rewrite if necessary
        suggest_resume_rewrite_task.delay(analysis.id)

        logger.info(f"Analysis completed for analysis_id: {analysis_id}")

    except ObjectDoesNotExist:
        logger.error(f"Analysis object not found for id: {analysis_id}")
    except ValueError as e:
        logger.error(f"Error in analysis for {analysis_id}: {str(e)}")
        analysis.status = 'failed'
        analysis.suggestions = f"Error in analysis: {str(e)}"
        analysis.save()
    except Exception as e:
        logger.error(f"Error analyzing resume {analysis_id}: {str(e)}")
        logger.exception("Full traceback:")
        analysis.status = 'failed'
        analysis.suggestions = f"Error analyzing resume: {str(e)}"
        analysis.save()

@shared_task
def generate_cover_letter_task(analysis_id):
    try:
        analysis = Analysis.objects.get(id=analysis_id)
        job_description = analysis.job_posting.job_description
        resume_text = extract_text_from_resume(analysis.resume.file)
        
        generator = pipeline('text-generation', model='gpt2')
        prompt = f"Write a cover letter for the following job description:\n\n{job_description}\n\nBased on the following resume:\n\n{resume_text}\n\nCover letter:"
        
        cover_letter = generator(prompt, max_length=500, num_return_sequences=1)[0]['generated_text']
        
        analysis.cover_letter = cover_letter
        analysis.save()
        
        logger.info(f"Cover letter generated for analysis_id: {analysis_id}")
    except Exception as e:
        logger.error(f"Error generating cover letter for analysis {analysis_id}: {str(e)}")

@shared_task
def suggest_resume_rewrite_task(analysis_id):
    try:
        analysis = Analysis.objects.get(id=analysis_id)
        match_percentage = analysis.match_percentage
        
        if match_percentage < 50:
            rewrite_suggestion = "Your resume might benefit from a rewrite. Consider using an AI-powered resume writing service to improve your match percentage."
        elif match_percentage < 70:
            rewrite_suggestion = "While your resume shows some alignment with the job description, there may be room for improvement. Consider tailoring your resume more specifically to this job."
        else:
            rewrite_suggestion = "Your resume appears to be well-aligned with the job description. Keep up the good work!"
        
        analysis.rewrite_suggestion = rewrite_suggestion
        analysis.save()
        
        logger.info(f"Resume rewrite suggestion generated for analysis_id: {analysis_id}")
    except Exception as e:
        logger.error(f"Error generating resume rewrite suggestion for analysis {analysis_id}: {str(e)}")

# @shared_task
# def retry_failed_job_postings():
#     failed_postings = JobPosting.objects.filter(status='failed')
#     for posting in failed_postings:
#         crawl_job_posting_task.delay(posting.id)