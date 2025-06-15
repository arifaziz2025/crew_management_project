# crew_management/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # --- Authentication URLs ---
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.dashboard, name='dashboard'), # Dashboard as root

    # --- Crew Management URLs ---
    path('crew/', views.crew_list, name='crew_list'),
    path('crew/add/', views.crew_create, name='crew_create'),
    path('crew/<int:pk>/', views.crew_profile_detail, name='crew_profile_detail'),
    path('crew/<int:pk>/edit/', views.crew_profile_edit, name='crew_profile_edit'),
    path('crew/<int:pk>/delete/', views.crew_delete, name='crew_delete'),
    path('crew/import-csv/', views.import_crew_csv, name='import_crew_csv'),
    path('crew/export-csv/', views.export_crew_csv, name='export_crew_csv'),

    # --- Principal Management URLs ---
    path('principals/', views.principal_list, name='principal_list'),
    path('principals/add/', views.principal_create, name='principal_create'),
    path('principals/<int:pk>/', views.principal_detail, name='principal_detail'),
    path('principals/<int:pk>/edit/', views.principal_edit, name='principal_edit'), # Added edit URL
    path('principals/<int:pk>/delete/', views.principal_delete, name='principal_delete'),
    path('principals/import-csv/', views.import_principal_csv, name='import_principal_csv'),
    path('principals/export-csv/', views.export_principal_csv, name='export_principal_csv'),

    # --- Vessel Management URLs ---
    path('vessels/', views.vessel_list, name='vessel_list'),
    path('vessels/add/', views.vessel_create, name='vessel_create'),
    path('vessels/<int:pk>/', views.vessel_detail, name='vessel_detail'),
    path('vessels/<int:pk>/edit/', views.vessel_edit, name='vessel_edit'), # Added edit URL
    path('vessels/<int:pk>/delete/', views.vessel_delete, name='vessel_delete'),
    path('vessels/import-csv/', views.import_vessel_csv, name='import_vessel_csv'),
    path('vessels/export-csv/', views.export_vessel_csv, name='export_vessel_csv'),

    # --- Document Management URLs ---
    # URLs for documents nested under a crew member
    path('crew/<int:pk>/documents/', views.crew_document_list, name='crew_document_list'),
    path('crew/<int:pk>/documents/add/', views.crew_document_add, name='crew_document_add'),
    # URLs for individual document operations (not nested)
    path('documents/<int:pk>/', views.document_detail, name='document_detail'),
    path('documents/<int:pk>/edit/', views.document_edit, name='document_edit'),
    path('documents/<int:pk>/delete/', views.document_delete, name='document_delete'),


    # --- Experience History URLs ---
    path('crew/<int:crew_pk>/experience/', views.crew_experience_list, name='crew_experience_list'),
    path('crew/<int:crew_pk>/experience/add/', views.experience_add, name='experience_add'), # Changed to _add suffix
    path('experience/<int:pk>/', views.experience_detail, name='experience_detail'),
    path('experience/<int:pk>/edit/', views.experience_edit, name='experience_edit'),
    path('experience/<int:pk>/delete/', views.experience_delete, name='experience_delete'),

    # --- Next of Kin URLs ---
    path('crew/<int:crew_pk>/nextofkin/', views.crew_nextofkin_list, name='crew_nextofkin_list'),
    path('crew/<int:crew_pk>/nextofkin/add/', views.nextofkin_add, name='nextofkin_add'),
    path('nextofkin/<int:pk>/', views.nextofkin_detail, name='nextofkin_detail'),
    path('nextofkin/<int:pk>/edit/', views.nextofkin_edit, name='nextofkin_edit'),
    path('nextofkin/<int:pk>/delete/', views.nextofkin_delete, name='nextofkin_delete'),

    # --- Communication Log URLs ---
    path('crew/<int:crew_pk>/logs/', views.crew_communication_log_list, name='crew_communication_log_list'),
    path('crew/<int:crew_pk>/logs/add/', views.communicationlog_add, name='communicationlog_add'),
    path('logs/<int:pk>/', views.communicationlog_detail, name='communicationlog_detail'),
    path('logs/<int:pk>/edit/', views.communicationlog_edit, name='communicationlog_edit'),
    path('logs/<int:pk>/delete/', views.communicationlog_delete, name='communicationlog_delete'),

    # --- Professional Reference URLs ---
    path('crew/<int:crew_pk>/references/', views.crew_professional_reference_list, name='crew_professional_reference_list'),
    path('crew/<int:crew_pk>/references/add/', views.professionalreference_add, name='professionalreference_add'),
    path('references/<int:pk>/', views.professionalreference_detail, name='professionalreference_detail'),
    path('references/<int:pk>/edit/', views.professionalreference_edit, name='professionalreference_edit'),
    path('references/<int:pk>/delete/', views.professionalreference_delete, name='professionalreference_delete'),

    # --- Appraisal URLs ---
    path('crew/<int:crew_pk>/appraisals/', views.crew_appraisal_list, name='crew_appraisal_list'),
    path('crew/<int:crew_pk>/appraisals/add/', views.appraisal_add, name='appraisal_add'),
    path('appraisals/<int:pk>/', views.appraisal_detail, name='appraisal_detail'),
    path('appraisals/<int:pk>/edit/', views.appraisal_edit, name='appraisal_edit'),
    path('appraisals/<int:pk>/delete/', views.appraisal_delete, name='appraisal_delete'),

    # --- Audit Log URL ---
    path('audit-log/', views.audit_log_list, name='audit_log_list'),
]