from django import forms
from .models import CrewMember, Principal, Vessel, Document, ExperienceHistory, NextOfKin, CommunicationLog, ProfessionalReference, Appraisal

class CrewMemberProfileForm(forms.ModelForm):
    class Meta:
        model = CrewMember
        fields = [
            'profile_picture',
            'first_name',
            'last_name',
            'father_name',
            'date_of_birth',
            'place_of_birth',
            'marital_status',
            'nationality',
            'city_of_residence',
            'address_temporary',
            'address_permanent',
            'phone_no',
            'mobile_no',
            'email_id',
            'skype_id',
            'domestic_airport',
            'nearest_international_airport',
            'current_rank', # Ensure this is editable if needed for initial creation
            'joined_in_company', # <--- ADDED THIS FIELD
            'joined_in_rank',
            'principal', # Ensure this is editable if needed for initial creation
            'crew_status',
            'performance_rating',
            'relieving_plan_date',
            'last_sign_off_date',
            'current_vessel', # Ensure this is editable if needed for initial creation
            'ssb_no',
            'client_name_for_appraisal',
            'account_title',
            'account_no',
            'bank_name',
            'branch_name_address',
            'iban',
            'swift_code',
            'blank_cheque_leaf_copy',
            'height_ft',
            'weight_kg',
            'collar_cm',
            'chest_cm',
            'waist_cm',
            'shoes_cm',
            'cap_cm',
            'inseam_cm',
            'working_gear_remarks',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'joined_in_company': forms.DateInput(attrs={'type': 'date'}),
            'relieving_plan_date': forms.DateInput(attrs={'type': 'date'}),
            'last_sign_off_date': forms.DateInput(attrs={'type': 'date'}),
        }

class PrincipalForm(forms.ModelForm):
    class Meta:
        model = Principal
        fields = [
            'name',
            'contact_person',
            'email',
            'phone',
            'address'
        ]

class VesselForm(forms.ModelForm):
    class Meta:
        model = Vessel
        fields = [
            'name',
            'imo_number',
            'vessel_type',
            'flag_state',
            'associated_principal'
        ]

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = [
            'document_name',
            'document_type',
            'place_of_issue',
            'issuing_country',
            'document_no',
            'issue_date',
            'expiry_date',
            'document_file'
        ]
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
        }

class ExperienceHistoryForm(forms.ModelForm):
    class Meta:
        model = ExperienceHistory
        fields = [
            'company_principal_name',
            'vessel_name',
            'vessel_type',
            'rank',
            'payscale_wages',
            'port_of_joining',
            'sign_on_date',
            'sign_off_date',
            'port_of_sign_off'
        ]
        widgets = {
            'sign_on_date': forms.DateInput(attrs={'type': 'date'}),
            'sign_off_date': forms.DateInput(attrs={'type': 'date'}),
        }

class NextOfKinForm(forms.ModelForm):
    class Meta:
        model = NextOfKin
        fields = [
            'full_name',
            'father_name',
            'date_of_birth',
            'relation_with_seafarer',
            'cnic_no',
            'cnic_copy',
            'place_of_birth',
            'country_of_birth',
            'nationality',
            'contact_no',
            'alternative_no',
            'email_id'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

class CommunicationLogForm(forms.ModelForm):
    class Meta:
        model = CommunicationLog
        fields = [
            'user_name',
            'contact_person_name',
            'purpose_of_call',
            'remarks'
        ]
        # Assuming 'date' is auto_now_add/default=timezone.now in model, so not in form.
        # If 'date' was in fields, it would need a DateInput widget.

class ProfessionalReferenceForm(forms.ModelForm):
    class Meta:
        model = ProfessionalReference
        fields = [
            'company_name',
            'contact_person',
            'designation',
            'email_id',
            'phone_no',
            'mobile_no',
            'fax_no',
            'remarks',
            # 'date' is likely auto_now_add/default=timezone.now, not in form for manual entry.
        ]

class AppraisalForm(forms.ModelForm):
    class Meta:
        model = Appraisal
        fields = [
            'vessel',
            'evaluation_date',
            'date_sign_on',
            'joining_port',
            'date_sign_off',
            'port_of_discharge',
            'reason_signed_off',
            'total_score',
            'overall_score_obtained',
            'remarks',
        ]
        widgets = {
            'evaluation_date': forms.DateInput(attrs={'type': 'date'}),
            'date_sign_on': forms.DateInput(attrs={'type': 'date'}),
            'date_sign_off': forms.DateInput(attrs={'type': 'date'}),
        }
