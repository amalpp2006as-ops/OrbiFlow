from django import forms
from .models import ProjectRequest, ProjectRequestAttachment


class ProjectRequestForm(forms.ModelForm):

    class Meta:
        model = ProjectRequest

        fields = [
            'title',
            'category',
            'description',
            'problem_statement',
            'expected_outcome',
            'technologies',
            'priority',
            'estimated_start_date',
            'expected_completion_date',
            'estimated_budget',
            'reason',
            'additional_notes',
        ]

        widgets = {

            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your project title'
            }),

            'category': forms.Select(attrs={
                'class': 'form-select'
            }),

            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe your project requirements in detail'
            }),

            'problem_statement': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'What problem does this project solve?'
            }),

            'expected_outcome': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'What results do you expect?'
            }),

            'technologies': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Example: Python, Django, React'
            }),

            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),

            'estimated_start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),

            'expected_completion_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),

            'estimated_budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter estimated budget',
                'min': '0',
                'step': '0.01'
            }),

            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Why are you requesting this project?'
            }),

            'additional_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any additional information?'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get('estimated_start_date')
        completion_date = cleaned_data.get('expected_completion_date')

        if start_date and completion_date:
            if completion_date < start_date:
                self.add_error(
                    'expected_completion_date',
                    'Completion date cannot be earlier than the start date.'
                )

        budget = cleaned_data.get('estimated_budget')

        if budget is not None and budget < 0:
            self.add_error(
                'estimated_budget',
                'Budget cannot be negative.'
            )

        return cleaned_data
