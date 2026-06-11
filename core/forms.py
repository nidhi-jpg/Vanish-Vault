from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import User, MissingPerson, FoundPerson
from .security import PasswordValidator, LoginAttemptMonitor, validate_email_domain


class CustomUserCreationForm(UserCreationForm):
    """Enhanced user registration form with role selection"""
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
    )
    
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number (Optional)'
        })
    )
    
    role = forms.ChoiceField(
        choices=User.Roles.choices,
        initial=User.Roles.CITIZEN,
        widget=forms.RadioSelect(attrs={
            'class': 'role-selector'
        })
    )
    
    organization = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Organization Name (Required for Police/NGO/Volunteer)'
        })
    )
    
    id_document = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        }),
        help_text='Upload ID document (Required for Police/NGO roles)'
    )
    
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 
                 'role', 'organization', 'id_document', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to default fields
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })
        # Disallow 'admin' role selection in public registration
        self.fields['role'].choices = [
            (value, label) for value, label in self.fields['role'].choices if value != User.Roles.ADMIN
        ]

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Check for username patterns that might be problematic
        if len(username) < 3:
            raise forms.ValidationError('Username must be at least 3 characters long.')
        
        # Check for suspicious patterns
        suspicious_patterns = ['admin', 'root', 'system', 'test']
        if any(pattern in username.lower() for pattern in suspicious_patterns):
            raise forms.ValidationError('Username contains reserved words. Please choose a different username.')
        
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Validate email domain if restrictions exist
        try:
            validate_email_domain(email)
        except ValidationError as e:
            raise forms.ValidationError(str(e))
        
        # Check if email already exists (case-insensitive)
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email address already exists.')
        
        return email
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        # Use enhanced password validation
        try:
            PasswordValidator.validate_password(password)
        except ValidationError as e:
            raise forms.ValidationError(list(e.messages))
        
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        organization = cleaned_data.get('organization')
        id_document = cleaned_data.get('id_document')
        
        # Block admin role even if tampered in client
        if role == User.Roles.ADMIN:
            raise forms.ValidationError("Admin accounts cannot be created via public registration.")
        
        # Validate organization for specific roles
        if role in [User.Roles.POLICE, User.Roles.NGO, User.Roles.VOLUNTEER]:
            if not organization:
                raise forms.ValidationError(
                    f"Organization name is required for {role} role."
                )
            
            # Validate organization name format
            if len(organization.strip()) < 2:
                raise forms.ValidationError("Please provide a valid organization name.")
        
        # Validate ID document for police and NGO roles
        if role in [User.Roles.POLICE, User.Roles.NGO]:
            if not id_document:
                raise forms.ValidationError(
                    f"ID document is required for {role} role."
                )
            
            # Validate file size (max 5MB)
            if id_document.size > 5 * 1024 * 1024:
                raise forms.ValidationError("ID document file size must be less than 5MB.")
            
            # Validate file type
            allowed_types = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']
            if id_document.content_type not in allowed_types:
                raise forms.ValidationError("ID document must be a PDF or image file (JPG/PNG).")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.phone_number = self.cleaned_data['phone_number']
        user.role = self.cleaned_data['role']
        user.organization = self.cleaned_data['organization']
        user.id_document = self.cleaned_data['id_document']
        # IMPORTANT: set hashed password (UserCreationForm does this only when commit=True in super().save)
        user.set_password(self.cleaned_data['password1'])
        
        # Set verification status based on role
        if user.role == User.Roles.CITIZEN:
            user.is_verified = True  # Citizens are auto-verified
        else:
            user.is_verified = False  # Other roles need admin verification
            
        if commit:
            user.save()
        return user


