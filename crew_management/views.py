import csv # For CSV handling
import io 
from django.http import HttpResponse 

from django.shortcuts import render, get_object_or_404, Http404, redirect
from .models import CrewMember, Document, Principal, Vessel, ExperienceHistory, NextOfKin, CommunicationLog, ProfessionalReference, Appraisal   
from django.db.models import Count 
from django.utils import timezone 
from datetime import timedelta 
from django.contrib.auth.decorators import login_required 
from django.contrib import messages 

from crew_management.models import CrewMember 
from .forms import CrewMemberProfileForm, PrincipalForm, VesselForm, DocumentForm, ExperienceHistoryForm, NextOfKinForm, CommunicationLogForm, ProfessionalReferenceForm, AppraisalForm  

@login_required
def dashboard_view(request):
    today = timezone.now().date()

    # --- Crew Overview ---
    total_crew = CrewMember.objects.count()
    crew_by_status = CrewMember.objects.values('crew_status').annotate(count=Count('crew_status'))

    # Convert queryset result into a more friendly dictionary
    crew_status_counts = {item['crew_status']: item['count'] for item in crew_by_status}

    # Example: Ensure all statuses are present, even if count is 0
    all_status_choices = [choice[0] for choice in CrewMember.SEAFARER_STATUS_CHOICES]
    for status in all_status_choices:
        if status not in crew_status_counts:
            crew_status_counts[status] = 0

    # --- Document Expiry Alerts ---
    # Documents expiring within the next 6 months (approx 180 days)
    six_months_from_now = today + timedelta(days=180)
    expiring_documents = Document.objects.filter(
        expiry_date__gte=today, # Expiry date is today or in the future
        expiry_date__lte=six_months_from_now # Expiry date is within the next 6 months
    ).order_by('expiry_date')[:10] # Limit to top 10 most urgent for dashboard

    # Documents that have already expired
    expired_documents = Document.objects.filter(expiry_date__lt=today).order_by('-expiry_date')[:5] # Limit to 5 most recently expired

    # --- Upcoming Crew Changes (Sign-off alerts) ---
    # Relieving plans within the next 2 months (approx 60 days)
    two_months_from_now = today + timedelta(days=60)
    upcoming_signoffs = CrewMember.objects.filter(
        relieving_plan_date__gte=today,
        relieving_plan_date__lte=two_months_from_now
    ).order_by('relieving_plan_date')[:10] # Limit to top 10

    # --- Financial Snapshot (Placeholder for now) ---
    # Once you build detailed financial models (e.g., Allotment, RetirementDues),
    # you'd query them here. For now, we can use simple counts or mock values.
    # Example: Counting crew members with a 'principal' assigned
    crew_with_principal = CrewMember.objects.filter(principal__isnull=False).count()
    # total_monthly_allotments = YourAllotmentModel.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    # pending_retirement_dues = YourRetirementDuesModel.objects.filter(is_paid=False).aggregate(Sum('amount'))['amount__sum'] or 0


    context = {
        # Crew Overview
        'total_crew': total_crew,
        'crew_status_counts': crew_status_counts,

        # Document Alerts
        'expiring_documents': expiring_documents,
        'expired_documents': expired_documents,

        # Crew Changes
        'upcoming_signoffs': upcoming_signoffs,

        # Financial Snapshot (placeholders)
        'financial_summary_placeholder': f"Financial data will go here. {crew_with_principal} crew members have a principal assigned.",
    }
    return render(request, 'crew_management/dashboard.html', context)


@login_required
def crew_list(request):
    # --- Authorization Logic for Crew List ---
    if not request.user.is_staff:
        # If the user is NOT staff, they are not allowed to view the full list.
        # Raise a 404 (Page Not Found) or redirect them.
        raise Http404("You are not authorized to view the full crew roster.")
        # Alternatively, you could redirect:
        # messages.error(request, "You do not have permission to view the full crew roster.")
        # return redirect('dashboard') # or their own profile page

    crew_members = CrewMember.objects.all().order_by('first_name', 'last_name')

    context = {
        'crew_members': crew_members,
    }
    return render(request, 'crew_management/crew_list.html', context)


@login_required
def crew_profile_detail(request, pk):
    crew_member = get_object_or_404(CrewMember, pk=pk)

    # --- Authorization Logic ---
    # If the logged-in user is NOT staff, they can only view their OWN profile.
    if not request.user.is_staff:
        # Check if the logged-in user is the one linked to this CrewMember profile
        if not request.user == crew_member.user:
            raise Http404("You are not authorized to view this profile.")
    # --- End Authorization Logic ---

    context = {
        'crew': crew_member,
    }
    return render(request, 'crew_management/crew_profile_detail.html', context)


