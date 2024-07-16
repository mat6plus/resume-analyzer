# tests.py

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import JobPosting, Resume, Analysis
from .forms import JobPostingForm, ResumeForm, UserRegisterForm
from django.core.cache import cache
import json


class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.job_posting = JobPosting.objects.create(
            user=self.user,
            url="https://example.com/job",
            title="Software Developer",
            company="Tech Co",
            description="Job description",
            keywords=["python", "django"],
        )
        self.resume = Resume.objects.create(
            user=self.user,
            file=SimpleUploadedFile("resume.pdf", b"file_content"),
            content="Resume content",
        )

    def test_job_posting_creation(self):
        self.assertTrue(isinstance(self.job_posting, JobPosting))
        self.assertEqual(self.job_posting.__str__(), "Software Developer at Tech Co")

    def test_resume_creation(self):
        self.assertTrue(isinstance(self.resume, Resume))
        self.assertEqual(self.resume.__str__(), f"Resume of {self.user.username}")

    def test_analysis_creation(self):
        analysis = Analysis.objects.create(
            user=self.user,
            job_posting=self.job_posting,
            resume=self.resume,
            match_percentage=85.5,
            suggestions="Add more keywords",
        )
        self.assertTrue(isinstance(analysis, Analysis))
        self.assertEqual(
            analysis.__str__(),
            f"Analysis for {self.user.username} - Software Developer",
        )


class FormTests(TestCase):
    def test_job_posting_form_valid(self):
        form_data = {
            "url": "https://example.com/job",
            "title": "Software Developer",
            "company": "Tech Co",
            "content": "Job description",
        }
        form = JobPostingForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_job_posting_form_invalid(self):
        form_data = {
            "url": "invalid-url",
            "title": "",
            "company": "Tech Co",
            "content": "Job description",
        }
        form = JobPostingForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_resume_form_valid(self):
        file = SimpleUploadedFile("resume.pdf", b"file_content")
        form = ResumeForm(files={"file": file})
        self.assertTrue(form.is_valid())

    def test_resume_form_invalid(self):
        form = ResumeForm(files={})
        self.assertFalse(form.is_valid())

    def test_user_register_form_valid(self):
        form_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "testpassword123",
            "password2": "testpassword123",
        }
        form = UserRegisterForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_user_register_form_invalid(self):
        form_data = {
            "username": "newuser",
            "email": "invalid-email",
            "password1": "testpassword123",
            "password2": "differentpassword",
        }
        form = UserRegisterForm(data=form_data)
        self.assertFalse(form.is_valid())


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.job_posting = JobPosting.objects.create(
            user=self.user,
            url="https://example.com/job",
            title="Software Developer",
            company="Tech Co",
            description="Job description",
            keywords=["python", "django"],
        )
        self.resume = Resume.objects.create(
            user=self.user,
            file=SimpleUploadedFile("resume.pdf", b"file_content"),
            content="Resume content",
        )

    def test_home_view(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "main/home.html")

    def test_job_posting_input_view(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get(reverse("job_posting_input"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "main/job_posting_input.html")

    def test_resume_upload_view(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get(reverse("resume_upload", args=[self.job_posting.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "main/resume_upload.html")

    def test_analysis_view(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get(
            reverse("analysis", args=[self.job_posting.id, self.resume.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "main/analysis_results.html")

    def test_user_profile_view(self):
        self.client.login(username="testuser", password="12345")
        response = self.client.get(reverse("user_profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "main/user_profile.html")


class IntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")

    def test_job_posting_workflow(self):
        # Submit job posting
        job_data = {
            "url": "https://example.com/job",
            "title": "Software Developer",
            "company": "Tech Co",
            "content": "Job description",
        }
        response = self.client.post(reverse("job_posting_input"), job_data)
        self.assertEqual(response.status_code, 302)  # Redirect to resume upload

        job_posting = JobPosting.objects.first()
        self.assertIsNotNone(job_posting)

        # Upload resume
        with open("test_resume.pdf", "wb") as f:
            f.write(b"Test resume content")

        with open("test_resume.pdf", "rb") as f:
            resume_data = {"file": f}
            response = self.client.post(
                reverse("resume_upload", args=[job_posting.id]), resume_data
            )

        self.assertEqual(response.status_code, 302)  # Redirect to analysis

        resume = Resume.objects.first()
        self.assertIsNotNone(resume)

        # Check analysis
        response = self.client.get(
            reverse("analysis", args=[job_posting.id, resume.id])
        )
        self.assertEqual(response.status_code, 200)

        # Wait for analysis to complete
        from django.db.models.signals import post_save
        from .models import Analysis

        def on_analysis_save(sender, instance, created, **kwargs):
            if created:
                cache.set(
                    f"analysis_progress_{instance.job_posting.id}_{instance.resume.id}",
                    100,
                    timeout=300,
                )

        post_save.connect(on_analysis_save, sender=Analysis)

        # Check analysis progress
        response = self.client.post(
            reverse("analysis_progress", args=[job_posting.id, resume.id])
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["progress"], 100)

        # Get analysis results
        response = self.client.get(
            reverse("get_analysis_results", args=[job_posting.id, resume.id])
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("match_percentage", data)
        self.assertIn("suggestions", data)


class SecurityTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.other_user = User.objects.create_user(
            username="otheruser", password="67890"
        )

    def test_login_required(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_user_cannot_access_others_data(self):
        self.client.login(username="testuser", password="12345")

        # Create job posting and resume for other user
        job_posting = JobPosting.objects.create(
            user=self.other_user, title="Test Job", company="Test Co"
        )
        resume = Resume.objects.create(
            user=self.other_user, file=SimpleUploadedFile("resume.pdf", b"file_content")
        )

        # Try to access other user's analysis
        response = self.client.get(
            reverse("analysis", args=[job_posting.id, resume.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_csrf_protection(self):
        self.client.login(username="testuser", password="12345")

        # Try to submit form without CSRF token
        response = self.client.post(
            reverse("job_posting_input"), {"title": "Test Job", "company": "Test Co"}
        )
        self.assertEqual(response.status_code, 403)  # CSRF validation failed


class PerformanceTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")

    def test_analysis_caching(self):
        job_posting = JobPosting.objects.create(
            user=self.user, title="Test Job", company="Test Co"
        )
        resume = Resume.objects.create(
            user=self.user, file=SimpleUploadedFile("resume.pdf", b"file_content")
        )

        # First request should take longer
        start_time = time.time()
        response = self.client.get(
            reverse("analysis", args=[job_posting.id, resume.id])
        )
        first_request_time = time.time() - start_time

        # Second request should be faster due to caching
        start_time = time.time()
        response = self.client.get(
            reverse("analysis", args=[job_posting.id, resume.id])
        )
        second_request_time = time.time() - start_time

        self.assertLess(second_request_time, first_request_time)
