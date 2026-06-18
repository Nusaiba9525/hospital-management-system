from django.utils import timezone
from django.views.generic import TemplateView

from accounts.mixins import PatientRequiredMixin
from appointments.models import Appointment


class PatientDashboardView(PatientRequiredMixin, TemplateView):
    template_name = 'patients/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        appointments = Appointment.objects.filter(patient=user).select_related('doctor__user', 'doctor__department')
        today = timezone.localdate()
        context.update({
            'appointments': appointments[:10],
            'upcoming': appointments.filter(
                date__gte=today,
                status__in=[Appointment.Status.PENDING, Appointment.Status.APPROVED],
            )[:5],
            'prescriptions': appointments.exclude(prescription='').exclude(
                status=Appointment.Status.REJECTED
            )[:5],
            'stats': {
                'total': appointments.count(),
                'pending': appointments.filter(status=Appointment.Status.PENDING).count(),
                'approved': appointments.filter(status=Appointment.Status.APPROVED).count(),
            },
        })
        return context
