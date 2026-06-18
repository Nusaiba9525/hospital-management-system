from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from datetime import datetime

from django.utils import timezone
from django.views.generic import CreateView, ListView, TemplateView, UpdateView, View

from accounts.mixins import AdminRequiredMixin, DoctorRequiredMixin, LoginRequiredMixin, PatientRequiredMixin
from appointments.models import Appointment
from appointments.pdf import generate_prescription_pdf
from appointments.utils import get_available_slots
from doctors.models import DoctorProfile

from .forms import AppointmentBookingForm, AppointmentStatusForm, PrescriptionForm


def send_appointment_email(appointment, action):
    subject_map = {
        'booked': 'Appointment Request Received — MedCare Hospital',
        'approved': 'Appointment Approved — MedCare Hospital',
        'rejected': 'Appointment Update — MedCare Hospital',
        'completed': 'Visit Completed — MedCare Hospital',
    }
    body = (
        f'Dear {appointment.patient.get_full_name() or appointment.patient.username},\n\n'
        f'Your appointment with Dr. {appointment.doctor.full_name} on '
        f'{appointment.date.strftime("%B %d, %Y")} at {appointment.time.strftime("%I:%M %p")} '
        f'has been {action}.\n\nStatus: {appointment.get_status_display()}\n\n'
        f'MedCare Hospital'
    )
    if appointment.patient.email:
        send_mail(
            subject_map.get(action, 'Appointment Update'),
            body,
            None,
            [appointment.patient.email],
            fail_silently=True,
        )


class AppointmentBookView(PatientRequiredMixin, CreateView):
    model = Appointment
    form_class = AppointmentBookingForm
    template_name = 'appointments/book.html'
    success_url = reverse_lazy('patients:dashboard')

    def get_initial(self):
        initial = super().get_initial()
        doctor_id = self.request.GET.get('doctor')
        if doctor_id:
            initial['doctor'] = doctor_id
        return initial

    def form_valid(self, form):
        form.instance.patient = self.request.user
        response = super().form_valid(form)
        send_appointment_email(self.object, 'booked')
        messages.success(self.request, 'Appointment booked successfully! Awaiting doctor approval.')
        return response


class AppointmentListView(LoginRequiredMixin, ListView):
    model = Appointment
    template_name = 'appointments/list.html'
    context_object_name = 'appointments'
    paginate_by = 12

    def get_queryset(self):
        user = self.request.user
        qs = Appointment.objects.select_related('patient', 'doctor__user', 'doctor__department')
        if user.is_admin_user:
            pass
        elif user.is_doctor_user:
            qs = qs.filter(doctor__user=user)
        else:
            qs = qs.filter(patient=user)

        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('-date', '-time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['status_choices'] = Appointment.Status.choices
        return context


class AppointmentStatusUpdateView(LoginRequiredMixin, UpdateView):
    model = Appointment
    form_class = AppointmentStatusForm
    template_name = 'appointments/status_form.html'

    def get_queryset(self):
        user = self.request.user
        if user.is_admin_user:
            return Appointment.objects.all()
        if user.is_doctor_user:
            return Appointment.objects.filter(doctor__user=user)
        return Appointment.objects.none()

    def form_valid(self, form):
        response = super().form_valid(form)
        action = form.instance.status
        send_appointment_email(self.object, action)
        messages.success(self.request, f'Appointment marked as {self.object.get_status_display()}.')
        return response

    def get_success_url(self):
        if self.request.user.is_doctor_user:
            return reverse_lazy('doctors:dashboard')
        return reverse_lazy('core:admin_dashboard')


class AppointmentQuickActionView(LoginRequiredMixin, View):
    def post(self, request, pk, action):
        user = request.user
        appointment = get_object_or_404(Appointment, pk=pk)

        if user.is_doctor_user:
            if appointment.doctor.user != user:
                messages.error(request, 'Permission denied.')
                return redirect('doctors:dashboard')
        elif not user.is_admin_user:
            messages.error(request, 'Permission denied.')
            return redirect('core:home')

        status_map = {
            'approve': Appointment.Status.APPROVED,
            'reject': Appointment.Status.REJECTED,
            'complete': Appointment.Status.COMPLETED,
        }
        new_status = status_map.get(action)
        if new_status:
            appointment.status = new_status
            appointment.save()
            send_appointment_email(appointment, new_status)
            messages.success(request, f'Appointment {appointment.get_status_display().lower()}.')

        redirect_url = 'doctors:dashboard' if user.is_doctor_user else 'core:admin_dashboard'
        return redirect(redirect_url)


class PrescriptionUpdateView(DoctorRequiredMixin, UpdateView):
    model = Appointment
    form_class = PrescriptionForm
    template_name = 'appointments/prescription_form.html'

    def get_queryset(self):
        return Appointment.objects.filter(doctor__user=self.request.user)

    def form_valid(self, form):
        form.instance.status = Appointment.Status.COMPLETED
        response = super().form_valid(form)
        send_appointment_email(self.object, 'completed')
        messages.success(self.request, 'Prescription saved and appointment completed.')
        return response

    def get_success_url(self):
        return reverse_lazy('doctors:dashboard')


class PrescriptionPDFView(LoginRequiredMixin, View):
    def get(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        user = request.user
        if not (user.is_admin_user or user == appointment.patient or
                (user.is_doctor_user and appointment.doctor.user == user)):
            messages.error(request, 'Permission denied.')
            return redirect('core:home')

        if not appointment.prescription:
            messages.warning(request, 'No prescription available for this appointment.')
            return redirect('patients:dashboard')

        pdf_buffer = generate_prescription_pdf(appointment)
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="prescription_{pk}.pdf"'
        return response


class AvailableSlotsAPIView(View):
    def get(self, request):
        doctor_id = request.GET.get('doctor_id')
        date_str = request.GET.get('date')
        if not doctor_id or not date_str:
            return JsonResponse({'slots': []})
        try:
            doctor = DoctorProfile.objects.get(pk=doctor_id)
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (DoctorProfile.DoesNotExist, ValueError):
            return JsonResponse({'slots': []})
        slots = get_available_slots(doctor, date)
        return JsonResponse({'slots': slots})
