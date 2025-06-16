# crew_management/models.py

from django.db import models
from django.utils import timezone
from datetime import date
from django.contrib.auth.models import User
import json # Ensure this is imported for JSONField

# Helper function to calculate age from date of birth
def calculate_age(dob):
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, today.day))

# Helper function to calculate total experience in YYMMDD format
def calculate_experience(sign_on_date, sign_off_date):
    if not sign_on_date or not sign_off_date:
        return "00Y00M00D"

    delta = sign_off_date - sign_on_date
    total_days = delta.days

    years = total_days // 365
    remaining_days_after_years = total_days % 365
    months = remaining_days_after_years // 30 # Approximate months
    days = remaining_days_after_years % 30

    return f"{years:02d}Y{months:02d}M{days:02d}D"


class Principal(models.Model):
    name = models.CharField(max_length=255, unique=True)
    contact_person = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Principal"
        verbose_name_plural = "Principals"


class Vessel(models.Model):
    name = models.CharField(max_length=255)
    imo_number = models.CharField(max_length=7, unique=True, verbose_name="IMO Number")
    vessel_type = models.CharField(max_length=100)
    flag_state = models.CharField(max_length=100)
    associated_principal = models.ForeignKey(Principal, on_delete=models.SET_NULL, null=True, blank=True,
                                            related_name='vessels')

    def __str__(self):
        return f"{self.name} ({self.imo_number})"

    class Meta:
        verbose_name = "Vessel"
        verbose_name_plural = "Vessels"


class CrewMember(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='crew_profile',
                                help_text="Link to the corresponding user account for login (optional)")

    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    # ----------------------------------
    # Personal Information
    # ----------------------------------
    SEAFARER_STATUS_CHOICES = [
        ('On Leave', 'On Leave'),
        ('Onboard', 'Onboard'),
        ('Available', 'Available'),
        ('Sick Leave', 'Sick Leave'),
        ('Other', 'Other'),
    ]
    MARITAL_STATUS_CHOICES = [
        ('Single', 'Single'),
        ('Married', 'Married'),
        ('Divorced', 'Divorced'),
        ('Widowed', 'Widowed'),
    ]

    seafarer_code = models.CharField(max_length=50, unique=True, verbose_name="Seafarer Code / Number")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    place_of_birth = models.CharField(max_length=100)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES)
    nationality = models.CharField(max_length=100)
    city_of_residence = models.CharField(max_length=100)

    # Calculated Properties (not stored in DB, generated when accessed)
    @property
    def age(self):
        return calculate_age(self.date_of_birth) if self.date_of_birth else None

    # ----------------------------------
    # Contact Information
    # ----------------------------------
    address_temporary = models.TextField(blank=True, verbose_name="Temporary Address")
    address_permanent = models.TextField(verbose_name="Permanent Address")
    phone_no = models.CharField(max_length=20, verbose_name="Phone No.")
    mobile_no = models.CharField(max_length=20, verbose_name="Mobile No.")
    email_id = models.EmailField(unique=True)
    skype_id = models.CharField(max_length=100, blank=True, null=True)
    domestic_airport = models.CharField(max_length=100)
    nearest_international_airport = models.CharField(max_length=100)

    # ----------------------------------
    # Employment Details
    # ----------------------------------
    current_rank = models.CharField(max_length=100, verbose_name="Current Rank")
    joined_in_company = models.DateField(verbose_name="Date Joined Company")
    joined_in_rank = models.CharField(max_length=100, verbose_name="Rank when First Joined")
    principal = models.ForeignKey(Principal, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='crew_members', verbose_name="Main Principal/Client")
    crew_status = models.CharField(max_length=20, choices=SEAFARER_STATUS_CHOICES)
    performance_rating = models.IntegerField(null=True, blank=True, help_text="Rating out of 5")
    relieving_plan_date = models.DateField(null=True, blank=True, verbose_name="Projected Next Sign-off Date")
    last_sign_off_date = models.DateField(null=True, blank=True)
    current_vessel = models.ForeignKey(Vessel, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='current_crew', verbose_name="Current Vessel")
    ssb_no = models.CharField(max_length=50, blank=True, verbose_name="SSB No.")
    client_name_for_appraisal = models.CharField(max_length=200, blank=True, verbose_name="Client Name (for appraisal)")

    # ----------------------------------
    # Bank Account Fields
    # ----------------------------------
    account_title = models.CharField(max_length=255, verbose_name="Account Title")
    account_no = models.CharField(max_length=50, verbose_name="Account No.")
    bank_name = models.CharField(max_length=255)
    branch_name_address = models.TextField(verbose_name="Branch Name & Address")
    iban = models.CharField(max_length=34, verbose_name="IBAN")
    swift_code = models.CharField(max_length=11, verbose_name="SWIFT Code")
    blank_cheque_leaf_copy = models.FileField(upload_to='bank_docs/', null=True, blank=True, verbose_name="Copy of Blank Cheque Leaf")

    # ----------------------------------
    # Working Gear Fields
    # ----------------------------------
    height_ft = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, verbose_name="Height (ft)")
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Weight (kg)")
    collar_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Collar (cm)")
    chest_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Chest (cm)")
    waist_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Waist (cm)")
    shoes_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Shoes (cm)")
    cap_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Cap (cm)")
    inseam_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Inseam (cm)")
    working_gear_remarks = models.TextField(blank=True, verbose_name="Remarks (Working Gear)")

    @property
    def bmi(self):
        if self.height_ft and self.weight_kg:
            height_m = float(self.height_ft) * 0.3048
            if height_m > 0:
                return round(float(self.weight_kg) / (height_m ** 2), 2)
        return None

    # ----------------------------------
    # Common fields (for audit/tracking)
    # ----------------------------------
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.seafarer_code})"

    class Meta:
        verbose_name = "Crew Member"
        verbose_name_plural = "Crew Members"