class CustomAuthenticationForm(AuthenticationForm):
    """Enhanced login form with security features"""
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username or Email',
            'autocomplete': 'username'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password',
            'autocomplete': 'current-password'
        })
    
    def clean_username(self):
        """Validate username and check for lockout."""
        username = self.cleaned_data.get('username')
        
        # Check if account is locked out
        if LoginAttemptMonitor.is_locked_out(username):
            raise forms.ValidationError(
                "Account has been temporarily locked due to too many failed login attempts. "
                "Please try again in 30 minutes."
            )
        
        return username
    
    def clean(self):
        """Enhanced authentication with security checks."""
        from .security import check_suspicious_activity
        
        # Check for suspicious activity
        if self.request and check_suspicious_activity(self.request):
            raise forms.ValidationError(
                "Suspicious activity detected. Please wait before trying again."
            )
        
        # Support login via email or username
        username_input = self.data.get('username') or ''
        if '@' in username_input:
            try:
                user = User.objects.filter(email__iexact=username_input).first()
                if user:
                    # Replace the username field with the actual username
                    mutable = self.data._mutable if hasattr(self.data, '_mutable') else None
                    try:
                        if hasattr(self.data, '_mutable'):
                            self.data._mutable = True
                        self.data = self.data.copy()
                        self.data['username'] = user.get_username()
                    finally:
                        if mutable is not None:
                            self.data._mutable = mutable
            except Exception:
                # Fall back to default behavior if lookup fails
                pass
        
        # Call parent clean method
        super().clean()
        
        # Additional validation after authentication
        if self.user_cache and not self.user_cache.is_active:
            raise forms.ValidationError(
                "This account has been deactivated. Please contact support."
            )
        
        return self.cleaned_data


class ReportMissingForm(forms.ModelForm):
    """Multi-step form for reporting missing persons"""
    
    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age and (age < 0 or age > 120):
            raise forms.ValidationError('Age must be between 0 and 120.')
        return age
    
    def clean_last_seen_date(self):
        date = self.cleaned_data.get('last_seen_date')
        if date and date > timezone.now().date():
            raise forms.ValidationError('Last seen date cannot be in the future.')
        return date
    
    def clean(self):
        cleaned_data = super().clean()
        last_seen_date = cleaned_data.get('last_seen_date')
        last_seen_time = cleaned_data.get('last_seen_time')
        
        # If date is provided but time is not, that's okay
        # If time is provided but date is not, that's an error
        if last_seen_time and not last_seen_date:
            raise forms.ValidationError('Please provide the date when the person was last seen.')
        
        return cleaned_data
    
    class Meta:
        model = MissingPerson
        fields = [
            'full_name', 'age', 'gender', 'height', 'weight',
            'hair_color', 'eye_color', 'distinguishing_features',
            'last_seen_location', 'last_seen_date', 'last_seen_time',
            'description', 'photo', 'reporter_relationship', 'reporter_phone'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full name of missing person'
            }),
            'age': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0, 'max': 120
            }),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'height': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 5\'8", 175cm'
            }),
            'weight': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 150 lbs, 68kg'
            }),
            'hair_color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Hair color'
            }),
            'eye_color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Eye color'
            }),
            'distinguishing_features': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Scars, tattoos, birthmarks, etc.'
            }),
            'last_seen_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last known location'
            }),
            'last_seen_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'last_seen_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Additional details about the disappearance'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'reporter_relationship': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your relationship to missing person'
            }),
            'reporter_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your contact phone number'
            }),
        }


class ReportFoundForm(forms.ModelForm):
    """Form for reporting found/unidentified persons"""
    
    class Meta:
        model = FoundPerson
        fields = [
            'possible_name', 'estimated_age', 'gender', 'height', 'weight',
            'hair_color', 'eye_color', 'distinguishing_features',
            'found_location', 'found_date', 'found_time', 'notes',
            'photo', 'found_by_organization', 'contact_person', 'contact_phone'
        ]
        widgets = {
            'possible_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Name if known (leave blank if unidentified)'
            }),
            'estimated_age': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0, 'max': 120
            }),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'height': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 5\'8", 175cm'
            }),
            'weight': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 150 lbs, 68kg'
            }),
            'hair_color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Hair color'
            }),
            'eye_color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Eye color'
            }),
            'distinguishing_features': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Scars, tattoos, birthmarks, etc.'
            }),
            'found_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Location where person was found'
            }),
            'found_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'found_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Additional notes about the found person'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'found_by_organization': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Hospital, NGO, or organization name'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contact person name'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contact phone number'
            }),
        }
