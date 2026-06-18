from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    allowed_roles = []

    def test_func(self):
        user = self.request.user
        if user.is_superuser:
            return True
        return user.role in self.allowed_roles


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['admin']

    def test_func(self):
        user = self.request.user
        return user.is_admin_user


class DoctorRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['doctor']

    def test_func(self):
        return self.request.user.is_doctor_user


class PatientRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['patient']

    def test_func(self):
        return self.request.user.is_patient_user
