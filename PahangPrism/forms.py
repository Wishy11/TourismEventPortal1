from django import forms
from .models import User

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['full_name', 'email']

