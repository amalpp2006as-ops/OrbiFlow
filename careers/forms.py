from django import forms
from .models import JobVacancy, JobApplication, Interview


class JobVacancyForm(forms.ModelForm):
    class Meta:
        model = JobVacancy
        fields = [
            'title', 'department', 'description', 'responsibilities',
            'qualifications', 'skills', 'experience', 'employment_type',
            'salary_range', 'location', 'openings', 'deadline', 'is_published'
        ]
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'responsibilities': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'qualifications': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != 'is_published':
                field.widget.attrs.setdefault('class', 'form-control')


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = [
            'full_name', 'email', 'phone', 'education', 'experience',
            'skills', 'linkedin_url', 'portfolio_url', 'cover_letter', 'resume'
        ]
        widgets = {
            'skills': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'cover_letter': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'resume': forms.ClearableFileInput(attrs={'accept': '.pdf', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class ApplicationReviewForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['status', 'private_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'private_notes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }


class InterviewForm(forms.ModelForm):
    class Meta:
        model = Interview
        fields = ['interviewer', 'scheduled_at', 'meeting_link_or_location', 'feedback']
        widgets = {
            'scheduled_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'interviewer': forms.Select(attrs={'class': 'form-select'}),
            'meeting_link_or_location': forms.TextInput(attrs={'class': 'form-control'}),
            'feedback': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }