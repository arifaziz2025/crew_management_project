from django import forms
from .models import CrewMember, Principal, Vessel, Document, ExperienceHistory, NextOfKin, CommunicationLog, ProfessionalReference, Appraisal


class CrewMemberProfileForm(forms.ModelForm):
    class Meta:
        model = CrewMember
        # Specify the fields you want to be editable via this form
        # For a crew member, they might edit personal info, contact, and working gear.
        # Financials, employment details, user link, etc., might be admin-only.
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

        # ... (existing imports and CrewMemberProfileForm) ...

class PrincipalForm(forms.ModelForm):
    class Meta:
        model = Principal
        # Specify all fields for Principal as they are generally all editable by staff
        fields = [
            'name',
            'contact_person',
            'email',
            'phone',
            'address'
        ]
        # Optional: You can specify widgets for better UI control, e.g., DateInput
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

# ... (existing imports, CrewMemberProfileForm, and PrincipalForm) ...

class VesselForm(forms.ModelForm):
    class Meta:
        model = Vessel
        # Specify all fields for Vessel as they are generally all editable by staff
        fields = [
            'name',
            'imo_number',
            'vessel_type',
            'flag_state',
            'associated_principal'
        ]

        # ... (existing imports, CrewMemberProfileForm, PrincipalForm, and VesselForm) ...

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        # Exclude 'crew_member' because it will be set programmatically in the view
        # Exclude auto-generated fields like 'created_at', 'updated_at'
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

# ... (existing imports, CrewMemberProfileForm, PrincipalForm, VesselForm, and DocumentForm) ...

class ExperienceHistoryForm(forms.ModelForm):
    class Meta:
        model = ExperienceHistory
        # Exclude 'crew_member' as it will be set programmatically
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

        # ... (existing imports, all other forms) ...

class NextOfKinForm(forms.ModelForm):
    class Meta:
        model = NextOfKin
        # Exclude 'crew_member' as it will be set programmatically
        fields = [
            'full_name',
            'father_name',
            'date_of_birth',
            'relation_with_seafarer',
            'cnic_no',
            'cnic_copy', # Include the file field
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

        # ... (existing imports, all other forms) ...

class CommunicationLogForm(forms.ModelForm):
    class Meta:
        model = CommunicationLog
        # Exclude 'crew_member' and 'date' as they will be set programmatically
        fields = [
            'user_name',        # For who logged the communication
            'contact_person_name',
            'purpose_of_call',
            'remarks'
        ]
        # No specific widgets needed here as date is excluded and other fields are text

        # ... (existing imports, all other forms) ...

class ProfessionalReferenceForm(forms.ModelForm):
    class Meta:
        model = ProfessionalReference
        # Exclude 'crew_member' and 'date' as they will be set programmatically
        fields = [
            'company_name',
            'contact_person',
            'designation',
            'email_id',
            'phone_no',
            'mobile_no',
            'fax_no',
            'remarks',
        ]
        # No specific widgets needed, date is excluded

        # ... (existing imports, all other forms) ...

# ... (existing imports, all other forms) ...

class AppraisalForm(forms.ModelForm):
    class Meta:
        model = Appraisal
        # Exclude 'crew_member', 'seafarer_name', 'ssb_no', 'client_name'
        # as these are either set programmatically or are properties/auto-appearing
        fields = [
            'vessel', # Include vessel field for selection
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