class ExperienceHistory(models.Model):
    crew_member = models.ForeignKey(CrewMember, on_delete=models.CASCADE, related_name='experience_history')
    company_principal_name = models.CharField(max_length=255, verbose_name="Company/Principal Name")
    vessel_name = models.CharField(max_length=255)
    vessel_type = models.CharField(max_length=100, blank=True, null=True)
    rank = models.CharField(max_length=100)
    payscale_wages = models.CharField(max_length=100, blank=True, null=True, verbose_name="Payscale/Wages (Optional for Other Co.)")
    port_of_joining = models.CharField(max_length=100)
    sign_on_date = models.DateField()
    sign_off_date = models.DateField()
    port_of_sign_off = models.CharField(max_length=100, blank=True, null=True)

    @property
    def total_experience(self):
        if self.sign_on_date and self.sign_off_date:
            delta = self.sign_off_date - self.sign_on_date
            total_days = delta.days

            years = total_days // 365
            remaining_days_after_years = total_days % 365
            months = remaining_days_after_years // 30
            days = remaining_days_after_years % 30

            return f"{years:02d}Y{months:02d}M{days:02d}D"
        return "00Y00M00D"

    def __str__(self):
        return f"{self.crew_member.first_name}'s experience on {self.vessel_name} ({self.rank})"

    class Meta:
        verbose_name = "Experience Record"
        verbose_name_plural = "Experience History"
        ordering = ['-sign_on_date']


class CommunicationLog(models.Model):
    crew_member = models.ForeignKey(CrewMember, on_delete=models.CASCADE, related_name='communication_logs')
    user_name = models.CharField(max_length=200, verbose_name="User Name (Auto Inserted)")
    date = models.DateField(default=timezone.now, verbose_name="Date (Auto Inserted)")
    contact_person_name = models.CharField(max_length=200, verbose_name="Contact Person Name")
    purpose_of_call = models.CharField(max_length=255, verbose_name="Purpose of Call")
    remarks = models.TextField()

    def __str__(self):
        return f"Log for {self.crew_member.first_name} on {self.date}"

    class Meta:
        verbose_name = "Communication Log Entry"
        verbose_name_plural = "Communication Log Entries"
        ordering = ['-date']


class NextOfKin(models.Model):
    crew_member = models.ForeignKey(CrewMember, on_delete=models.CASCADE, related_name='next_of_kins')
    full_name = models.CharField(max_length=200)
    father_name = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    RELATION_CHOICES = [
        ('Spouse', 'Spouse'),
        ('Child', 'Child'),
        ('Parent', 'Parent'),
        ('Sibling', 'Sibling'),
        ('Other', 'Other'),
    ]
    relation_with_seafarer = models.CharField(max_length=50, choices=RELATION_CHOICES, verbose_name="Relation With Seafarer")
    cnic_no = models.CharField(max_length=15, unique=True, verbose_name="CNIC No.")
    cnic_copy = models.FileField(upload_to='cnic_copies/', verbose_name="CNIC Copy")
    place_of_birth = models.CharField(max_length=100)
    country_of_birth = models.CharField(max_length=100)
    nationality = models.CharField(max_length=100)
    contact_no = models.CharField(max_length=20)
    alternative_no = models.CharField(max_length=20, blank=True, null=True)
    email_id = models.EmailField(blank=True, null=True)

    @property
    def age(self):
        return calculate_age(self.date_of_birth) if self.date_of_birth else None

    def __str__(self):
        return f"{self.full_name} ({self.relation_with_seafarer}) for {self.crew_member.first_name}"

    class Meta:
        verbose_name = "Next of Kin"
        verbose_name_plural = "Next of Kin Records"


