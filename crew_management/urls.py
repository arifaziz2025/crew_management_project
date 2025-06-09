from django.urls import path
from django.shortcuts import redirect # Import redirect for lambda functions
from . import views

urlpatterns = [
    # Dashboard (Root URL)
    path('', views.dashboard_view, name='dashboard'),

    # Crew Management URLs
    path('crew/list/', views.crew_list, name='crew_list'),
    path('crew/add/', views.crew_create, name='crew_create'),
    path('crew/export/csv/', views.export_crew_csv, name='export_crew_csv'),
    path('crew/import/csv/', views.import_crew_csv, name='import_crew_csv'),
    path('crew/<int:pk>/', views.crew_profile_detail, name='crew_profile_detail'),
    path('crew/<int:pk>/edit/', views.crew_profile_edit, name='crew_profile_edit'),
    path('crew/<int:pk>/delete/', views.crew_delete, name='crew_delete'), # <--- ADDED THIS LINE

    # Principal Management URLs
    path('principals/', views.principal_list, name='principal_list'),
    path('principals/add/', views.principal_create, name='principal_create'),
    path('principals/<int:pk>/', views.principal_detail, name='principal_detail'),
    path('principals/<int:pk>/edit/', views.principal_edit, name='principal_edit'),
    path('principals/<int:pk>/delete/', views.principal_delete, name='principal_delete'), # <--- ADDED THIS LINE

    # Vessel Management URLs
    path('vessels/', views.vessel_list, name='vessel_list'),
    path('vessels/add/', views.vessel_create, name='vessel_create'),
    path('vessels/<int:pk>/', views.vessel_detail, name='vessel_detail'),
    path('vessels/<int:pk>/edit/', views.vessel_edit, name='vessel_edit'),
    path('vessels/<int:pk>/delete/', views.vessel_delete, name='vessel_delete'), # <--- ADDED THIS LINE

    # Document Management URLs (per crew member)
    path('crew/<int:crew_pk>/documents/', views.document_list_for_crew, name='document_list_for_crew'),
    path('crew/<int:crew_pk>/documents/add/', views.document_create, name='document_create'),
    path('documents/<int:pk>/', views.document_detail, name='document_detail'),
    path('documents/<int:pk>/edit/', views.document_edit, name='document_edit'),

    # Experience History URLs (per crew member)
    path('crew/<int:crew_pk>/experience/', views.experience_list_for_crew, name='experience_list_for_crew'),
    path('crew/<int:crew_pk>/experience/add/', views.experience_create, name='experience_create'),
    path('experience/<int:pk>/', views.experience_detail, name='experience_detail'),
    path('experience/<int:pk>/edit/', views.experience_edit, name='experience_edit'),

    # Next of Kin URLs (per crew member)
    path('crew/<int:crew_pk>/nextofkin/', views.nextofkin_list_for_crew, name='nextofkin_list_for_crew'),
    path('crew/<int:crew_pk>/nextofkin/add/', views.nextofkin_create, name='nextofkin_create'),
    path('nextofkin/<int:pk>/', views.nextofkin_detail, name='nextofkin_detail'),
    path('nextofkin/<int:pk>/edit/', views.nextofkin_edit, name='nextofkin_edit'),

    # Communication Log URLs (per crew member)
    path('crew/<int:crew_pk>/logs/', views.communicationlog_list_for_crew, name='communicationlog_list_for_crew'),
    path('crew/<int:crew_pk>/logs/add/', views.communicationlog_create, name='communicationlog_create'),
    path('logs/<int:pk>/', views.communicationlog_detail, name='communicationlog_detail'),
    path('logs/<int:pk>/edit/', views.communicationlog_edit, name='communicationlog_edit'),

    # Professional Reference URLs (per crew member)
    path('crew/<int:crew_pk>/references/', views.professionalreference_list_for_crew, name='professionalreference_list_for_crew'),
    path('crew/<int:crew_pk>/references/add/', views.professionalreference_create, name='professionalreference_create'),
    path('references/<int:pk>/', views.professionalreference_detail, name='professionalreference_detail'),
    path('references/<int:pk>/edit/', views.professionalreference_edit, name='professionalreference_edit'),

    # Appraisal URLs (per crew member)
    path('crew/<int:crew_pk>/appraisals/', views.appraisal_list_for_crew, name='appraisal_list_for_crew'),
    path('crew/<int:crew_pk>/appraisals/add/', views.appraisal_create, name='appraisal_create'),
    path('appraisals/<int:pk>/', views.appraisal_detail, name='appraisal_detail'),
    path('appraisals/<int:pk>/edit/', views.appraisal_edit, name='appraisal_edit'),

    # --- FINANCIAL MANAGEMENT URLS WILL BE ADDED HERE LATER ---
]
