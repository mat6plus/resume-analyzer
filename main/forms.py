# main/forms.py

from django import forms
from .models import JobPosting, Resume

class JobPostingForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = ['url', 'title', 'company']
        widgets = {
            'url': forms.URLInput(attrs={'class': 'w-full px-3 py-2 border rounded-md'}),
            'title': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-md'}),
            'company': forms.TextInput(attrs={'class': 'w-full px-3 py-2 border rounded-md'}),
        }

class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'w-full px-3 py-2 border rounded-md'}),
        }