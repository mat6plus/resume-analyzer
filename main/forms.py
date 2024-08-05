from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import JobPosting, Resume
from django.forms.renderers import TemplatesSetting


class JobPostingForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = ["job_name", "company_name", "job_description"]
        widgets = {
            "job_name": forms.TextInput(
                attrs={"class": "w-full px-3 py-2 border rounded-md"}
            ),
            "company_name": forms.TextInput(
                attrs={"class": "w-full px-3 py-2 border rounded-md"}
            ),
            "job_description": forms.Textarea(
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


class TailwindFormRenderer(TemplatesSetting):
    form_template_name = "forms/form.html"
    formset_template_name = "forms/formset.html"
    field_template_name = "forms/field.html"


class TailwindTextInput(forms.TextInput):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs.update(
            {
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
            }
        )


class TailwindEmailInput(forms.EmailInput):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs.update(
            {
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
            }
        )


class TailwindPasswordInput(forms.PasswordInput):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs.update(
            {
                "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-300 focus:ring focus:ring-indigo-200 focus:ring-opacity-50"
            }
        )
