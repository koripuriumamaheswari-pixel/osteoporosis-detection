from django import forms
from .models import UserRegistrationModel

class UserRegistrationForm(forms.ModelForm):
    name = forms.CharField(
        widget=forms.TextInput(attrs={'pattern': '[A-Za-z ]+',  'title': 'Enter alphabets only'}),
        required=True, max_length=100)
    
    loginid = forms.CharField(
        widget=forms.TextInput(attrs={'pattern': '[a-zA-Z0-9]+', 'title': 'Only alphanumeric characters allowed'}),
        required=True, max_length=100)
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'pattern': '(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}',
            'title': 'Must contain at least one number, one uppercase and lowercase letter, and at least 8 characters'
        }),
        required=True, max_length=100)
    
    mobile = forms.CharField(
        widget=forms.TextInput(attrs={
            'pattern': '[6-9][0-9]{9}',
            'title': 'Enter a valid 10-digit Indian mobile number'
        }),
        required=True, max_length=10)
    
    email = forms.EmailField(required=True, max_length=100)
    
    locality = forms.CharField(required=True, max_length=100)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 4, 'cols': 22}), required=True, max_length=250)
    
    city = forms.CharField(
        widget=forms.TextInput(attrs={
            'pattern': '[A-Za-z ]+',
            'title': 'Enter characters only'
        }),
        required=True, max_length=100)
    
    state = forms.CharField(
        widget=forms.TextInput(attrs={
            'pattern': '[A-Za-z ]+',
            'title': 'Enter characters only'
        }),
        required=True, max_length=100)
    
    status = forms.CharField(widget=forms.HiddenInput(), initial='waiting')

    class Meta:
        model = UserRegistrationModel
        fields = '__all__'