class ProfessionalReference(models.Model):
    crew_member = models.ForeignKey(CrewMember, on_delete=models.CASCADE, related_name='professional_references')
    company_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=200)
    designation = models.CharField(max_length=200)
    email_id = models.EmailField()
    phone_no = models.CharField(max_length=20)
    mobile_no = models.CharField(max_length=20, blank=True, null=True)
    fax_no = models.CharField(max_length=20, blank=True, null=True)
    remarks = models.TextField()
    date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Ref: {self.contact_person} from {self.company_name} for {self.crew_member.first_name}"

    class Meta:
        verbose_name = "Professional Reference"
        verbose_name_plural = "Professional References"


class Appraisal(models.Model):
    crew_member = models.ForeignKey(CrewMember, on_delete=models.CASCADE, related_name='appraisals')
    vessel = models.ForeignKey(Vessel, on_delete=models.SET_NULL, null=True, blank=True,
                            verbose_name="Vessel Name (Auto Appearing)")
    evaluation_date = models.DateField()
    date_sign_on = models.DateField(verbose_name="Date Sign On")
    joining_port = models.CharField(max_length=100)
    date_sign_off = models.DateField(verbose_name="Date Sign Off")
    port_of_discharge = models.CharField(max_length=100)
    reason_signed_off = models.TextField(verbose_name="Reason Signed Off")
    total_score = models.IntegerField(help_text="e.g., 5")
    overall_score_obtained = models.IntegerField(help_text="e.g., 3")
    remarks = models.TextField()

    @property
    def seafarer_name(self):
        return f"{self.crew_member.first_name} {self.crew_member.last_name}"

    @property
    def ssb_no(self):
        return self.crew_member.ssb_no

    @property
    def client_name(self):
        return self.crew_member.client_name_for_appraisal

    def __str__(self):
        return f"Appraisal for {self.crew_member.first_name} on {self.vessel.name if self.vessel else 'N/A'} ({self.evaluation_date})"

    class Meta:
        verbose_name = "Appraisal"
        verbose_name_plural = "Appraisals"
        ordering = ['-evaluation_date']


class Document(models.Model):
    crew_member = models.ForeignKey(CrewMember, on_delete=models.CASCADE, related_name='documents')

    DOCUMENT_TYPE_CHOICES = [
        ('Travel', 'Travel Document'),
        ('License', 'License'),
        ('Training', 'Training Certificate'),
        ('Medical', 'Medical Certificate'),
        ('Flag', 'Flag Document'),
        ('Recruitment', 'Recruitment Document'),
        ('Other', 'Other Document'),
    ]

    # Document Fields
    document_name = models.CharField(max_length=255)
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES)
    place_of_issue = models.CharField(max_length=100)
    issuing_country = models.CharField(max_length=100)
    document_no = models.CharField(max_length=100, unique=False)
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    document_file = models.FileField(upload_to='crew_documents/', null=True, blank=True)

    # Auto-tracked fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_expired(self):
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False

    def days_to_expiry(self):
        if self.expiry_date:
            today = timezone.now().date()
            delta = self.expiry_date - today
            return delta.days
        return None

    def __str__(self):
        return f"{self.document_name} ({self.document_no}) for {self.crew_member.first_name} {self.crew_member.last_name}"

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        unique_together = ('crew_member', 'document_name', 'document_type', 'document_no')
        ordering = ['expiry_date']


# --- New Financial Management Models ---

class MonthlyAllotment(models.Model):
    FUNDS_STATUS_CHOICES = [
        ('RECEIVED', 'Received'),
        ('NOT_RECEIVED', 'Not Received'),
        ('PRINCIPAL_PAYS_DIRECT', 'Principal Pays Direct'),
    ]
    ALLOTMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('PARTIAL', 'Partial Payment'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
    ]

    crew_member = models.ForeignKey(CrewMember, on_delete=models.CASCADE, related_name='monthly_allotments')
    vessel = models.ForeignKey(Vessel, on_delete=models.SET_NULL, null=True, blank=True,
                               verbose_name="Vessel at Allotment",
                               help_text="Vessel crew member was onboard during this allotment period.")
    allotment_month = models.DateField(help_text="Month and year for this allotment (e.g., 2025-06-01)") # Storing as first day of month
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=5, default='USD') # Example, consider choices or FK to Currency
    funding_from_principal_status = models.CharField(
        max_length=30, choices=FUNDS_STATUS_CHOICES, default='NOT_RECEIVED',
        help_text="Status of funds from Principal for this allotment."
    )
    tentative_payment_date = models.DateField(
        help_text="Tentative date for payment to crew. Used for alerts."
    )
    actual_payment_date = models.DateField(null=True, blank=True,
                                           help_text="Actual date payment was confirmed to crew.")
    status = models.CharField(max_length=15, choices=ALLOTMENT_STATUS_CHOICES, default='PENDING')
    transaction_reference = models.CharField(max_length=100, blank=True, null=True,
                                             help_text="Internal transaction ID or bank reference.")
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Allotment for {self.crew_member.first_name} {self.crew_member.last_name} ({self.allotment_month.strftime('%b %Y')}) - {self.amount} {self.currency}"

    class Meta:
        verbose_name = "Monthly Allotment"
        verbose_name_plural = "Monthly Allotments"
        unique_together = ('crew_member', 'allotment_month') # Ensure unique allotment per crew per month
        ordering = ['-allotment_month']


