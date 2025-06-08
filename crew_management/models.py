from django.db import models
from django.utils import timezone
from datetime import date # Import date for age calculation
from django.contrib.auth.models import User # <--- ADD THIS LINE
# ... (rest of your existing imports and helper functions)
# Helper function to calculate age from date of birth

def calculate_age(dob):
    today = date.today()
    # Subtract years, then subtract 1 if birthday hasn't occurred yet this year
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

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

class CrewMember(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='crew_profile',
                                help_text="Link to the corresponding user account for login (optional)")
    
    # Profile Picture Upload/Display (We'll handle actual upload path later)
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
    # Rank will likely be a foreign key to a separate Rank model later, for now CharField
    current_rank = models.CharField(max_length=100, verbose_name="Current Rank")
    joined_in_company = models.DateField(verbose_name="Date Joined Company")
    joined_in_rank = models.CharField(max_length=100, verbose_name="Rank when First Joined")
    # Principal will be a foreign key to a Principal model later
    principal = models.ForeignKey('Principal', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='crew_members', verbose_name="Main Principal/Client")
    crew_status = models.CharField(max_length=20, choices=SEAFARER_STATUS_CHOICES)
    performance_rating = models.IntegerField(null=True, blank=True, help_text="Rating out of 5") # Example: 1-5 rating
    relieving_plan_date = models.DateField(null=True, blank=True, verbose_name="Projected Next Sign-off Date")
    last_sign_off_date = models.DateField(null=True, blank=True)
    # Vessel assignment will be a foreign key to a Vessel model later
    current_vessel = models.ForeignKey('Vessel', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='current_crew', verbose_name="Current Vessel")
    ssb_no = models.CharField(max_length=50, blank=True, verbose_name="SSB No.") # Can be blank if not available
    client_name_for_appraisal = models.CharField(max_length=200, blank=True, verbose_name="Client Name (for appraisal)")

    # ----------------------------------
    # Communication Log
    # ----------------------------------
    # This will be a separate model related to CrewMember, as it's a list of entries.
    # We'll define it after CrewMember.

    # ----------------------------------
    # Family / Next of Kin Records
    # ----------------------------------
    # This will be a separate model related to CrewMember, as there can be multiple entries.
    # We'll define it after CrewMember.

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
    # Professional Reference Fields
    # ----------------------------------
    # This will be a separate model related to CrewMember, as there can be multiple entries.
    # We'll define it after CrewMember.

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
            # Convert height from feet to meters for BMI calculation (1 ft = 0.3048 m)
            height_m = float(self.height_ft) * 0.3048
            if height_m > 0:
                return round(float(self.weight_kg) / (height_m ** 2), 2)
        return None

    # ----------------------------------
    # Appraisal Fields
    # ----------------------------------
    # This will be a separate model related to CrewMember, as there can be multiple appraisals.
    # We'll define it after CrewMember.

# ... (all your existing models, after Appraisal, before Principal/Vessel placeholders if you put them there) ...

# ----------------------------------
# Experience History (Sea Service Records)
# ----------------------------------
class ExperienceHistory(models.Model):
    crew_member = models.ForeignKey(CrewMember, on_delete=models.CASCADE, related_name='experience_history')
    company_principal_name = models.CharField(max_length=255, verbose_name="Company/Principal Name")
    vessel_name = models.CharField(max_length=255)
    vessel_type = models.CharField(max_length=100, blank=True, null=True) # Optional as per your req
    rank = models.CharField(max_length=100)
    payscale_wages = models.CharField(max_length=100, blank=True, null=True, verbose_name="Payscale/Wages (Optional for Other Co.)")
    port_of_joining = models.CharField(max_length=100)
    sign_on_date = models.DateField()
    sign_off_date = models.DateField()
    port_of_sign_off = models.CharField(max_length=100, blank=True, null=True) # Optional as per your req

    # Calculated Properties (not stored in DB, generated when accessed)
    @property
    def total_experience(self):
        # Calculates total experience in YYMMDD based on sign_on_date and sign_off_date
        if self.sign_on_date and self.sign_off_date:
            delta = self.sign_off_date - self.sign_on_date
            total_days = delta.days

            years = total_days // 365
            remaining_days_after_years = total_days % 365
            months = remaining_days_after_years // 30 # Approximate months
            days = remaining_days_after_years % 30

            return f"{years:02d}Y{months:02d}M{days:02d}D"
        return "00Y00M00D"

    def __str__(self):
        return f"{self.crew_member.first_name}'s experience on {self.vessel_name} ({self.rank})"

    class Meta:
        verbose_name = "Experience Record"
        verbose_name_plural = "Experience History"
        ordering = ['-sign_on_date'] # Order by most recent experience first
    # ----------------------------------
    # Common fields (e.g., for audit/tracking)
    # ----------------------------------
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.seafarer_code})"

    class Meta:
        verbose_name = "Crew Member"
        verbose_name_plural = "Crew Members"


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
        ordering = ['-date'] # Order by latest date first


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
    cnic_copy = models.FileField(upload_to='cnic_copies/', verbose_name="CNIC Copy") # Mandatory file upload
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
    vessel = models.ForeignKey('Vessel', on_delete=models.SET_NULL, null=True, blank=True,
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

    # These fields will be populated automatically when an appraisal is created/updated
    # and linked to a CrewMember.
    # They are not directly stored on Appraisal, but pulled from CrewMember/Vessel
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


# Placeholder models for Principal and Vessel (will be fleshed out later)
# These are needed for ForeignKey relationships in CrewMember and Appraisal
class Principal(models.Model):
    name = models.CharField(max_length=255, unique=True)
    contact_person = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

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

        # ----------------------------------
# Document Management and Validity Tracking
# ----------------------------------

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
    document_no = models.CharField(max_length=100, unique=True) # Assuming document numbers are unique globally
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True) # Some documents may not have expiry
    document_file = models.FileField(upload_to='crew_documents/', null=True, blank=True) # Actual file upload

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
        unique_together = ('crew_member', 'document_name', 'document_type', 'document_no') # Prevent exact duplicates for a crew member
        ordering = ['expiry_date'] # Order by expiry date