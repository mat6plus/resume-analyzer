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
        self.fields["login"].widget = TailwindEmailInput()
        self.fields["password"].widget = TailwindPasswordInput()


class CustomSignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget = TailwindTextInput()
        self.fields["email"].widget = TailwindEmailInput()
        self.fields["password1"].widget = TailwindPasswordInput()
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
