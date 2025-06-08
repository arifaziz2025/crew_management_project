from django.urls import path
from . import views

urlpatterns = [
    # ... (existing crew related paths) ...
    path('', views.dashboard_view, name='dashboard'),
    path('crew/list/', views.crew_list, name='crew_list'),
    path('crew/add/', views.crew_create, name='crew_create'),
    path('crew/export/csv/', views.export_crew_csv, name='export_crew_csv'),
    path('crew/import/csv/', views.import_crew_csv, name='import_crew_csv'),
    path('crew/<int:pk>/', views.crew_profile_detail, name='crew_profile_detail'),
    path('crew/<int:pk>/edit/', views.crew_profile_edit, name='crew_profile_edit'),

    # --- Principal Management URLs ---
    path('principals/', views.principal_list, name='principal_list'),
    path('principals/add/', views.principal_create, name='principal_create'),
    path('principals/<int:pk>/', views.principal_detail, name='principal_detail'),
    path('principals/<int:pk>/edit/', views.principal_edit, name='principal_edit'),

    path('vessels/', views.vessel_list, name='vessel_list'), # <--- THIS LINE MUST BE PRESENT AND CORRECT
    path('vessels/add/', views.vessel_create, name='vessel_create'),
    path('vessels/<int:pk>/', views.vessel_detail, name='vessel_detail'),
    path('vessels/<int:pk>/edit/', views.vessel_edit, name='vessel_edit'),

    # --- Document Management URLs ---
    # List documents for a specific crew member
    path('crew/<int:crew_pk>/documents/', views.document_list_for_crew, name='document_list_for_crew'),
    # Add new document for a specific crew member
    path('crew/<int:crew_pk>/documents/add/', views.document_create, name='document_create'),
    # View specific document details
    path('documents/<int:pk>/', views.document_detail, name='document_detail'),
    # Edit specific document
    path('documents/<int:pk>/edit/', views.document_edit, name='document_edit'),

    path('crew/<int:crew_pk>/experience/', views.experience_list_for_crew, name='experience_list_for_crew'),
    # Add new experience record for a specific crew member
    path('crew/<int:crew_pk>/experience/add/', views.experience_create, name='experience_create'),
    # View specific experience record details
    path('experience/<int:pk>/', views.experience_detail, name='experience_detail'),
    # Edit specific experience record
    path('experience/<int:pk>/edit/', views.experience_edit, name='experience_edit'),

    path('crew/<int:crew_pk>/nextofkin/', views.nextofkin_list_for_crew, name='nextofkin_list_for_crew'),
    # Add new Next of Kin record for a specific crew member
    path('crew/<int:crew_pk>/nextofkin/add/', views.nextofkin_create, name='nextofkin_create'),
    # View specific Next of Kin record details
    path('nextofkin/<int:pk>/', views.nextofkin_detail, name='nextofkin_detail'),
    # Edit specific Next of Kin record
    path('nextofkin/<int:pk>/edit/', views.nextofkin_edit, name='nextofkin_edit'),

    path('crew/<int:crew_pk>/logs/', views.communicationlog_list_for_crew, name='communicationlog_list_for_crew'),
    # Add new Communication Log record for a specific crew member
    path('crew/<int:crew_pk>/logs/add/', views.communicationlog_create, name='communicationlog_create'),
    # View specific Communication Log record details
    path('logs/<int:pk>/', views.communicationlog_detail, name='communicationlog_detail'),
    # Edit specific Communication Log record
    path('logs/<int:pk>/edit/', views.communicationlog_edit, name='communicationlog_edit'),

path('crew/<int:crew_pk>/references/', views.professionalreference_list_for_crew, name='professionalreference_list_for_crew'),
    # Add new Professional Reference record for a specific crew member
    path('crew/<int:crew_pk>/references/add/', views.professionalreference_create, name='professionalreference_create'),
    # View specific Professional Reference record details
    path('references/<int:pk>/', views.professionalreference_detail, name='professionalreference_detail'),
    # Edit specific Professional Reference record
    path('references/<int:pk>/edit/', views.professionalreference_edit, name='professionalreference_edit'),

    path('crew/<int:crew_pk>/appraisals/', views.appraisal_list_for_crew, name='appraisal_list_for_crew'),
    # Add new Appraisal record for a specific crew member
    path('crew/<int:crew_pk>/appraisals/add/', views.appraisal_create, name='appraisal_create'),
    # View specific Appraisal record details
    path('appraisals/<int:pk>/', views.appraisal_detail, name='appraisal_detail'),
    # Edit specific Appraisal record
    path('appraisals/<int:pk>/edit/', views.appraisal_edit, name='appraisal_edit'),
]