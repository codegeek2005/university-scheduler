# scheduler/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from scheduler.models import Section, Teacher

class CustomRegistrationForm(UserCreationForm):
    ROLE_CHOICES = (('student', 'Student'), ('faculty', 'Faculty Member'))
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'w-full rounded-lg border-gray-300 p-3'})
    )
    section = forms.ModelChoiceField(
        queryset=Section.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'w-full rounded-lg border-gray-300 p-3'})
    )
    teacher = forms.ModelChoiceField(
        queryset=Teacher.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'w-full rounded-lg border-gray-300 p-3'})
    )

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        
        # Enforce that students must have a section and faculty must have a teacher
        if role == 'student' and not cleaned_data.get("section"):
            self.add_error('section', "Students must select a section.")
        if role == 'faculty' and not cleaned_data.get("teacher"):
            self.add_error('teacher', "Faculty must select their profile.")
        return cleaned_data
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'password1', 'password2')