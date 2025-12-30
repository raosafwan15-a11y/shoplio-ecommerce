from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Affiliate


class AffiliateRegistrationForm(UserCreationForm):
    """Form for affiliate registration"""
    full_name = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Full Name'
        })
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Email Address'
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Phone Number (Optional)'
        })
    )
    
    payment_method = forms.ChoiceField(
        choices=[
            ('bank', 'Bank Transfer'),
            ('paypal', 'PayPal'),
            ('easypaisa', 'Easypaisa'),
            ('jazzcash', 'JazzCash'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    payment_details = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-textarea',
            'placeholder': 'Enter your bank account number, PayPal email, or mobile wallet number',
            'rows': 3
        }),
        required=True,
        help_text="Provide your payment details for receiving commissions"
    )
    
    agree_terms = forms.BooleanField(
        required=True,
        label="I agree to the affiliate terms and conditions"
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Username'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Confirm Password'
        })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # Create affiliate profile
            Affiliate.objects.create(
                user=user,
                full_name=self.cleaned_data['full_name'],
                phone=self.cleaned_data.get('phone', ''),
                payment_method=self.cleaned_data['payment_method'],
                payment_details=self.cleaned_data['payment_details']
            )
        
        return user
