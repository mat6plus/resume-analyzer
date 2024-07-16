from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import JobPosting, Resume


class JobPostingForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = ["url", "title", "company", "content"]
        widgets = {
            "url": forms.URLInput(
                attrs={"class": "w-full px-3 py-2 border rounded-md"}
            ),
            "title": forms.TextInput(
                attrs={"class": "w-full px-3 py-2 border rounded-md"}
            ),
            "company": forms.TextInput(
                attrs={"class": "w-full px-3 py-2 border rounded-md"}
            ),
            "content": forms.Textarea(
                attrs={"class": "w-full px-3 py-2 border rounded-md", "rows": 5}
            ),
        }


class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ["file"]
        widgets = {
            "file": forms.FileInput(
                attrs={"class": "w-full px-3 py-2 border rounded-md"}
            ),
        }


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
