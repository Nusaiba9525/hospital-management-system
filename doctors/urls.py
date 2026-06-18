from django.urls import path

from . import views

app_name = 'doctors'

urlpatterns = [
    path('', views.DoctorListView.as_view(), name='list'),
    path('dashboard/', views.DoctorDashboardView.as_view(), name='dashboard'),
    path('manage/', views.DoctorManageListView.as_view(), name='manage_list'),
    path('manage/add/', views.DoctorCreateView.as_view(), name='create'),
    path('manage/<int:pk>/edit/', views.DoctorUpdateView.as_view(), name='update'),
    path('manage/<int:pk>/delete/', views.DoctorDeleteView.as_view(), name='delete'),
    path('departments/', views.DepartmentListView.as_view(), name='department_list'),
    path('departments/add/', views.DepartmentCreateView.as_view(), name='department_create'),
    path('departments/<int:pk>/edit/', views.DepartmentUpdateView.as_view(), name='department_update'),
    path('availability/', views.AvailabilityManageView.as_view(), name='availability'),
    path('availability/<int:pk>/delete/', views.AvailabilityDeleteView.as_view(), name='availability_delete'),
    path('<int:pk>/', views.DoctorDetailView.as_view(), name='detail'),
]
