from django.contrib import admin

from .models import AvailabilitySchedule, Department, DoctorProfile


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    search_fields = ['name']


class AvailabilityInline(admin.TabularInline):
    model = AvailabilitySchedule
    extra = 1


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'department', 'specialization', 'is_available']
    list_filter = ['department', 'is_available']
    search_fields = ['user__first_name', 'user__last_name', 'specialization']
    inlines = [AvailabilityInline]
