from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

PROFILE_FIELDS = ('first_name', 'last_name', 'username', 'email', 'contact_number', 'location')
class AccountFieldsMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in PROFILE_FIELDS:
            self.fields[name].required = True
    def clean_email(self):
        value = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=value).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return value
    def clean_username(self):
        value = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=value).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This username is already taken.')
        return value

PUBLIC_ROLES = [('', 'Choose Donor or Recipient'), ('DONOR', 'Donor'), ('RECIPIENT', 'Recipient')]

class RoleChoiceForm(forms.Form):
    role = forms.ChoiceField(choices=PUBLIC_ROLES, required=True, label='Account preference',
                            help_text='Donor: share food. Recipient: receive food. Choose one to continue.')

class RegistrationForm(AccountFieldsMixin, UserCreationForm):
    role = forms.ChoiceField(choices=PUBLIC_ROLES, required=True, label='Account preference',
                            help_text='Choose Donor to share food or Recipient to receive food.')
    class Meta(UserCreationForm.Meta):
        model = User
        fields = PROFILE_FIELDS + ('role',)

class ProfileForm(AccountFieldsMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = PROFILE_FIELDS

class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Username or email', max_length=254,
                               widget=forms.TextInput(attrs={'autofocus': True, 'autocomplete': 'username'}))
    error_messages = {'invalid_login': 'Incorrect username/email or password. Please try again.',
                      'inactive': 'This account is inactive.'}
