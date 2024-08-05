from celery import shared_task
from celery.exceptions import MaxRetriesExceededError, Retry
from django.core.exceptions import ObjectDoesNotExist
from .utils import calculate_match_percentage, generate_suggestions
from .models import Analysis
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_resume_job_task(self, analysis_id):
    try:
        logger.info(f"Starting analysis for analysis_id: {analysis_id}")
        analysis = Analysis.objects.get(id=analysis_id)
        analysis.status = 'in_progress'
        analysis.save()

        job_posting = analysis.job_posting
        resume = analysis.resume

        if not job_posting.job_description.strip() or not resume.content.strip():
            raise ValueError("Job description or resume content is empty")

        # Calculate match percentage
        match_percentage = calculate_match_percentage(job_posting.job_description, resume.content)
        logger.info(f"Match percentage calculated for analysis_id {analysis_id}: {match_percentage}")

        # Generate suggestions
        suggestions = generate_suggestions(job_posting.job_description, resume.content)
        logger.info(f"Suggestions generated for analysis_id {analysis_id}")

        analysis.match_percentage = match_percentage
        analysis.suggestions = '\n'.join(suggestions) if suggestions else "No suggestions available."
        analysis.status = 'completed'
        analysis.progress = 100
        analysis.save()

        logger.info(f"Analysis completed for analysis_id: {analysis_id}")

    except ObjectDoesNotExist:
        logger.error(f"Analysis object not found for id: {analysis_id}")
    except ValueError as e:
        logger.error(f"ValueError in analysis for {analysis_id}: {str(e)}")
        analysis.status = 'failed'
        analysis.suggestions = f"Error in analysis: {str(e)}"
        analysis.save()
    except Exception as e:
        logger.exception(f"Unexpected error in analyze_resume_job_task for analysis_id {analysis_id}")
        try:
            self.retry(exc=e)
        except MaxRetriesExceededError:
            analysis.status = 'failed'
            analysis.suggestions = f"Error analyzing resume: Max retries exceeded"
            analysis.save()