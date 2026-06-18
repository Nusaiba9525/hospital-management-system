from django.urls import path

from . import views

app_name = 'appointments'

urlpatterns = [
    path('book/', views.AppointmentBookView.as_view(), name='book'),
    path('', views.AppointmentListView.as_view(), name='list'),
    path('<int:pk>/status/', views.AppointmentStatusUpdateView.as_view(), name='status'),
    path('<int:pk>/<str:action>/', views.AppointmentQuickActionView.as_view(), name='quick_action'),
    path('<int:pk>/prescription/', views.PrescriptionUpdateView.as_view(), name='prescription'),
    path('<int:pk>/prescription/pdf/', views.PrescriptionPDFView.as_view(), name='prescription_pdf'),
    path('api/slots/', views.AvailableSlotsAPIView.as_view(), name='api_slots'),
]
