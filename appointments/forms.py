from django import forms
from django.utils import timezone

from appointments.models import Appointment
from doctors.models import DoctorProfile


class AppointmentBookingForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['doctor', 'date', 'time', 'reason']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Describe your symptoms or reason for visit...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['doctor'].queryset = DoctorProfile.objects.filter(is_available=True).select_related('user', 'department')
        self.fields['doctor'].widget.attrs.update({'class': 'form-select'})
        self.fields['date'].widget.attrs['min'] = timezone.localdate().isoformat()

    def clean(self):
        cleaned = super().clean()
        doctor = cleaned.get('doctor')
        date = cleaned.get('date')
        time = cleaned.get('time')
        if doctor and date and time:
            conflict = Appointment.objects.filter(
                doctor=doctor,
                date=date,
                time=time,
            ).exclude(status=Appointment.Status.CANCELLED)
            if self.instance.pk:
                conflict = conflict.exclude(pk=self.instance.pk)
            if conflict.exists():
                raise forms.ValidationError('This time slot is already booked. Please choose another time.')
        return cleaned


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['prescription', 'notes']
        widgets = {
            'prescription': forms.Textarea(attrs={
                'rows': 6,
                'class': 'form-control',
                'placeholder': 'Enter medications, dosage, and instructions...',
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Internal notes...',
            }),
        }


class AppointmentStatusForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class TestimonialForm(forms.ModelForm):
    class Meta:
        from appointments.models import Testimonial
        model = Testimonial
        fields = ['name', 'role', 'content', 'rating', 'is_active']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name != 'content':
                field.widget.attrs.update({'class': 'form-control'})
        self.fields['is_active'].widget.attrs.update({'class': 'form-check-input'})
