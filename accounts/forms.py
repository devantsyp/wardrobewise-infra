from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

User = get_user_model()

INPUT_CLASSES = (
    'w-full px-3 py-2 border border-accent-400 rounded-lg '
    'focus:outline-none focus:ring-2 focus:ring-primary-700 focus:border-primary-700'
)


class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Email field
        self.fields['email'].widget.attrs.update({
            'class': INPUT_CLASSES,
            'placeholder': 'you@example.com',
            'autofocus': True,
        })

        # Password field
        self.fields['password1'].label = 'Password'
        self.fields['password1'].help_text = None
        self.fields['password1'].widget.attrs.update({
            'class': INPUT_CLASSES,
            'placeholder': 'Create a password',
        })

        # Confirm password field
        self.fields['password2'].label = 'Confirm password'
        self.fields['password2'].help_text = None
        self.fields['password2'].widget.attrs.update({
            'class': INPUT_CLASSES,
            'placeholder': 'Repeat your password',
        })

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Rename username → Email (USERNAME_FIELD is email, so this is fine)
        self.fields['username'].label = 'Email'
        self.fields['username'].widget = forms.EmailInput(attrs={
            'class': INPUT_CLASSES,
            'placeholder': 'you@example.com',
            'autofocus': True,
        })

        self.fields['password'].widget.attrs.update({
            'class': INPUT_CLASSES,
            'placeholder': 'Your password',
        })
