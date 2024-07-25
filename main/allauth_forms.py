from allauth.account.forms import (
    LoginForm,
    SignupForm,
    ResetPasswordForm,
    ResetPasswordKeyForm,
    ChangePasswordForm,
    SetPasswordForm,
)
from .forms import TailwindTextInput, TailwindEmailInput, TailwindPasswordInput


class CustomLoginForm(LoginForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'login' in self.fields:
            self.fields["login"].widget = TailwindEmailInput()
        if 'password' in self.fields:
            self.fields["password"].widget = TailwindPasswordInput()


class CustomSignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            self.fields["username"].widget = TailwindTextInput()
        if 'email' in self.fields:
            self.fields["email"].widget = TailwindEmailInput()
        if 'password1' in self.fields:
            self.fields["password1"].widget = TailwindPasswordInput()
        if 'password2' in self.fields:
            self.fields["password2"].widget = TailwindPasswordInput()


class CustomResetPasswordForm(ResetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget = TailwindEmailInput()


class CustomResetPasswordKeyForm(ResetPasswordKeyForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget = TailwindPasswordInput()
        self.fields["password2"].widget = TailwindPasswordInput()


class CustomChangePasswordForm(ChangePasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["oldpassword"].widget = TailwindPasswordInput()
        self.fields["password1"].widget = TailwindPasswordInput()
        self.fields["password2"].widget = TailwindPasswordInput()


class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget = TailwindPasswordInput()
        self.fields["password2"].widget = TailwindPasswordInput()
