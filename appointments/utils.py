from datetime import datetime, timedelta

from django.utils import timezone

from appointments.models import Appointment
from doctors.models import AvailabilitySchedule


def get_available_slots(doctor, date):
    """Return list of available time slots for a doctor on a given date."""
    day_of_week = date.weekday()
    schedules = AvailabilitySchedule.objects.filter(
        doctor=doctor,
        day_of_week=day_of_week,
        is_active=True,
    )

    if not schedules.exists():
        return []

    booked_times = set(
        Appointment.objects.filter(
            doctor=doctor,
            date=date,
        ).exclude(
            status__in=[Appointment.Status.CANCELLED, Appointment.Status.REJECTED]
        ).values_list('time', flat=True)
    )

    slots = []
    now = timezone.localtime()
    for schedule in schedules:
        current = datetime.combine(date, schedule.start_time)
        end = datetime.combine(date, schedule.end_time)
        delta = timedelta(minutes=schedule.slot_duration)

        while current + delta <= end:
            slot_time = current.time()
            if slot_time not in booked_times:
                if date > now.date() or (date == now.date() and slot_time > now.time()):
                    slots.append(slot_time.strftime('%H:%M'))
            current += delta

    return slots
