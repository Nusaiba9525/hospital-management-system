from django.contrib import admin

from .models import Appointment, Testimonial


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'date', 'time', 'status', 'created_at']
    list_filter = ['status', 'date', 'doctor']
    search_fields = ['patient__username', 'doctor__user__first_name']
    date_hierarchy = 'date'


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'rating', 'is_active']
