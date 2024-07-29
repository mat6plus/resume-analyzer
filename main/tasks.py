from celery import shared_task
from .models import JobPosting, Resume, Analysis
from bs4 import BeautifulSoup
import requests
import logging
import chardet
import PyPDF2
import docx2txt
import logging
import os
from .utils import calculate_match_percentage, extract_keywords, generate_suggestions, extract_text_from_resume

logger = logging.getLogger(__name__)

@shared_task
def crawl_job_posting_task(job_posting_id):
    job_posting = JobPosting.objects.get(id=job_posting_id)
    job_posting.status = 'crawling'
    job_posting.save()

    try:
        response = requests.get(job_posting.url, timeout=10)
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response content: {response.text[:500]}...")  # Log first 500 chars

        soup = BeautifulSoup(response.content, "html.parser")

        job_description = soup.find("div", class_="job-description")
        if not job_description:
            job_description = soup.find("p", class_="job-description") or soup.find("section", id="job-details")

        if job_description:
            job_posting.content = job_description.get_text()
            logger.info(f"Extracted job description: {job_posting.content[:500]}...")  # Log first 500 chars
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
        logger.exception("Full traceback:")
        job_posting.save()


def extract_text_from_resume(file):
    file_extension = os.path.splitext(file.name)[1].lower()

    try:
        if file_extension == '.pdf':
            return extract_text_from_pdf(file)
        elif file_extension in ['.doc', '.docx']:
            return extract_text_from_docx(file)
        elif file_extension in ['.txt', '.rtf']:
            return extract_text_from_text(file)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    except Exception as e:
        logger.error(f"Error extracting text from resume: {str(e)}")
        raise

def extract_text_from_pdf(file):
    try:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise

def extract_text_from_docx(file):
    try:
        text = docx2txt.process(file)
        return text
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {str(e)}")
        raise

def extract_text_from_text(file):
    try:
        raw_data = file.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        return raw_data.decode(encoding)
    except Exception as e:
        logger.error(f"Error extracting text from text file: {str(e)}")
        raise


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def analyze_resume_job_task(self, analysis_id):
    try:
        analysis = Analysis.objects.get(id=analysis_id)
        analysis.status = 'in_progress'
        analysis.save()

        job_posting = analysis.job_posting
        resume = analysis.resume

        # Check if job posting content is available
        if not job_posting.content:
            logger.info(f"Job posting content not available for analysis_id: {analysis_id}. Retrying...")
            raise Retry()

        job_description = job_posting.content
        resume_text = extract_text_from_resume(resume.file)

        if not job_description.strip() or not resume_text.strip():
            raise ValueError("Job description or resume text is empty after extraction.")

        # Calculate match percentage
        match_percentage = calculate_match_percentage(job_description, resume_text)

        # Generate suggestions
        suggestions = generate_suggestions(job_description, resume_text)

        analysis.match_percentage = match_percentage
        analysis.suggestions = '\n'.join(suggestions) if suggestions else "No suggestions available."
        analysis.status = 'completed'
        analysis.save()

        logger.info(f"Analysis completed for analysis_id: {analysis_id}")
        logger.info(f"Match percentage: {match_percentage}")
        logger.info(f"Suggestions: {suggestions}")

    except Retry as e:
        raise self.retry(exc=e)
    except ObjectDoesNotExist:
        logger.error(f"Analysis object not found for id: {analysis_id}")
        return
    except Exception as e:
        analysis.status = 'failed'
        error_message = f"Error analyzing resume {analysis_id}: {str(e)}"
        logger.error(error_message)
        logger.exception("Full traceback:")
        analysis.suggestions = error_message
        analysis.save()