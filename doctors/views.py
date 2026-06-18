from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView, View

from accounts.mixins import AdminRequiredMixin, DoctorRequiredMixin
from accounts.models import User

from .forms import AvailabilityForm, DepartmentForm, DoctorProfileForm
from .models import AvailabilitySchedule, Department, DoctorProfile


class DoctorListView(ListView):
    model = DoctorProfile
    template_name = 'doctors/doctor_list.html'
    context_object_name = 'doctors'
    paginate_by = 12

    def get_queryset(self):
        qs = DoctorProfile.objects.filter(is_available=True).select_related('user', 'department')
        dept = self.request.GET.get('department')
        q = self.request.GET.get('q')
        if dept:
            qs = qs.filter(department_id=dept)
        if q:
            qs = qs.filter(
                user__first_name__icontains=q
            ) | qs.filter(
                user__last_name__icontains=q
            ) | qs.filter(
                specialization__icontains=q
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.filter(is_active=True)
        context['selected_department'] = self.request.GET.get('department', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class DoctorDetailView(TemplateView):
    template_name = 'doctors/doctor_detail.html'

    def get_context_data(self, **kwargs):
        from appointments.utils import get_available_slots

        context = super().get_context_data(**kwargs)
        doctor = get_object_or_404(
            DoctorProfile.objects.select_related('user', 'department'),
            pk=self.kwargs['pk'],
        )
        context['doctor'] = doctor
        context['availability'] = doctor.availability.filter(is_active=True)
        today = timezone.localdate()
        context['sample_slots'] = get_available_slots(doctor, today)
        return context


class DoctorDashboardView(DoctorRequiredMixin, TemplateView):
    template_name = 'doctors/dashboard.html'

    def get_context_data(self, **kwargs):
        from appointments.models import Appointment

        context = super().get_context_data(**kwargs)
        doctor = get_object_or_404(DoctorProfile, user=self.request.user)
        today = timezone.localdate()
        appointments = Appointment.objects.filter(doctor=doctor).select_related('patient')
        context.update({
            'doctor': doctor,
            'today_appointments': appointments.filter(date=today).exclude(
                status=Appointment.Status.CANCELLED
            ),
            'upcoming_appointments': appointments.filter(date__gte=today).exclude(
                status__in=[Appointment.Status.CANCELLED, Appointment.Status.REJECTED, Appointment.Status.COMPLETED]
            )[:10],
            'pending_count': appointments.filter(status=Appointment.Status.PENDING).count(),
            'total_patients': appointments.values('patient').distinct().count(),
        })
        return context


class DoctorManageListView(AdminRequiredMixin, ListView):
    model = DoctorProfile
    template_name = 'doctors/manage_list.html'
    context_object_name = 'doctors'

    def get_queryset(self):
        return DoctorProfile.objects.select_related('user', 'department').order_by('user__first_name')


class DoctorCreateView(AdminRequiredMixin, CreateView):
    model = DoctorProfile
    form_class = DoctorProfileForm
    template_name = 'doctors/doctor_form.html'
    success_url = reverse_lazy('doctors:manage_list')

    def form_valid(self, form):
        user = User.objects.create_user(
            username=form.cleaned_data['username'],
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password'] or 'changeme123',
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            phone=form.cleaned_data.get('phone', ''),
            role=User.Role.DOCTOR,
        )
        form.instance.user = user
        messages.success(self.request, f'Doctor {user.get_full_name()} added successfully.')
        return super().form_valid(form)


class DoctorUpdateView(AdminRequiredMixin, UpdateView):
    model = DoctorProfile
    form_class = DoctorProfileForm
    template_name = 'doctors/doctor_form.html'
    success_url = reverse_lazy('doctors:manage_list')

    def form_valid(self, form):
        user = self.object.user
        user.username = form.cleaned_data['username']
        user.email = form.cleaned_data['email']
        user.first_name = form.cleaned_data['first_name']
        user.last_name = form.cleaned_data['last_name']
        user.phone = form.cleaned_data.get('phone', '')
        password = form.cleaned_data.get('password')
        if password:
            user.set_password(password)
        user.save()
        messages.success(self.request, 'Doctor profile updated successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context


class DoctorDeleteView(AdminRequiredMixin, DeleteView):
    model = DoctorProfile
    template_name = 'doctors/doctor_confirm_delete.html'
    success_url = reverse_lazy('doctors:manage_list')

    def form_valid(self, form):
        self.object.user.delete()
        messages.success(self.request, 'Doctor removed successfully.')
        return redirect(self.success_url)


class DepartmentListView(AdminRequiredMixin, ListView):
    model = Department
    template_name = 'doctors/department_list.html'
    context_object_name = 'departments'


class DepartmentCreateView(AdminRequiredMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'doctors/department_form.html'
    success_url = reverse_lazy('doctors:department_list')

    def form_valid(self, form):
        messages.success(self.request, 'Department created successfully.')
        return super().form_valid(form)


class DepartmentUpdateView(AdminRequiredMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'doctors/department_form.html'
    success_url = reverse_lazy('doctors:department_list')

    def form_valid(self, form):
        messages.success(self.request, 'Department updated successfully.')
        return super().form_valid(form)


class AvailabilityManageView(DoctorRequiredMixin, TemplateView):
    template_name = 'doctors/availability.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor = get_object_or_404(DoctorProfile, user=self.request.user)
        context['doctor'] = doctor
        context['schedules'] = doctor.availability.all()
        context['form'] = AvailabilityForm()
        return context

    def post(self, request):
        doctor = get_object_or_404(DoctorProfile, user=request.user)
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.doctor = doctor
            schedule.save()
            messages.success(request, 'Availability slot added.')
        else:
            messages.error(request, 'Could not add availability. Please check the form.')
        return redirect('doctors:availability')


class AvailabilityDeleteView(DoctorRequiredMixin, View):
    def post(self, request, pk):
        doctor = get_object_or_404(DoctorProfile, user=request.user)
        schedule = get_object_or_404(AvailabilitySchedule, pk=pk, doctor=doctor)
        schedule.delete()
        messages.success(request, 'Availability slot removed.')
        return redirect('doctors:availability')
