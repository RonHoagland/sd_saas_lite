from django import forms
from django.contrib.auth.models import User
from .models import UserProfile

class UserForm(forms.ModelForm):
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    role = forms.ModelChoiceField(
        queryset=None, # Populated in __init__
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Assign a role to this user."
    )
    
    # Password Management
    password = forms.CharField(
        required=False, 
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        help_text="Leave blank to keep current password."
    )
    password_confirm = forms.CharField(
        required=False, 
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'username': 'Required. 150 characters or fewer.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Role
        self.fields['role'].queryset = Role.objects.all()
        
        if self.instance.pk:
            current_role = self.instance.user_roles.first()
            if current_role:
                self.fields['role'].initial = current_role.role
        else:
            self.fields['password'].help_text = "Required for new users (if not generating manually)."
            
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password:
            if password != password_confirm:
                self.add_error('password_confirm', "Passwords do not match.")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        
        if password:
            user.set_password(password)
            
        if commit:
            user.save()
            
        return user

class UserProfileForm(forms.ModelForm):
    birthday = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_left = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    class Meta:
        model = UserProfile
        fields = [
            'display_name', 'time_zone', 'birthday', 'gender', 
            'phone_number', 'position', 'date_left', 'notes'
        ]
        widgets = {
            'display_name': forms.TextInput(attrs={'class': 'form-control'}),
            'time_zone': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
