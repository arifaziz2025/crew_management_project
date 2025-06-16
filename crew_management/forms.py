from django import forms
from .models import CrewMember, Principal, Vessel, Document, ExperienceHistory, NextOfKin, CommunicationLog, ProfessionalReference, Appraisal, MonthlyAllotment, FinancialObligation
from .widgets import SsbCdcNumbersWidget # NEW: Import the custom widget
import json # Already used, ensure it's imported

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
            'current_rank',
            'joined_in_company',
            'joined_in_rank',
            'principal',
            'crew_status',
            'performance_rating',
            'relieving_plan_date',
            'last_sign_off_date',
            'current_vessel',
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

# --- New Financial Management Forms ---

class MonthlyAllotmentForm(forms.ModelForm):
    class Meta:
        model = MonthlyAllotment
        fields = [
            'allotment_month',
            'vessel',
            'amount',
            'currency',
            'funding_from_principal_status',
            'tentative_payment_date',
            'actual_payment_date',
            'status',
            'transaction_reference',
            'remarks',
        ]
        widgets = {
            'allotment_month': forms.DateInput(attrs={'type': 'month'}),
            'tentative_payment_date': forms.DateInput(attrs={'type': 'date'}),
            'actual_payment_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_allotment_month(self):
        allotment_month = self.cleaned_data['allotment_month']
        return allotment_month.replace(day=1)


class FinancialObligationForm(forms.ModelForm):
    class Meta:
        model = FinancialObligation
        fields = [
            'obligation_type',
            'opening_balance',
            'amount_due',
            'currency',
            'due_date',
            'amount_paid',
            'status',
            'description',
            'contract_vessel',
            'ssb_cdc_numbers', # This field now uses the custom widget
        ]
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'ssb_cdc_numbers': SsbCdcNumbersWidget(), # NEW: Use the custom widget here
        }

    # IMPORTANT: The clean_ssb_cdc_numbers method is now removed because the widget handles JSON parsing
    # The widget's value_from_datadict method will return a Python list/None/string for invalid JSON
    # If the widget returns a string (due to JSONDecodeError), Django's default validation will
    # flag it, or you can add a custom validator to the field if more complex checks are needed.