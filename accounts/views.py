from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, UpdateView

from patients.forms import PatientProfileForm
from patients.models import PatientProfile

from accounts.models import User

from .forms import LoginForm, PatientRegistrationForm, ProfileUpdateForm
from .mixins import LoginRequiredMixin


class RegisterView(CreateView):
    form_class = PatientRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('patients:dashboard')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(request.user.get_dashboard_url_name())
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        PatientProfile.objects.get_or_create(user=self.object)
        login(self.request, self.object)
        messages.success(self.request, 'Welcome to MedCare Hospital! Your account has been created.')
        return response


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy(self.request.user.get_dashboard_url_name())


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('core:home')

    def dispatch(self, request, *args, **kwargs):
        messages.info(request, 'You have been logged out successfully.')
        return super().dispatch(request, *args, **kwargs)


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileUpdateForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_patient_user:
            profile, _ = PatientProfile.objects.get_or_create(user=user)
            context['patient_form'] = PatientProfileForm(instance=profile)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            self.object = form.save()
            if request.user.is_patient_user:
                profile, _ = PatientProfile.objects.get_or_create(user=request.user)
                patient_form = PatientProfileForm(request.POST, instance=profile)
                if patient_form.is_valid():
                    patient_form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect(self.success_url)
        return self.form_invalid(form)