class FinancialObligation(models.Model):
    OBLIGATION_TYPE_CHOICES = [
        ('RETIREMENT_DUE', 'Retirement Due'),
        ('LOAN', 'Loan'),
        ('FINE', 'Fine'),
        ('BONUS', 'Bonus'),
        ('OTHER', 'Other Obligation'),
    ]
    OBLIGATION_STATUS_CHOICES = [
        ('OUTSTANDING', 'Outstanding'),
        ('PARTIALLY_PAID', 'Partially Paid'),
        ('PAID', 'Paid'),
        ('WAIVED', 'Waived'),
        ('CANCELLED', 'Cancelled'),
    ]

    crew_member = models.ForeignKey(CrewMember, on_delete=models.CASCADE, related_name='financial_obligations')
    obligation_type = models.CharField(max_length=20, choices=OBLIGATION_TYPE_CHOICES)
    # New: Opening balance for previously collected dues
    opening_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,
                                         help_text="Any balance transferred from previous records.")
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=5, default='USD') # Example, consider choices or FK to Currency
    due_date = models.DateField(null=True, blank=True) # Can be null if ongoing or immediate
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00,
                                      help_text="Total amount paid against this obligation.")
    status = models.CharField(max_length=15, choices=OBLIGATION_STATUS_CHOICES, default='OUTSTANDING')
    description = models.TextField(blank=True, null=True)
    
    # New: Contract/Vessel context for Gratuity/Retirement
    contract_vessel = models.ForeignKey(Vessel, on_delete=models.SET_NULL, null=True, blank=True,
                                        verbose_name="Associated Vessel/Contract",
                                        help_text="Vessel or contract period this obligation is tied to (e.g., Gratuity from this vessel's tenure).")
    
    # New: Multiple SSB/CDC Numbers (JSONField for structured data)
    # Example format in JSON: [{"number": "12345", "expiry": "2026-12-31"}, {"number": "67890", "expiry": "2028-06-30"}]
    ssb_cdc_numbers = models.JSONField(blank=True, null=True,
                                      help_text="List of SSB/CDC numbers (JSON format: [{\"number\": \"value\", \"expiry\": \"YYYY-MM-DD\"}])")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def balance_due(self):
        return self.amount_due - self.amount_paid

    def __str__(self):
        return f"{self.crew_member.first_name} {self.crew_member.last_name} - {self.get_obligation_type_display()} ({self.amount_due} {self.currency})"

    class Meta:
        verbose_name = "Financial Obligation"
        verbose_name_plural = "Financial Obligations"
        ordering = ['due_date', 'status']


# --- AuditLog model MUST be at the very end to avoid NameErrors for other models it references ---
class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('LOGIN', 'User Logged In'),
        ('LOGOUT', 'User Logged Out'),
        ('PASSWORD_CHANGE', 'Password Changed'),
        ('CREATE', 'Record Created'),
        ('UPDATE', 'Record Updated'),
        ('DELETE', 'Record Deleted'),
        ('IMPORT', 'Data Imported'),
        ('EXPORT', 'Data Exported'),
        ('EMAIL_SENT', 'Email Sent'), # Added for email alert logging
        ('EMAIL_FAIL', 'Email Failed'), # Added for email alert logging
        # Add more specific actions as needed, e.g., 'DOCUMENT_VIEW', 'PROFILE_VIEW'
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                             help_text="User who performed the action")
    action_type = models.CharField(max_length=50, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    model_name = models.CharField(max_length=100, blank=True, null=True,
                                  help_text="Name of the model affected (e.g., 'CrewMember')")
    record_id = models.PositiveIntegerField(blank=True, null=True,
                                            help_text="ID of the record affected")
    description = models.TextField(help_text="Detailed description of the action")
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    changes = models.JSONField(blank=True, null=True, help_text="Dictionary of changed fields (old_value, new_value)")

    class Meta:
        verbose_name = "Audit Log Entry"
        verbose_name_plural = "Audit Log Entries"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {self.user.username if self.user else 'System'} - {self.get_action_type_display()} on {self.model_name}:{self.record_id if self.record_id else 'N/A'}"