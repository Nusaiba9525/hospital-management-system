from django.db.models import Count, Q
from django.utils import timezone
from django.views.generic import ListView, TemplateView

from accounts.mixins import AdminRequiredMixin
from accounts.models import User
from appointments.models import Appointment
from doctors.models import Department, DoctorProfile


class HomeView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        from appointments.models import Testimonial

        context = super().get_context_data(**kwargs)
        context.update({
            'departments': Department.objects.filter(is_active=True)[:6],
            'doctors': DoctorProfile.objects.filter(is_available=True).select_related('user', 'department')[:6],
            'testimonials': Testimonial.objects.filter(is_active=True)[:4],
            'stats': {
                'doctors': DoctorProfile.objects.filter(is_available=True).count(),
                'departments': Department.objects.filter(is_active=True).count(),
                'patients': User.objects.filter(role=User.Role.PATIENT).count(),
            },
        })
        return context


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'core/admin_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        appointments = Appointment.objects.all()
        context.update({
            'total_patients': User.objects.filter(role=User.Role.PATIENT).count(),
            'total_doctors': DoctorProfile.objects.count(),
            'total_appointments': appointments.count(),
            'pending_appointments': appointments.filter(status=Appointment.Status.PENDING).count(),
            'today_appointments': appointments.filter(date=today).count(),
            'recent_appointments': appointments.select_related('patient', 'doctor__user')[:8],
            'departments': Department.objects.annotate(doctor_count=Count('doctors')),
        })
        return context


class AdminUserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = 'core/admin_users.html'
    context_object_name = 'users'
    paginate_by = 15

    def get_queryset(self):
        qs = User.objects.exclude(is_superuser=True).order_by('-created_at')
        role = self.request.GET.get('role')
        q = self.request.GET.get('q')
        if role:
            qs = qs.filter(role=role)
        if q:
            qs = qs.filter(
                Q(username__icontains=q) |
                Q(email__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q)
            )
        return qs
