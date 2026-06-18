from django import forms

from patients.models import PatientProfile


class PatientProfileForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        fields = ['blood_group', 'emergency_contact', 'medical_history', 'allergies']
        widgets = {
            'medical_history': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'allergies': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name not in ('medical_history', 'allergies'):
                field.widget.attrs.update({'class': 'form-control'})