@login_required
def crew_profile_edit(request, pk):
    crew_member = get_object_or_404(CrewMember, pk=pk)

    # --- Authorization for Editing ---
    # A staff user can edit any profile.
    # A non-staff user (crew) can ONLY edit their own profile.
    if not request.user.is_staff:
        if not request.user == crew_member.user: # Check if logged-in user is the one linked to this profile
            raise Http404("You are not authorized to edit this profile.")
    # --- End Authorization ---

    if request.method == 'POST':
        # Populate the form with submitted data AND the existing instance
        # request.FILES is needed for file/image uploads
        form = CrewMemberProfileForm(request.POST, request.FILES, instance=crew_member)
        if form.is_valid():
            form.save() # Saves the changes to the database
            messages.success(request, "Your profile has been updated successfully!")
            # Redirect to the profile detail page after successful update
            return redirect('crew_profile_detail', pk=crew_member.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # For a GET request, create a form instance pre-filled with existing data
        form = CrewMemberProfileForm(instance=crew_member)

    context = {
        'crew': crew_member, # Still pass the crew member object for template context
        'form': form,
    }
    return render(request, 'crew_management/crew_profile_edit.html', context)


@login_required
def crew_create(request):
    # --- Authorization: Only staff users can create new crew members ---
    if not request.user.is_staff:
        raise Http404("You are not authorized to create new crew members.")
    # --- End Authorization ---

    if request.method == 'POST':
        # Create a form instance from POST data, including files
        form = CrewMemberProfileForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the new CrewMember instance
            new_crew_member = form.save()
            messages.success(request, f"Crew Member '{new_crew_member.first_name} {new_crew_member.last_name}' added successfully!")
            # Redirect to the detail page of the newly created crew member
            return redirect('crew_profile_detail', pk=new_crew_member.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # For a GET request, display an empty form
        form = CrewMemberProfileForm()

    context = {
        'form': form,
        'is_create_page': True, # A flag for the template to know it's a create page
    }
    return render(request, 'crew_management/crew_create.html', context)


@login_required
def crew_delete(request, pk):
    """
    Handles the deletion of a CrewMember record.
    Only accessible by staff users.
    Deletes the CrewMember and any related records that are set to CASCADE deletion.
    """
    crew_member = get_object_or_404(CrewMember, pk=pk)

    # Authorization: Only staff users can delete crew members
    if not request.user.is_staff:
        messages.error(request, "You are not authorized to delete crew members.")
        # Redirect to their own profile if unauthorized, or a generic unauthorized page
        if request.user.is_authenticated and hasattr(request.user, 'crew_profile') and request.user.crew_profile:
             return redirect('crew_profile_detail', pk=request.user.crew_profile.pk)
        return redirect('dashboard') # Fallback for unauthorized non-staff

    if request.method == 'GET': # Deletion triggered via a GET request from the button click
        # In a real application, a POST request with CSRF token is safer for deletion.
        # For this simple example, we're proceeding with GET as requested.
        try:
            crew_member.delete()
            messages.success(request, f"Crew Member '{crew_member.first_name} {crew_member.last_name}' (ID: {pk}) has been successfully deleted.")
        except Exception as e:
            messages.error(request, f"Error deleting Crew Member '{crew_member.first_name} {crew_member.last_name}': {e}")

    return redirect('crew_list') # Redirect back to the crew list after deletion attempt


@login_required
def export_crew_csv(request):
    # --- Authorization: Only staff users can export data ---
    if not request.user.is_staff:
        raise Http404("You are not authorized to export data.")
    # --- End Authorization ---

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="crew_members_export.csv"'

    writer = csv.writer(response)

    # Define the header row based on your CrewMember model fields
    # This should match the columns you want in your export, similar to your Excel template.
    # You'll need to manually list them here to ensure order and readability.
    writer.writerow([
        'ID', 'Seafarer Code', 'First Name', 'Last Name', 'Father Name', 
        'Date of Birth', 'Place of Birth', 'Marital Status', 'Nationality', 'City of Residence',
        'Address (Temporary)', 'Address (Permanent)', 'Phone No.', 'Mobile No.', 'Email ID', 'Skype ID',
        'Domestic Airport', 'Nearest International Airport', 'Current Rank', 'Date Joined Company',
        'Rank when First Joined', 'Principal', 'Crew Status', 'Performance Rating', 'Projected Next Sign-off Date',
        'Last Sign-off Date', 'Current Vessel', 'SSB No.', 'Client Name (for appraisal)',
        'Account Title', 'Account No.', 'Bank Name', 'Branch Name & Address', 'IBAN', 'SWIFT Code',
        'Height (ft)', 'Weight (kg)', 'Collar (cm)', 'Chest (cm)', 'Waist (cm)', 'Shoes (cm)',
        'Cap (cm)', 'Inseam (cm)', 'Working Gear Remarks'
        # Note: File fields (profile_picture, blank_cheque_leaf_copy) are not directly exported as content,
        # but you could export their paths if needed.
        # Relationship fields (user) are also not exported directly as object, but as their name/ID
    ])

    # Query all CrewMember objects
    crew_members = CrewMember.objects.all().order_by('id')

    # Write data rows
    for crew in crew_members:
        # For relationship fields (Principal, Vessel), get their names or unique identifiers
        principal_name = crew.principal.name if crew.principal else ''
        current_vessel_name = crew.current_vessel.name if crew.current_vessel else ''

        writer.writerow([
            crew.id, crew.seafarer_code, crew.first_name, crew.last_name, crew.father_name,
            crew.date_of_birth.strftime('%Y-%m-%d') if crew.date_of_birth else '', # Format date
            crew.place_of_birth, crew.marital_status, crew.nationality, crew.city_of_residence,
            crew.address_temporary, crew.address_permanent, crew.phone_no, crew.mobile_no,
            crew.email_id, crew.skype_id, crew.domestic_airport, crew.nearest_international_airport,
            crew.current_rank, crew.joined_in_company.strftime('%Y-%m-%d') if crew.joined_in_company else '',
            crew.joined_in_rank, principal_name, crew.crew_status,
            crew.performance_rating if crew.performance_rating is not None else '', # Handle None for numbers
            crew.relieving_plan_date.strftime('%Y-%m-%d') if crew.relieving_plan_date else '',
            crew.last_sign_off_date.strftime('%Y-%m-%d') if crew.last_sign_off_date else '',
            current_vessel_name, crew.ssb_no, crew.client_name_for_appraisal,
            crew.account_title, crew.account_no, crew.bank_name, crew.branch_name_address,
            crew.iban, crew.swift_code,
            crew.height_ft if crew.height_ft is not None else '',
            crew.weight_kg if crew.weight_kg is not None else '',
            crew.collar_cm if crew.collar_cm is not None else '',
            crew.chest_cm if crew.chest_cm is not None else '',
            crew.waist_cm if crew.waist_cm is not None else '',
            crew.shoes_cm if crew.shoes_cm is not None else '',
            crew.cap_cm if crew.cap_cm is not None else '',
            crew.inseam_cm if crew.inseam_cm is not None else '',
            crew.working_gear_remarks
        ])

    return response


@login_required
def import_crew_csv(request):
    # --- Authorization: Only staff users can import data ---
    if not request.user.is_staff:
        raise Http404("You are not authorized to import data.")
    # --- End Authorization ---

    if request.method == 'POST':
        if 'csv_file' not in request.FILES:
            messages.error(request, "No file uploaded. Please select a CSV file.")
            return redirect('import_crew_csv')

        csv_file = request.FILES['csv_file']

        # Check if it's a CSV file
        if not csv_file.name.endswith('.csv'):
            messages.error(request, "This is not a CSV file. Please upload a CSV file.")
            return redirect('import_crew_csv')

        # Read the CSV file content
        data_set = csv_file.read().decode('UTF-8')
        io_string = io.StringIO(data_set)
        # Skip the header row
        next(io_string)

        imported_count = 0
        updated_count = 0
        skipped_count = 0
        errors = []

        # Use csv.reader to parse the CSV
        for row in csv.reader(io_string, delimiter=','):
            if not row: # Skip empty rows
                skipped_count += 1
                continue

            # --- Map CSV columns to model fields ---
            # IMPORTANT: Adjust these indices (e.g., row[0], row[1]) based on your Excel sheet's column order
            # Refer to your "Excel Sheet 1: Crew Members (for CrewMember Model)" blueprint
            try:
                # Example mapping (adjust indices to match your CSV columns)
                # This is a sample mapping, replace with your actual column order from Excel
                seafarer_code = row[1].strip() # Assuming Seafarer Code is in the first column
                first_name = row[2].strip()
                last_name = row[3].strip()
                father_name = row[4].strip()
                date_of_birth_str = row[5].strip()
                place_of_birth = row[6].strip()
                marital_status = row[7].strip()
                nationality = row[8].strip()
                city_of_residence = row[9].strip()
                address_temporary = row[10].strip()
                address_permanent = row[11].strip()
                phone_no = row[12].strip()
                mobile_no = row[13].strip()
                email_id = row[14].strip()
                skype_id = row[15].strip()
                domestic_airport = row[16].strip()
                nearest_international_airport = row[17].strip()
                current_rank = row[18].strip()
                joined_in_company_str = row[19].strip()
                joined_in_rank = row[20].strip()
                principal_name = row[21].strip() # Principal Name for lookup
                crew_status = row[22].strip()
                performance_rating_str = row[23].strip()
                relieving_plan_date_str = row[24].strip()
                last_sign_off_date_str = row[25].strip()
                current_vessel_name = row[26].strip() # Current Vessel Name for lookup
                ssb_no = row[27].strip()
                client_name_for_appraisal = row[28].strip()
                account_title = row[29].strip()
                account_no = row[30].strip()
                bank_name = row[31].strip()
                branch_name_address = row[32].strip()
                iban = row[33].strip()
                swift_code = row[34].strip()
                height_ft_str = row[35].strip()
                weight_kg_str = row[36].strip()
                collar_cm_str = row[37].strip()
                chest_cm_str = row[38].strip()
                waist_cm_str = row[39].strip()
                shoes_cm_str = row[40].strip()
                cap_cm_str = row[41].strip()
                inseam_cm_str = row[42].strip()
                working_gear_remarks = row[43].strip()

                # Handle dates (YYYY-MM-DD format)
                date_of_birth = None
                if date_of_birth_str:
                    date_of_birth = timezone.datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
                joined_in_company = None
                if joined_in_company_str:
                    joined_in_company = timezone.datetime.strptime(joined_in_company_str, '%Y-%m-%d').date()
                relieving_plan_date = None
                if relieving_plan_date_str:
                    relieving_plan_date = timezone.datetime.strptime(relieving_plan_date_str, '%Y-%m-%d').date()
                last_sign_off_date = None
                if last_sign_off_date_str:
                    last_sign_off_date = timezone.datetime.strptime(last_sign_off_date_str, '%Y-%m-%d').date()

                # Handle numbers (convert empty strings to None for Decimal/Integer fields)
                performance_rating = int(performance_rating_str) if performance_rating_str else None
                height_ft = float(height_ft_str) if height_ft_str else None
                weight_kg = float(weight_kg_str) if weight_kg_str else None
                collar_cm = float(collar_cm_str) if collar_cm_str else None
                chest_cm = float(chest_cm_str) if chest_cm_str else None
                waist_cm = float(waist_cm_str) if waist_cm_str else None
                shoes_cm = float(shoes_cm_str) if shoes_cm_str else None
                cap_cm = float(cap_cm_str) if cap_cm_str else None
                inseam_cm = float(inseam_cm_str) if inseam_cm_str else None

                # Look up Principal and Vessel (by name/IMO for Principals/Vessels)
                # IMPORTANT: Ensure Principals and Vessels are imported FIRST, or exist in DB.
                principal_obj = None
                if principal_name:
                    try:
                        principal_obj = Principal.objects.get(name__iexact=principal_name) # Case-insensitive lookup
                    except Principal.DoesNotExist:
                        errors.append(f"Row skipped (Seafarer: {seafarer_code}): Principal '{principal_name}' not found.")
                        skipped_count += 1
                        continue # Skip this row if principal not found

                current_vessel_obj = None
                if current_vessel_name:
                    try:
                        # Assuming vessel name is sufficient, or you could use IMO number
                        current_vessel_obj = Vessel.objects.get(name__iexact=current_vessel_name)
                    except Vessel.DoesNotExist:
                        errors.append(f"Row skipped (Seafarer: {seafarer_code}): Vessel '{current_vessel_name}' not found.")
                        skipped_count += 1
                        continue # Skip this row if vessel not found

                # Try to get existing CrewMember or create a new one
                crew_member, created = CrewMember.objects.update_or_create(
                    seafarer_code=seafarer_code, # Use seafarer_code as the unique identifier for update_or_create
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'father_name': father_name,
                        'date_of_birth': date_of_birth,
                        'place_of_birth': place_of_birth,
                        'marital_status': marital_status,
                        'nationality': nationality,
                        'city_of_residence': city_of_residence,
                        'address_temporary': address_temporary,
                        'address_permanent': address_permanent,
                        'phone_no': phone_no,
                        'mobile_no': mobile_no,
                        'email_id': email_id,
                        'skype_id': skype_id,
                        'domestic_airport': domestic_airport,
                        'nearest_international_airport': nearest_international_airport,
                        'current_rank': current_rank,
                        'joined_in_company': joined_in_company,
                        'joined_in_rank': joined_in_rank,
                        'principal': principal_obj, # Assign the looked-up object
                        'crew_status': crew_status,
                        'performance_rating': performance_rating,
                        'relieving_plan_date': relieving_plan_date,
                        'last_sign_off_date': last_sign_off_date,
                        'current_vessel': current_vessel_obj, # Assign the looked-up object
                        'ssb_no': ssb_no,
                        'client_name_for_appraisal': client_name_for_appraisal,
                        'account_title': account_title,
                        'account_no': account_no,
                        'bank_name': bank_name,
                        'branch_name_address': branch_name_address,
                        'iban': iban,
                        'swift_code': swift_code,
                        'height_ft': height_ft,
                        'weight_kg': weight_kg,
                        'collar_cm': collar_cm,
                        'chest_cm': chest_cm,
                        'waist_cm': waist_cm,
                        'shoes_cm': shoes_cm,
                        'cap_cm': cap_cm,
                        'inseam_cm': inseam_cm,
                        'working_gear_remarks': working_gear_remarks,
                        # File fields (profile_picture, blank_cheque_leaf_copy) are complex to import from CSV
                        # You would need separate logic to link files based on names if needed.
                        # For initial import, leave them blank and upload via frontend later if required.
                        # 'profile_picture': ...
                        # 'blank_cheque_leaf_copy': ...
                    }
                )
                if created:
                    imported_count += 1
                else:
                    updated_count += 1

            except Exception as e:
                errors.append(f"Error importing row '{row}': {e}")
                skipped_count += 1

        if errors:
            messages.error(request, f"Import finished with errors: {len(errors)} rows skipped. See details below.")
            for err in errors[:5]: # Show first 5 errors on message
                messages.error(request, err)
            if len(errors) > 5:
                messages.error(request, "And more errors...")

        messages.success(request, f"Import complete: {imported_count} new crew members, {updated_count} updated, {skipped_count} skipped (including header).")
        return redirect('crew_list') # Redirect to crew list after import

    return render(request, 'crew_management/import_crew_csv.html')


# --- Principal Management Views ---
@login_required
def principal_list(request):
    # Only staff can view list of principals
    if not request.user.is_staff:
        raise Http404("You are not authorized to view this page.")

    principals = Principal.objects.all().order_by('name')
    context = {
        'principals': principals
    }
    return render(request, 'crew_management/principal_list.html', context)

@login_required
def principal_detail(request, pk):
    # Only staff can view principal details
    if not request.user.is_staff:
        raise Http404("You are not authorized to view this page.")

    principal = get_object_or_404(Principal, pk=pk)
    # Optionally, get vessels associated with this principal
    associated_vessels = principal.vessels.all() # Uses related_name defined in Vessel model

    context = {
        'principal': principal,
        'associated_vessels': associated_vessels
    }
    return render(request, 'crew_management/principal_detail.html', context)

@login_required
def principal_create(request):
    # Only staff can create new principals
    if not request.user.is_staff:
        raise Http404("You are not authorized to create principals.")

    if request.method == 'POST':
        form = PrincipalForm(request.POST)
        if form.is_valid():
            new_principal = form.save()
            messages.success(request, f"Principal '{new_principal.name}' added successfully!")
            return redirect('principal_detail', pk=new_principal.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PrincipalForm()

    context = {
        'form': form,
        'title': 'Add New Principal',
        'button_text': 'Add Principal'
    }
    return render(request, 'crew_management/principal_form.html', context)

@login_required
def principal_edit(request, pk):
    # Only staff can edit principals
    if not request.user.is_staff:
        raise Http404("You are not authorized to edit principals.")

    principal = get_object_or_404(Principal, pk=pk)

    if request.method == 'POST':
        form = PrincipalForm(request.POST, instance=principal)
        if form.is_valid():
            form.save()
            messages.success(request, f"Principal '{principal.name}' updated successfully!")
            return redirect('principal_detail', pk=principal.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PrincipalForm(instance=principal)

    context = {
        'form': form,
        'title': f'Edit Principal: {principal.name}',
        'button_text': 'Save Changes',
        'principal': principal # Pass principal object for back link
    }
    return render(request, 'crew_management/principal_form.html', context)

@login_required
def principal_delete(request, pk):
    """
    Handles the deletion of a Principal record.
    Only accessible by staff users.
    """
    principal = get_object_or_404(Principal, pk=pk)

    # Authorization: Only staff users can delete principals
    if not request.user.is_staff:
        messages.error(request, "You are not authorized to delete principals.")
        return redirect('principal_list') # Redirect back to the principals list

    if request.method == 'GET': # Deletion triggered via a GET request from the button click
        try:
            # Check for related objects before deleting (e.g., vessels associated with this principal)
            # Django's default CASCADE will delete related vessels/crew if configured.
            # You might want to add a check here if you prefer to prevent deletion if associated vessels/crew exist
            # For example:
            # if principal.vessels.exists():
            #    messages.error(request, f"Cannot delete Principal '{principal.name}' because it has associated vessels.")
            #    return redirect('principal_detail', pk=principal.pk)

            principal.delete()
            messages.success(request, f"Principal '{principal.name}' (ID: {pk}) has been successfully deleted.")
        except Exception as e:
            messages.error(request, f"Error deleting Principal '{principal.name}': {e}")

    return redirect('principal_list') # Redirect back to the principals list after deletion attempt

# --- Vessel Management Views ---
@login_required
def vessel_list(request):
    # Only staff can view list of vessels
    if not request.user.is_staff:
        raise Http404("You are not authorized to view this page.")

    vessels = Vessel.objects.all().order_by('name')
    context = {
        'vessels': vessels
    }
    return render(request, 'crew_management/vessel_list.html', context)

@login_required
def vessel_detail(request, pk):
    # Only staff can view vessel details
    if not request.user.is_staff:
        raise Http404("You are not authorized to view this page.")

    vessel = get_object_or_404(Vessel, pk=pk)
    # Optionally, get crew members currently on board this vessel
    crew_onboard = vessel.current_crew.all() # Uses related_name defined in CrewMember model

    context = {
        'vessel': vessel,
        'crew_onboard': crew_onboard
    }
    return render(request, 'crew_management/vessel_detail.html', context)

@login_required
def vessel_create(request):
    # Only staff can create new vessels
    if not request.user.is_staff:
        raise Http404("You are not authorized to create vessels.")

    if request.method == 'POST':
        form = VesselForm(request.POST)
        if form.is_valid():
            new_vessel = form.save()
            messages.success(request, f"Vessel '{new_vessel.name}' added successfully!")
            return redirect('vessel_detail', pk=new_vessel.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = VesselForm()

    context = {
        'form': form,
        'title': 'Add New Vessel',
        'button_text': 'Add Vessel'
    }
    return render(request, 'crew_management/vessel_form.html', context)

@login_required
def vessel_edit(request, pk):
    # Only staff can edit vessels
    if not request.user.is_staff:
        raise Http404("You are not authorized to edit vessels.")

    vessel = get_object_or_404(Vessel, pk=pk)

    if request.method == 'POST':
        form = VesselForm(request.POST, instance=vessel)
        if form.is_valid():
            form.save()
            messages.success(request, f"Vessel '{vessel.name}' updated successfully!")
            return redirect('vessel_detail', pk=vessel.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = VesselForm(instance=vessel)

    context = {
        'form': form,
        'title': f'Edit Vessel: {vessel.name}',
        'button_text': 'Save Changes',
        'vessel': vessel # Pass vessel object for back link
    }
    return render(request, 'crew_management/vessel_form.html', context)

@login_required
def vessel_delete(request, pk):
    """
    Handles the deletion of a Vessel record.
    Only accessible by staff users.
    """
    vessel = get_object_or_404(Vessel, pk=pk)

    # Authorization: Only staff users can delete vessels
    if not request.user.is_staff:
        messages.error(request, "You are not authorized to delete vessels.")
        return redirect('vessel_list') # Redirect back to the vessels list

    if request.method == 'GET': # Deletion triggered via a GET request from the button click
        try:
            # Check for related objects (CrewMembers assigned to this vessel)
            if vessel.current_crew.exists():
                messages.error(request, f"Cannot delete Vessel '{vessel.name}' because it has associated crew members.")
                return redirect('vessel_detail', pk=vessel.pk) # Redirect back to vessel detail if cannot delete

            vessel.delete()
            messages.success(request, f"Vessel '{vessel.name}' (ID: {pk}) has been successfully deleted.")
        except Exception as e:
            messages.error(request, f"Error deleting Vessel '{vessel.name}': {e}")

    return redirect('vessel_list') # Redirect back to the vessels list after deletion attempt

# --- Document Management Views ---
@login_required
def document_list_for_crew(request, crew_pk): # Takes crew_pk to list docs for a specific crew
    crew_member = get_object_or_404(CrewMember, pk=crew_pk)

    # Authorization: Staff can view all documents for any crew.
    # Crew can only view documents for their own profile.
    if not request.user.is_staff:
        if not request.user == crew_member.user:
            raise Http404("You are not authorized to view these documents.")

    documents = Document.objects.filter(crew_member=crew_member).order_by('document_name')

    context = {
        'crew': crew_member,
        'documents': documents
    }
    return render(request, 'crew_management/document_list_for_crew.html', context)

@login_required
def document_detail(request, pk): # Takes document pk
    document = get_object_or_404(Document, pk=pk)

    # Authorization: Staff can view any document.
    # Crew can only view documents linked to their own profile.
    if not request.user.is_staff:
        if not request.user == document.crew_member.user:
            raise Http404("You are not authorized to view this document.")

    context = {
        'document': document,
        'crew': document.crew_member # Pass the related crew member for breadcrumbs/back links
    }
    return render(request, 'crew_management/document_detail.html', context)

@login_required
def document_create(request, crew_pk): # Takes crew_pk to link new doc to a specific crew
    crew_member = get_object_or_404(CrewMember, pk=crew_pk)

    # Authorization: Staff can add documents for any crew.
    # Crew can only add documents for their own profile.
    if not request.user.is_staff:
        if not request.user == crew_member.user:
            raise Http404("You are not authorized to add documents for this profile.")

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            new_document = form.save(commit=False) # Create object but don't save to DB yet
            new_document.crew_member = crew_member # Assign the correct crew member
            new_document.save() # Now save to DB
            messages.success(request, f"Document '{new_document.document_name}' added successfully for {crew_member.first_name}.")
            return redirect('document_list_for_crew', crew_pk=crew_member.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = DocumentForm()

    context = {
        'form': form,
        'crew': crew_member,
        'title': f'Add New Document for {crew_member.first_name} {crew_member.last_name}',
        'button_text': 'Add Document'
    }
    return render(request, 'crew_management/document_form.html', context)

@login_required
def document_edit(request, pk): # Takes document pk to edit a specific document
    document = get_object_or_404(Document, pk=pk)
    crew_member = document.crew_member # Get the associated crew member

    # Authorization: Staff can edit any document.
    # Crew can only edit documents linked to their own profile.
    if not request.user.is_staff:
        if not request.user == crew_member.user:
            raise Http404("You are not authorized to edit this document.")

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            messages.success(request, f"Document '{document.document_name}' updated successfully.")
            return redirect('document_list_for_crew', crew_pk=crew_member.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = DocumentForm(instance=document)

    context = {
        'form': form,
        'document': document,
        'crew': crew_member,
        'title': f'Edit Document: {document.document_name}',
        'button_text': 'Save Changes'
    }
    return render(request, 'crew_management/document_form.html', context)


# --- Experience History Management Views ---
@login_required
def experience_list_for_crew(request, crew_pk): # Takes crew_pk to list experience for a specific crew
    crew_member = get_object_or_404(CrewMember, pk=crew_pk)

    # Authorization: Staff can view all experience for any crew.
    # Crew can only view experience for their own profile.
    if not request.user.is_staff:
        if not request.user == crew_member.user:
            raise Http404("You are not authorized to view this experience history.")

    experience_records = ExperienceHistory.objects.filter(crew_member=crew_member).order_by('-sign_on_date')

    context = {
        'crew': crew_member,
        'experience_records': experience_records
    }
    return render(request, 'crew_management/experience_list_for_crew.html', context)

@login_required
def experience_detail(request, pk): # Takes experience pk
    experience = get_object_or_404(ExperienceHistory, pk=pk)
    crew_member = experience.crew_member # Get the associated crew member

    # Authorization: Staff can view any experience.
    # Crew can only view experience linked to their own profile.
    if not request.user.is_staff:
        if not request.user == crew_member.user:
            raise Http404("You are not authorized to view this experience record.")

    context = {
        'experience': experience,
        'crew': crew_member
    }
    return render(request, 'crew_management/experience_detail.html', context)

@login_required
def experience_create(request, crew_pk): # Takes crew_pk to link new record to a specific crew
    crew_member = get_object_or_404(CrewMember, pk=crew_pk)

    # Authorization
    if not request.user.is_staff:
        if not request.user == crew_member.user:
            raise Http404("You are not authorized to add experience for this profile.")

    if request.method == 'POST':
        form = ExperienceHistoryForm(request.POST)
        if form.is_valid():
            new_experience = form.save(commit=False)
            new_experience.crew_member = crew_member # Assign the correct crew member
            new_experience.save()
            messages.success(request, f"Experience on '{new_experience.vessel_name}' added successfully for {crew_member.first_name}.")
            return redirect('experience_list_for_crew', crew_pk=crew_member.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ExperienceHistoryForm()

    context = {
        'form': form,
        'crew': crew_member,
        'title': f'Add New Experience for {crew_member.first_name} {crew_member.last_name}',
        'button_text': 'Add Experience Record'
    }
    return render(request, 'crew_management/experience_form.html', context)

@login_required
def experience_edit(request, pk): # Takes experience pk to edit a specific record
    experience = get_object_or_404(ExperienceHistory, pk=pk)
    crew_member = experience.crew_member # Get the associated crew member

    # Authorization: Staff can edit any experience.
    # Crew can only edit experience linked to their own profile.
    if not request.user.is_staff:
        if not request.user == crew_member.user:
            raise Http404("You are not authorized to edit this experience record.")

    if request.method == 'POST':
        form = ExperienceHistoryForm(request.POST, instance=experience)
        if form.is_valid():
            form.save()
            messages.success(request, f"Experience on '{experience.vessel.name}' updated successfully.")
            return redirect('experience_list_for_crew', crew_pk=crew_member.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ExperienceHistoryForm(instance=experience)

    context = {
        'form': form,
        'experience': experience,
        'crew': crew_member,
        'title': f'Edit Experience: {experience.vessel.name}',
        'button_text': 'Save Changes'
    }
    return render(request, 'crew_management/experience_form.html', context)


# --- Next of Kin Management Views ---
@login_required
def nextofkin_list_for_crew(request, crew_pk):
    crew_member = get_object_or_404(CrewMember, pk=crew_pk)

    # Authorization
    if not request.user.is_staff:
        if not request.user == crew_member.user:
            raise Http404("You are not authorized to view these Next of Kin records.")

    next_of_kins = NextOfKin.objects.filter(crew_member=crew_member).order_by('full_name')

    context = {
        'crew': crew_member,
        'next_of_kins': next_of_kins
    }
    return render(request, 'crew_management/nextofkin_list_for_crew.html', context)

@login_required
def nextofkin_detail(request, pk): # Takes nextofkin pk
    nextofkin = get_object_or_404(NextOfKin, pk=pk)
    crew_member = nextofkin.crew_member

    # Authorization
    if not request.user.is_staff:
        if not request.user == crew_member.user:
            raise Http404("You are not authorized to view this Next of Kin record.")

    context = {
        'nextofkin': nextofkin,
        'crew': crew_member
    }
    return render(request, 'crew_management/nextofkin_detail.html', context)

@login_required
def nextofkin_create(request, crew_pk):
    crew_member = get_object_or_404(CrewMember, pk=crew_pk)

    # Authorization
    if not request.user.is_staff:
        if not request.user == crew_member.user:
            raise Http404("You are not authorized to add Next of Kin records for this profile.")

    if request.method == 'POST':
        form = NextOfKinForm(request.POST, request.FILES) # Pass request.FILES for cnic_copy
        if form.is_valid():
            new_nextofkin = form.save(commit=False)
            new_nextofkin.crew_member = crew_member
            new_nextofkin.save()
            messages.success(request, f"Next of Kin '{new_nextofkin.full_name}' added successfully for {crew_member.first_name}.")
            return redirect('nextofkin_list_for_crew', crew_pk=crew_member.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = NextOfKinForm()

    context = {
        'form': form,
        'crew': crew_member,
        'title': f'Add Next of Kin for {crew_member.first_name} {crew_member.last_name}',
        'button_text': 'Add Next of Kin'
    }
    return render(request, 'crew_management/nextofkin_form.html', context)

@login_required
def nextofkin_edit(request, pk):
    nextofkin = get_object_or_404(NextOfKin, pk=pk)
    crew_member = nextofkin.crew_member

    # Authorization
    if not request.user.is_staff:
        if not request.user == crew_member.user:
            raise Http404("You are not authorized to edit this Next of Kin record.")

    if request.method == 'POST':
        form = NextOfKinForm(request.POST, request.FILES, instance=nextofkin) # Pass request.FILES
        if form.is_valid():
            form.save()
            messages.success(request, f"Next of Kin '{nextofkin.full_name}' updated successfully.")
            return redirect('nextofkin_list_for_crew', crew_pk=crew_member.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = NextOfKinForm(instance=nextofkin)

    context = {
        'form': form,
        'nextofkin': nextofkin,
        'crew': crew_member,
        'title': f'Edit Next of Kin: {nextofkin.full_name}',
        'button_text': 'Save Changes'
    }
    return render(request, 'crew_management/nextofkin_form.html', context)


# --- Communication Log Management Views ---
@login_required
def communicationlog_list_for_crew(request, crew_pk):
    crew_member = get_object_or_404(CrewMember, pk=crew_pk)

    # Authorization
    if not request.user.is_staff:
        if not request.user == crew_member.user:
            raise Http404("You are not authorized to view these communication logs.")

    logs = CommunicationLog.objects.filter(crew_member=crew_member).order_by('-date') # Ordered by date descending

    context = {
        'crew': crew_member,
        'logs': logs
    }
    return render(request, 'crew_management/communicationlog_list_for_crew.html', context)

@login_required
def communicationlog_detail(request, pk): # Takes log pk
    log = get_object_or_404(CommunicationLog, pk=pk)
    crew_member = log.crew_member

    # Authorization
    if not request.user.is_staff:
        if not request.user == crew_member.user:
            raise Http404("You are not authorized to view this communication log.")

    context = {
        'log': log,
        'crew': crew_member
    }
    return render(request, 'crew_management/communicationlog_detail.html', context)

@login_required
def communicationlog_create(request, crew_pk):
    crew_member = get_object_or_404(CrewMember, pk=crew_pk)

    # Authorization
    if not request.user.is_staff:
        if not request.user == crew_member.user:
            raise Http404("You are not authorized to add communication logs for this profile.")

    if request.method == 'POST':
        form = CommunicationLogForm(request.POST)
        if form.is_valid():
            new_log = form.save(commit=False)
            new_log.crew_member = crew_member
            # Optionally, auto-set user_name if it's supposed to be the logged-in user
            # new_log.user_name = request.user.username # Assuming user_name is the current logged-in user
            new_log.save()
            messages.success(request, f"Communication log for {new_log.contact_person_name} added successfully for {crew_member.first_name}.")
            return redirect('communicationlog_list_for_crew', crew_pk=crew_member.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # Pre-populate user_name with logged-in user if it's meant to be auto-filled
        initial_data = {'user_name': request.user.username} if not request.user.is_anonymous else {}
        form = CommunicationLogForm(initial=initial_data)

    context = {
        'form': form,
        'crew': crew_member,
        'title': f'Add Communication Log for {crew_member.first_name} {crew_member.last_name}',
        'button_text': 'Add Log Entry'
    }
    return render(request, 'crew_management/communicationlog_form.html', context)

@login_required
def communicationlog_edit(request, pk):
    log = get_object_or_404(CommunicationLog, pk=pk)
    crew_member = log.crew_member

    # Authorization
    if not request.user.is_staff:
        if not request.user == crew_member.user:
            raise Http404("You are not authorized to edit this communication log.")

    if request.method == 'POST':
        form = CommunicationLogForm(request.POST, instance=log)
        if form.is_valid():
            form.save()
            messages.success(request, f"Communication log for {log.contact_person_name} updated successfully.")
            return redirect('communicationlog_list_for_crew', crew_pk=crew_member.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CommunicationLogForm(instance=log)

    context = {
        'form': form,
        'log': log,
        'crew': crew_member,
        'title': f'Edit Communication Log: {log.contact_person_name}',
        'button_text': 'Save Changes'
    }
    return render(request, 'crew_management/communicationlog_form.html', context)


# --- Professional Reference Management Views ---
@login_required
def professionalreference_list_for_crew(request, crew_pk):
    crew_member = get_object_or_404(CrewMember, pk=crew_pk)

    # Authorization
    if not request.user.is_staff:
        if not request.user == crew_member.user:
            raise Http404("You are not authorized to view these professional references.")

    references = ProfessionalReference.objects.filter(crew_member=crew_member).order_by('company_name')

    context = {
        'crew': crew_member,
        'references': references
    }
    return render(request, 'crew_management/professionalreference_list_for_crew.html', context)

@login_required
def professionalreference_detail(request, pk): # Takes reference pk
    reference = get_object_or_404(ProfessionalReference, pk=pk)
    crew_member = reference.crew_member

    # Authorization
    if not request.user.is_staff:
        if not request.user == crew_member.user:
            raise Http404("You are not authorized to view this professional reference.")

    context = {
        'reference': reference,
        'crew': crew_member
    }
    return render(request, 'crew_management/professionalreference_detail.html', context)

@login_required
def professionalreference_create(request, crew_pk):
    crew_member = get_object_or_404(CrewMember, pk=crew_pk)

    # Authorization
    if not request.user.is_staff:
        if not request.user == crew_member.user:
            raise Http404("You are not authorized to add professional references for this profile.")

    if request.method == 'POST':
        form = ProfessionalReferenceForm(request.POST)
        if form.is_valid():
            new_reference = form.save(commit=False)
            new_reference.crew_member = crew_member
            new_reference.save() # Date field will be auto_now_add
            messages.success(request, f"Professional Reference '{new_reference.contact_person}' added successfully for {crew_member.first_name}.")
            return redirect('professionalreference_list_for_crew', crew_pk=crew_member.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProfessionalReferenceForm()

    context = {
        'form': form,
        'crew': crew_member,
        'title': f'Add Professional Reference for {crew_member.first_name} {crew_member.last_name}',
        'button_text': 'Add Reference'
    }
    return render(request, 'crew_management/professionalreference_form.html', context)

@login_required
def professionalreference_edit(request, pk):
    reference = get_object_or_404(ProfessionalReference, pk=pk)
    crew_member = reference.crew_member

    # Authorization
    if not request.user.is_staff:
        if not request.user == crew_member.user:
            raise Http404("You are not authorized to edit this professional reference.")

    if request.method == 'POST':
        form = ProfessionalReferenceForm(request.POST, instance=reference)
        if form.is_valid():
            form.save()
            messages.success(request, f"Professional Reference '{reference.contact_person}' updated successfully.")
            return redirect('professionalreference_list_for_crew', crew_pk=crew_member.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProfessionalReferenceForm(instance=reference)

    context = {
        'form': form,
        'reference': reference,
        'crew': crew_member,
        'title': f'Edit Professional Reference: {reference.contact_person}',
        'button_text': 'Save Changes'
    }
    return render(request, 'crew_management/professionalreference_form.html', context)

@login_required
def appraisal_list_for_crew(request, crew_pk):
    crew_member = get_object_or_404(CrewMember, pk=crew_pk)

    # Authorization
    if not request.user.is_staff:
        if not request.user == crew_member.user:
            raise Http404("You are not authorized to view these appraisals.")

    appraisals = Appraisal.objects.filter(crew_member=crew_member).order_by('-evaluation_date')

    context = {
        'crew': crew_member,
        'appraisals': appraisals
    }
    return render(request, 'crew_management/appraisal_list_for_crew.html', context)

@login_required
def appraisal_detail(request, pk): # Takes appraisal pk
    appraisal = get_object_or_404(Appraisal, pk=pk)
    crew_member = appraisal.crew_member

    # Authorization
    if not request.user.is_staff:
        if not request.user == crew_member.user:
            raise Http404("You are not authorized to view this appraisal.")

    context = {
        'appraisal': appraisal,
        'crew': crew_member
    }
    return render(request, 'crew_management/appraisal_detail.html', context)

@login_required
def appraisal_create(request, crew_pk):
    crew_member = get_object_or_404(CrewMember, pk=crew_pk)

    # Authorization
    if not request.user.is_staff:
        if not request.user == crew_member.user:
            raise Http404("You are not authorized to add appraisals for this profile.")

    if request.method == 'POST':
        form = AppraisalForm(request.POST)
        if form.is_valid():
            new_appraisal = form.save(commit=False)
            new_appraisal.crew_member = crew_member
            # Auto-fill fields if they are meant to be auto-appearing based on crew/vessel
            # new_appraisal.seafarer_name = f"{crew_member.first_name} {crew_member.last_name}" # Example, if this wasn't a @property
            # new_appraisal.ssb_no = crew_member.ssb_no # Example
            # new_appraisal.client_name = crew_member.client_name_for_appraisal # Example
            new_appraisal.save()
            messages.success(request, f"Appraisal for {new_appraisal.vessel.name if new_appraisal.vessel else 'N/A Vessel'} added successfully for {crew_member.first_name}.")
            return redirect('appraisal_list_for_crew', crew_pk=crew_member.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        # Optionally pre-fill vessel with current_vessel if it's the most common case
        initial_data = {}
        if crew_member.current_vessel:
            initial_data['vessel'] = crew_member.current_vessel.pk
        form = AppraisalForm(initial=initial_data)

    context = {
        'form': form,
        'crew': crew_member,
        'title': f'Add Appraisal for {crew_member.first_name} {crew_member.last_name}',
        'button_text': 'Add Appraisal'
    }
    return render(request, 'crew_management/appraisal_form.html', context)

@login_required
def appraisal_edit(request, pk):
    appraisal = get_object_or_404(Appraisal, pk=pk)
    crew_member = appraisal.crew_member

    # Authorization
    if not request.user.is_staff:
        if not request.user == crew_member.user:
            raise Http404("You are not authorized to edit this appraisal.")

    if request.method == 'POST':
        form = AppraisalForm(request.POST, instance=appraisal)
        if form.is_valid():
            form.save()
            messages.success(request, f"Appraisal for {appraisal.vessel.name if appraisal.vessel else 'N/A Vessel'} updated successfully.")
            return redirect('appraisal_list_for_crew', crew_pk=crew_member.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AppraisalForm(instance=appraisal)

    context = {
        'form': form,
        'appraisal': appraisal,
        'crew': crew_member,
        'title': f'Edit Appraisal: {appraisal.vessel.name if appraisal.vessel else "N/A Vessel"}',
        'button_text': 'Save Changes'
    }
    return render(request, 'crew_management/appraisal_form.html', context)
