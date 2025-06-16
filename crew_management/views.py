# crew_management/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.db import models
import csv
import io
import datetime
from django.utils import timezone
import json # Make sure this is imported if not already

# Corrected: Import User from django.contrib.auth.models
from django.contrib.auth.models import User

# Import your models based on the provided models.py
from .models import (
    CrewMember, Principal, Vessel, Document,
    ExperienceHistory, NextOfKin, CommunicationLog,
    ProfessionalReference, Appraisal, AuditLog # Ensure AuditLog is imported
)

# Import your forms (from forms.py)
from .forms import (
    CrewMemberProfileForm, PrincipalForm, VesselForm, DocumentForm,
    ExperienceHistoryForm, NextOfKinForm, CommunicationLogForm,
    ProfessionalReferenceForm, AppraisalForm
)

# Helper function to check if user is staff
def is_staff(user):
    return user.is_staff

# NEW: Helper function to check if user is a superuser
def is_superuser_only(user):
    return user.is_superuser

def create_audit_log(user, action_type, model_instance=None, description="", ip_address=None, changes=None):
    """
    Helper function to create an AuditLog entry.
    """
    model_name = model_instance.__class__.__name__ if model_instance else None
    record_id = model_instance.pk if model_instance else None

    # Get IP address from request if not provided
    # Note: request object is not directly available here, but REMOTE_ADDR is often in request.META.
    # For a comprehensive solution, consider a custom middleware to attach IP to request.user.
    # For now, if called from a view, request.META.get('REMOTE_ADDR') is passed directly.
    
    AuditLog.objects.create(
        user=user,
        action_type=action_type,
        timestamp=timezone.now(), # Ensure timestamp is explicitly set here
        model_name=model_name,
        record_id=record_id,
        description=description,
        ip_address=ip_address,
        changes=changes
    )

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, f"Welcome, {user.username}!")

            # Log login via signal in apps.py, no direct call here
            # (assuming apps.py signals are correctly set up)

            if user.is_staff:
                return redirect('dashboard')
            else:
                try:
                    crew_profile = CrewMember.objects.get(user=user)
                    return redirect('crew_profile_detail', pk=crew_profile.pk)
                except CrewMember.DoesNotExist:
                    messages.warning(request, "Your user account is not linked to a crew profile. Please contact support.")
                    auth_logout(request)
                    return redirect('login')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    # Log logout via signal in apps.py
    auth_logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

# --- Dashboard View ---
@login_required
def dashboard(request):
    total_crew = CrewMember.objects.count()
    crew_by_status_query = CrewMember.objects.values('crew_status').annotate(count=models.Count('crew_status'))
    crew_status_counts = {item['crew_status']: item['count'] for item in crew_by_status_query}

    today = datetime.date.today()
    three_months_from_now = today + datetime.timedelta(days=90)
    six_months_from_now = today + datetime.timedelta(days=180)


    # Document Expiry Alerts (Expiring within 3 months)
    expiring_documents = Document.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=three_months_from_now
    ).order_by('expiry_date')[:10]

    expired_documents = Document.objects.filter(
        expiry_date__lt=today
    ).order_by('-expiry_date')[:10]

    # Upcoming Crew Changes (based on relieving_plan_date from CrewMember, next 6 months)
    upcoming_sign_offs = CrewMember.objects.filter(
        relieving_plan_date__gte=today,
        relieving_plan_date__lte=six_months_from_now
    ).order_by('relieving_plan_date')[:10]

    context = {
        'total_crew': total_crew,
        'crew_status_counts': crew_status_counts,
        'expiring_documents': expiring_documents,
        'expired_documents': expired_documents,
        'upcoming_sign_offs': upcoming_sign_offs,
        'financial_summary_placeholder': 'Financial snapshot data will appear here.',
    }
    return render(request, 'crew_management/dashboard.html', context)

# --- Crew Management Views ---

@login_required
def crew_list(request):
    crew_members = CrewMember.objects.all().order_by('first_name', 'last_name')
    return render(request, 'crew_management/crew_list.html', {'crew_members': crew_members})

@login_required
@user_passes_test(is_staff)
def crew_create(request):
    if request.method == 'POST':
        form = CrewMemberProfileForm(request.POST, request.FILES)
        if form.is_valid():
            crew_member_instance = form.save()
            messages.success(request, "New Crew Member added successfully!")
            create_audit_log(
                request.user,
                'CREATE',
                model_instance=crew_member_instance,
                description=f"Created Crew Member: {crew_member_instance.first_name} {crew_member_instance.last_name} (Code: {crew_member_instance.seafarer_code}).",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return redirect('crew_list')
        else:
            messages.error(request, "Error adding crew member. Please check the form.")
    else:
        form = CrewMemberProfileForm()

    context = {
        'form': form,
        'title': "Add New Crew Member",
        'button_text': "Add Crew Member",
    }
    return render(request, 'crew_management/crew_create.html', context)

@login_required
def crew_profile_detail(request, pk):
    crew_member = get_object_or_404(CrewMember, pk=pk)
    if not request.user.is_staff and (not crew_member.user or crew_member.user != request.user):
        messages.error(request, "You are not authorized to view this profile.")
        return redirect('dashboard')
    return render(request, 'crew_management/crew_profile_detail.html', {'crew_member': crew_member})

@login_required
@user_passes_test(is_staff)
def crew_profile_edit(request, pk):
    crew_member = get_object_or_404(CrewMember, pk=pk)
    if request.method == 'POST':
        # Capture initial state for diffing
        initial_data = {field.name: getattr(crew_member, field.name) for field in crew_member._meta.fields if field.name not in ['id', 'user', 'created_at', 'updated_at', 'profile_picture', 'blank_cheque_leaf_copy']}

        form = CrewMemberProfileForm(request.POST, request.FILES, instance=crew_member)
        if form.is_valid():
            updated_instance = form.save()
            messages.success(request, f"Profile for {crew_member.first_name} {crew_member.last_name} updated successfully!")

            # Generate detailed changes for audit log
            changed_fields_detail = {}
            for field_name, new_value in form.cleaned_data.items():
                if field_name not in ['id', 'user', 'created_at', 'updated_at', 'profile_picture', 'blank_cheque_leaf_copy']:
                    old_value = initial_data.get(field_name) # Retrieve old value
                    # Handle Foreign Keys (display name instead of ID)
                    if hasattr(form.fields[field_name], 'queryset') and form.fields[field_name].queryset.model in [Principal, Vessel]:
                        old_obj = form.fields[field_name].queryset.model.objects.filter(pk=old_value).first()
                        new_obj = form.fields[field_name].queryset.model.objects.filter(pk=new_value.pk).first() if new_value else None
                        old_value_display = str(old_obj) if old_obj else 'None'
                        new_value_display = str(new_obj) if new_obj else 'None'
                    else:
                        old_value_display = str(old_value)
                        new_value_display = str(new_value)

                    if old_value != new_value:
                        changed_fields_detail[field_name] = {
                            'old': old_value_display,
                            'new': new_value_display
                        }

            description_parts = [f"Updated Crew Member: {updated_instance.first_name} {updated_instance.last_name} (Code: {updated_instance.seafarer_code})."]
            if changed_fields_detail:
                description_parts.append("Changes:")
                for field, values in changed_fields_detail.items():
                    description_parts.append(f"  {field}: '{values['old']}' -> '{values['new']}'")
            else:
                description_parts.append("No significant data changes detected.")

            create_audit_log(
                request.user,
                'UPDATE',
                model_instance=updated_instance,
                description="\n".join(description_parts),
                ip_address=request.META.get('REMOTE_ADDR'),
                changes=changed_fields_detail
            )
            return redirect('crew_profile_detail', pk=crew_member.pk)
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = CrewMemberProfileForm(instance=crew_member)

    context = {
        'crew_member': crew_member,
        'form': form,
        'title': f"Edit Profile for {crew_member.first_name} {crew_member.last_name}",
        'button_text': "Save Changes",
    }
    return render(request, 'crew_management/crew_profile_edit.html', context)


@login_required
@user_passes_test(is_staff)
def crew_delete(request, pk):
    crew_member = get_object_or_404(CrewMember, pk=pk)
    if request.method == 'POST' or request.method == 'GET':
        create_audit_log(
            request.user,
            'DELETE',
            model_instance=crew_member,
            description=f"Deleted Crew Member: {crew_member.first_name} {crew_member.last_name} (Code: {crew_member.seafarer_code}).",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        crew_member.delete()
        messages.success(request, f"Crew member '{crew_member.first_name} {crew_member.last_name}' deleted successfully.")
    else:
        messages.warning(request, "Deletion requires a POST request. Please confirm deletion via the provided button/form.")
    return redirect('crew_list')

@login_required
@user_passes_test(is_staff)
def import_crew_csv(request):
    if request.method == 'POST':
        if 'csv_file' in request.FILES:
            csv_file = request.FILES['csv_file']
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'This is not a CSV file. Please upload a CSV file.')
                return redirect('import_crew_csv')

            data_set = csv_file.read().decode('UTF-8')
            io_string = io.StringIO(data_set)
            try:
                header = next(io_string)
            except StopIteration:
                messages.error(request, 'CSV file is empty.')
                return redirect('import_crew_csv')

            reader = csv.reader(io_string, delimiter=',')

            imported_count = 0
            updated_count = 0
            errors = []

            def parse_date_safe(date_str, field_name, row_num):
                if date_str:
                    try:
                        return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        try:
                            return datetime.datetime.strptime(date_str, '%d-%m-%Y').date()
                        except ValueError:
                            errors.append(f"Row {row_num}: Invalid '{field_name}' date format ('{date_str}'). Expected YYYY-MM-DD or DD-MM-YYYY.")
                            return None
                return None

            expected_min_columns = 43

            for row_num, row in enumerate(reader, start=2):
                if not row or not row[0].strip():
                    if row and not row[0].strip():
                         errors.append(f"Row {row_num}: Seafarer Code is missing. Skipping row.")
                    continue

                if len(row) < expected_min_columns:
                    errors.append(f"Row {row_num}: Not enough columns ({len(row)} provided, at least {expected_min_columns} expected). Skipping row.")
                    continue

                try:
                    seafarer_code = row[0].strip()
                    if not seafarer_code:
                        errors.append(f"Row {row_num}: Seafarer Code is missing. Skipping row.")
                        continue

                    principal_name = row[20].strip() if len(row) > 20 else ''
                    principal_obj = None
                    if principal_name:
                        try:
                            principal_obj = Principal.objects.get(name__iexact=principal_name)
                        except Principal.DoesNotExist:
                            errors.append(f"Row {row_num}: Principal '{principal_name}' not found for crew '{seafarer_code}'. Please import or create it first. Skipping crew member.")
                            continue

                    vessel_name = row[41].strip() if len(row) > 41 else ''
                    vessel_obj = None
                    if vessel_name:
                        try:
                            vessel_obj = Vessel.objects.get(name__iexact=vessel_name)
                        except Vessel.DoesNotExist:
                            errors.append(f"Row {row_num}: Vessel '{vessel_name}' not found for crew '{seafarer_code}'. Please import or create it first. Skipping crew member.")
                            continue


                    crew_member_data = {
                        'first_name': row[1].strip(),
                        'last_name': row[2].strip(),
                        'father_name': row[3].strip(),
                        'date_of_birth': parse_date_safe(row[4].strip(), 'date_of_birth', row_num),
                        'place_of_birth': row[5].strip(),
                        'marital_status': row[6].strip(),
                        'nationality': row[7].strip(),
                        'city_of_residence': row[8].strip(),
                        'address_temporary': row[9].strip(),
                        'address_permanent': row[10].strip(),
                        'phone_no': row[11].strip(),
                        'mobile_no': row[12].strip(),
                        'email_id': row[13].strip(),
                        'skype_id': row[14].strip(),
                        'domestic_airport': row[15].strip(),
                        'nearest_international_airport': row[16].strip(),
                        'current_rank': row[17].strip(),
                        'joined_in_company': parse_date_safe(row[18].strip(), 'joined_in_company', row_num),
                        'joined_in_rank': row[19].strip(),
                        'principal': principal_obj,
                        'crew_status': row[21].strip(),
                        'performance_rating': int(float(row[22].strip())) if row[22].strip() and row[22].strip().replace('.', '', 1).isdigit() else None,
                        'relieving_plan_date': parse_date_safe(row[23].strip(), 'relieving_plan_date', row_num),
                        'last_sign_off_date': parse_date_safe(row[24].strip(), 'last_sign_off_date', row_num),
                        'ssb_no': row[25].strip(),
                        'client_name_for_appraisal': row[26].strip(),
                        'account_title': row[27].strip(),
                        'account_no': row[28].strip(),
                        'bank_name': row[29].strip(),
                        'branch_name_address': row[30].strip(),
                        'iban': row[31].strip(),
                        'swift_code': row[32].strip(),
                        'height_ft': float(row[33].strip()) if row[33].strip() else None,
                        'weight_kg': float(row[34].strip()) if row[34].strip() else None,
                        'collar_cm': float(row[35].strip()) if row[35].strip() else None,
                        'chest_cm': float(row[36].strip()) if row[36].strip() else None,
                        'waist_cm': float(row[37].strip()) if row[37].strip() else None,
                        'shoes_cm': float(row[38].strip()) if row[38].strip() else None,
                        'cap_cm': float(row[39].strip()) if row[39].strip() else None,
                        'inseam_cm': float(row[40].strip()) if row[40].strip() else None,
                        'current_vessel': vessel_obj,
                        'working_gear_remarks': row[42].strip() if len(row) > 42 else '',
                    }

                    for key in ['date_of_birth', 'joined_in_company', 'relieving_plan_date', 'last_sign_off_date']:
                        if crew_member_data[key] is None:
                            del crew_member_data[key]

                    temp_form = CrewMemberProfileForm(crew_member_data)
                    if temp_form.is_valid():
                        crew_obj, created = CrewMember.objects.update_or_create(
                            seafarer_code=seafarer_code,
                            defaults=temp_form.cleaned_data
                        )
                        if created:
                            imported_count += 1
                            create_audit_log(
                                request.user,
                                'CREATE',
                                model_instance=crew_obj,
                                description=f"Imported new Crew Member: {crew_obj.first_name} {crew_obj.last_name} (Code: {crew_obj.seafarer_code}).",
                                ip_address=request.META.get('REMOTE_ADDR')
                            )
                        else:
                            updated_count += 1
                            create_audit_log(
                                request.user,
                                'UPDATE',
                                model_instance=crew_obj,
                                description=f"Updated existing Crew Member via import: {crew_obj.first_name} {crew_obj.last_name} (Code: {crew_obj.seafarer_code}).",
                                # For import, detailed changes are harder to log without tracking previous state for each row
                                ip_address=request.META.get('REMOTE_ADDR')
                            )
                    else:
                        error_messages = "; ".join([f"{k}: {', '.join(v)}" for k, v in temp_form.errors.items()])
                        errors.append(f"Row {row_num}: Validation error for '{seafarer_code}': {error_messages}. Row content: {row[:5]}...")


                except IndexError:
                    errors.append(f"Row {row_num}: CSV row has fewer columns than expected or columns are out of order. Please check the template. Row content: {row}")
                except ValueError as ve:
                    errors.append(f"Row {row_num}: Data type conversion error for '{seafarer_code}': {ve}. Ensure numeric fields are numbers and dates are valid. Row content: {row[:5]}...")
                except Exception as e:
                    errors.append(f"Row {row_num}: Unexpected error processing row for '{seafarer_code}': {e}. Row content: {row[:5]}...")

            if imported_count > 0:
                messages.success(request, f'{imported_count} new crew members imported successfully!')
            if updated_count > 0:
                messages.info(request, f'{updated_count} existing crew members updated successfully!')
            if errors:
                display_errors = errors[:5]
                for error in display_errors:
                    messages.error(request, error)
                if len(errors) > 5:
                    messages.error(request, f'And {len(errors) - 5} more errors. Check your CSV file for details.')
                messages.warning(request, f'Total issues encountered: {len(errors)}.')

            return redirect('crew_list')

        else:
            messages.error(request, 'No file uploaded.')
            return redirect('import_crew_csv')
    return render(request, 'crew_management/import_crew_csv.html')

@login_required
@user_passes_test(is_staff)
def export_crew_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="crew_members_export_' + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'seafarer_code', 'first_name', 'last_name', 'father_name', 'date_of_birth',
        'place_of_birth', 'marital_status', 'nationality', 'city_of_residence',
        'address_temporary', 'address_permanent', 'phone_no', 'mobile_no',
        'email_id', 'skype_id', 'domestic_airport', 'nearest_international_airport',
        'current_rank', 'joined_in_company', 'joined_in_rank', 'principal_name',
        'crew_status', 'performance_rating', 'relieving_plan_date', 'last_sign_off_date',
        'ssb_no', 'client_name_for_appraisal',
        'account_title', 'account_no', 'bank_name', 'branch_name_address', 'iban', 'swift_code',
        'height_ft', 'weight_kg', 'collar_cm', 'chest_cm', 'waist_cm',
        'shoes_cm', 'cap_cm', 'inseam_cm', 'current_vessel_name', 'working_gear_remarks'
    ])

    crew_members = CrewMember.objects.all().order_by('last_name', 'first_name')

    for crew in crew_members:
        writer.writerow([
            crew.seafarer_code,
            crew.first_name,
            crew.last_name,
            crew.father_name,
            crew.date_of_birth.strftime('%Y-%m-%d') if crew.date_of_birth else '',
            crew.place_of_birth,
            crew.marital_status,
            crew.nationality,
            crew.city_of_residence,
            crew.address_temporary,
            crew.address_permanent,
            crew.phone_no,
            crew.mobile_no,
            crew.email_id,
            crew.skype_id,
            crew.domestic_airport,
            crew.nearest_international_airport,
            crew.current_rank,
            crew.joined_in_company.strftime('%Y-%m-%d') if crew.joined_in_company else '',
            crew.joined_in_rank,
            crew.principal.name if crew.principal else '',
            crew.crew_status,
            crew.performance_rating if crew.performance_rating is not None else '',
            crew.relieving_plan_date.strftime('%Y-%m-%d') if crew.relieving_plan_date else '',
            crew.last_sign_off_date.strftime('%Y-%m-%d') if crew.last_sign_off_date else '',
            crew.ssb_no,
            crew.client_name_for_appraisal,
            crew.account_title,
            crew.account_no,
            crew.bank_name,
            crew.branch_name_address,
            crew.iban,
            crew.swift_code,
            crew.height_ft if crew.height_ft is not None else '',
            crew.weight_kg if crew.weight_kg is not None else '',
            crew.collar_cm if crew.collar_cm is not None else '',
            crew.chest_cm if crew.chest_cm is not None else '',
            crew.waist_cm if crew.waist_cm is not None else '',
            crew.shoes_cm if crew.shoes_cm is not None else '',
            crew.cap_cm if crew.cap_cm is not None else '',
            crew.inseam_cm if crew.inseam_cm is not None else '',
            crew.current_vessel.name if crew.current_vessel else '',
            crew.working_gear_remarks,
        ])
    create_audit_log(
        request.user,
        'EXPORT',
        description=f"Exported Crew Members CSV.",
        ip_address=request.META.get('REMOTE_ADDR')
    )
    return response

# --- Principal Management Views ---

@login_required
def principal_list(request):
    principals = Principal.objects.all().order_by('name')
    return render(request, 'crew_management/principal_list.html', {'principals': principals})

@login_required
@user_passes_test(is_staff)
def principal_create(request):
    if request.method == 'POST':
        form = PrincipalForm(request.POST)
        if form.is_valid():
            principal_instance = form.save()
            messages.success(request, "Principal added successfully!")
            create_audit_log(
                request.user,
                'CREATE',
                model_instance=principal_instance,
                description=f"Created Principal: {principal_instance.name}.",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return redirect('principal_list')
        else:
            messages.error(request, "Error adding principal. Please check the form.")
    else:
        form = PrincipalForm()

    context = {
        'form': form,
        'title': "Add New Principal",
        'button_text': "Add Principal",
    }
    return render(request, 'crew_management/principal_form.html', context)

@login_required
def principal_detail(request, pk):
    principal = get_object_or_404(Principal, pk=pk)
    associated_vessels = Vessel.objects.filter(associated_principal=principal).order_by('name')
    return render(request, 'crew_management/principal_detail.html', {'principal': principal, 'associated_vessels': associated_vessels})

@login_required
@user_passes_test(is_staff)
def principal_edit(request, pk):
    principal = get_object_or_404(Principal, pk=pk)
    if request.method == 'POST':
        initial_data = {field.name: getattr(principal, field.name) for field in principal._meta.fields if field.name not in ['id', 'remarks']} # Exclude remarks for simpler diff
        form = PrincipalForm(request.POST, instance=principal)
        if form.is_valid():
            updated_instance = form.save()
            messages.success(request, f"Principal '{principal.name}' updated successfully!")

            changed_fields_detail = {}
            for field_name, new_value in form.cleaned_data.items():
                if field_name not in ['id', 'remarks']:
                    old_value = initial_data.get(field_name)
                    if old_value != new_value:
                        changed_fields_detail[field_name] = {
                            'old': str(old_value),
                            'new': str(new_value)
                        }

            description_parts = [f"Updated Principal: {updated_instance.name}."]
            if changed_fields_detail:
                description_parts.append("Changes:")
                for field, values in changed_fields_detail.items():
                    description_parts.append(f"  {field}: '{values['old']}' -> '{values['new']}'")
            else:
                description_parts.append("No significant data changes detected.")

            create_audit_log(
                request.user,
                'UPDATE',
                model_instance=updated_instance,
                description="\n".join(description_parts),
                ip_address=request.META.get('REMOTE_ADDR'),
                changes=changed_fields_detail
            )
            return redirect('principal_detail', pk=principal.pk)
        else:
            messages.error(request, "Error updating principal. Please check the form.")
    else:
        form = PrincipalForm(instance=principal)

    context = {
        'form': form,
        'principal': principal,
        'title': f"Edit Principal: {principal.name}",
        'button_text': "Save Changes",
    }
    return render(request, 'crew_management/principal_form.html', context)

@login_required
@user_passes_test(is_staff)
def principal_delete(request, pk):
    principal = get_object_or_404(Principal, pk=pk)
    if CrewMember.objects.filter(principal=principal).exists():
        messages.error(request, f"Cannot delete Principal '{principal.name}' as there are crew members directly associated with it.")
        return redirect('principal_list')
    if Vessel.objects.filter(associated_principal=principal).exists():
        messages.error(request, f"Cannot delete Principal '{principal.name}' as there are vessels associated with it.")
        return redirect('principal_list')

    if request.method == 'POST' or request.method == 'GET':
        create_audit_log(
            request.user,
            'DELETE',
            model_instance=principal,
            description=f"Deleted Principal: {principal.name}.",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        principal.delete()
        messages.success(request, f"Principal '{principal.name}' deleted successfully.")
    else:
        messages.warning(request, "Deletion requires a GET or POST request. Please confirm deletion via the provided button/form.")
    return redirect('principal_list')

@login_required
@user_passes_test(is_staff)
def import_principal_csv(request):
    if request.method == 'POST':
        if 'csv_file' in request.FILES:
            csv_file = request.FILES['csv_file']
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'This is not a CSV file. Please upload a CSV file.')
                return redirect('import_principal_csv')

            data_set = csv_file.read().decode('UTF-8')
            io_string = io.StringIO(data_set)
            try:
                header = next(io_string)
            except StopIteration:
                messages.error(request, 'CSV file is empty.')
                return redirect('import_principal_csv')

            reader = csv.reader(io_string, delimiter=',')

            imported_count = 0
            updated_count = 0
            errors = []

            for row_num, row in enumerate(reader, start=2):
                if not row or not row[0].strip():
                    if row and not row[0].strip():
                        errors.append(f"Row {row_num}: Principal Name is missing. Skipping row.")
                    continue

                if len(row) < 1:
                    errors.append(f"Row {row_num}: Not enough columns for Principal (at least 1 expected for name). Skipping row.")
                    continue

                try:
                    principal_name = row[0].strip()

                    contact_person = row[1].strip() if len(row) > 1 and row[1].strip() else None
                    email = row[2].strip() if len(row) > 2 and row[2].strip() else None
                    phone = row[3].strip() if len(row) > 3 and row[3].strip() else None
                    address = row[4].strip() if len(row) > 4 and row[4].strip() else None
                    remarks = row[5].strip() if len(row) > 5 and row[5].strip() else None


                    principal_data = {
                        'contact_person': contact_person,
                        'email': email,
                        'phone': phone,
                        'address': address,
                        'remarks': remarks,
                    }

                    temp_form = PrincipalForm(principal_data)
                    if temp_form.is_valid():
                        principal, created = Principal.objects.update_or_create(
                            name=principal_name,
                            defaults=temp_form.cleaned_data
                        )
                        if created:
                            imported_count += 1
                            create_audit_log(
                                request.user,
                                'CREATE',
                                model_instance=principal,
                                description=f"Imported new Principal: {principal.name}.",
                                ip_address=request.META.get('REMOTE_ADDR')
                            )
                        else:
                            updated_count += 1
                            create_audit_log(
                                request.user,
                                'UPDATE',
                                model_instance=principal,
                                description=f"Updated existing Principal via import: {principal.name}.",
                                ip_address=request.META.get('REMOTE_ADDR')
                            )
                    else:
                        error_messages = "; ".join([f"{k}: {', '.join(v)}" for k, v in temp_form.errors.items()])
                        errors.append(f"Row {row_num}: Validation error for '{principal_name}': {error_messages}. Row content: {row[:5]}...")


                except Exception as e:
                    errors.append(f'Row {row_num}: Error processing row for "{row[0].strip() if row else "N/A"}": {e}')

            if imported_count > 0:
                messages.success(request, f'{imported_count} new principals imported successfully!')
            if updated_count > 0:
                messages.info(request, f'{updated_count} existing principals updated successfully!')
            if errors:
                display_errors = errors[:5]
                for error in display_errors:
                    messages.error(request, error)
                if len(errors) > 5:
                    messages.error(request, f'And {len(errors) - 5} more errors. Check your CSV file for details.')
                messages.warning(request, f'Total issues encountered: {len(errors)}.')

            return redirect('principal_list')

        else:
            messages.error(request, 'No file uploaded.')
            return redirect('import_principal_csv')
    return render(request, 'crew_management/import_principal_csv.html')

@login_required
@user_passes_test(is_staff)
def export_principal_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="principals_export_' + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Contact Person', 'Email', 'Phone', 'Address', 'Remarks'])

    principals = Principal.objects.all().order_by('name')

    for principal in principals:
        writer.writerow([
            principal.name,
            principal.contact_person if principal.contact_person else '',
            principal.email if principal.email else '',
            principal.phone if principal.phone else '',
            principal.address if principal.address else '',
            principal.remarks if principal.remarks else '',
        ])
    create_audit_log(
        request.user,
        'EXPORT',
        description=f"Exported Principals CSV.",
        ip_address=request.META.get('REMOTE_ADDR')
    )
    return response

# --- Vessel Management Views ---

@login_required
def vessel_list(request):
    vessels = Vessel.objects.all().order_by('name')
    return render(request, 'crew_management/vessel_list.html', {'vessels': vessels})

@login_required
@user_passes_test(is_staff)
def vessel_create(request):
    if request.method == 'POST':
        form = VesselForm(request.POST)
        if form.is_valid():
            vessel_instance = form.save()
            messages.success(request, "Vessel added successfully!")
            create_audit_log(
                request.user,
                'CREATE',
                model_instance=vessel_instance,
                description=f"Created Vessel: {vessel_instance.name} (IMO: {vessel_instance.imo_number}).",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return redirect('vessel_list')
        else:
            messages.error(request, "Error adding vessel. Please check the form.")
    else:
        form = VesselForm()

    context = {
        'form': form,
        'title': "Add New Vessel",
        'button_text': "Add Vessel",
    }
    return render(request, 'crew_management/vessel_form.html', context)

@login_required
def vessel_detail(request, pk):
    vessel = get_object_or_404(Vessel, pk=pk)
    crew_onboard = CrewMember.objects.filter(current_vessel=vessel).order_by('last_name', 'first_name')
    return render(request, 'crew_management/vessel_detail.html', {'vessel': vessel, 'crew_onboard': crew_onboard})


@login_required
@user_passes_test(is_staff)
def vessel_edit(request, pk):
    vessel = get_object_or_404(Vessel, pk=pk)
    if request.method == 'POST':
        initial_data = {field.name: getattr(vessel, field.name) for field in vessel._meta.fields if field.name not in ['id']}
        form = VesselForm(request.POST, instance=vessel)
        if form.is_valid():
            updated_instance = form.save()
            messages.success(request, f"Vessel '{vessel.name}' updated successfully!")

            changed_fields_detail = {}
            for field_name, new_value in form.cleaned_data.items():
                if field_name not in ['id']:
                    old_value = initial_data.get(field_name)
                    if field_name == 'associated_principal': # Handle FK
                        old_value_display = str(Principal.objects.filter(pk=old_value).first()) if old_value else 'None'
                        new_value_display = str(new_value) if new_value else 'None'
                    else:
                        old_value_display = str(old_value)
                        new_value_display = str(new_value)

                    if old_value != new_value:
                        changed_fields_detail[field_name] = {
                            'old': old_value_display,
                            'new': new_value_display
                        }

            description_parts = [f"Updated Vessel: {updated_instance.name} (IMO: {updated_instance.imo_number})."]
            if changed_fields_detail:
                description_parts.append("Changes:")
                for field, values in changed_fields_detail.items():
                    description_parts.append(f"  {field}: '{values['old']}' -> '{values['new']}'")
            else:
                description_parts.append("No significant data changes detected.")

            create_audit_log(
                request.user,
                'UPDATE',
                model_instance=updated_instance,
                description="\n".join(description_parts),
                ip_address=request.META.get('REMOTE_ADDR'),
                changes=changed_fields_detail
            )
            return redirect('vessel_detail', pk=vessel.pk)
        else:
            messages.error(request, "Error updating vessel. Please check the form.")
    else:
        form = VesselForm(instance=vessel)

    context = {
        'form': form,
        'vessel': vessel,
        'title': f"Edit Vessel: {vessel.name}",
        'button_text': "Save Changes",
    }
    return render(request, 'crew_management/vessel_form.html', context)


@login_required
@user_passes_test(is_staff)
def vessel_delete(request, pk):
    vessel = get_object_or_404(Vessel, pk=pk)
    if CrewMember.objects.filter(current_vessel=vessel).exists():
        messages.error(request, f"Cannot delete vessel '{vessel.name}' as there are crew members assigned to it.")
        return redirect('vessel_list')

    if request.method == 'POST' or request.method == 'GET':
        create_audit_log(
            request.user,
            'DELETE',
            model_instance=vessel,
            description=f"Deleted Vessel: {vessel.name} (IMO: {vessel.imo_number}).",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        vessel.delete()
        messages.success(request, f"Vessel '{vessel.name}' deleted successfully.")
    else:
        messages.warning(request, "Deletion requires a POST request. Please confirm deletion via the provided button/form.")
    return redirect('vessel_list')


@login_required
@user_passes_test(is_staff)
def import_vessel_csv(request):
    if request.method == 'POST':
        if 'csv_file' in request.FILES:
            csv_file = request.FILES['csv_file']
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'This is not a CSV file. Please upload a CSV file.')
                return redirect('import_vessel_csv')

            data_set = csv_file.read().decode('UTF-8')
            io_string = io.StringIO(data_set)
            try:
                header = next(io_string)
            except StopIteration:
                messages.error(request, 'CSV file is empty.')
                return redirect('import_vessel_csv')

            reader = csv.reader(io_string, delimiter=',')

            imported_count = 0
            updated_count = 0
            errors = []

            for row_num, row in enumerate(reader, start=2):
                if not row or not row[0].strip():
                    if row and not row[0].strip():
                        errors.append(f"Row {row_num}: Vessel Name is missing. Skipping row.")
                    continue

                if len(row) < 2:
                    errors.append(f"Row {row_num}: Not enough columns for Vessel (at least 2 expected for name and IMO). Skipping row.")
                    continue

                try:
                    vessel_name = row[0].strip()
                    imo_number = row[1].strip()

                    principal_name = row[4].strip() if len(row) > 4 and row[4].strip() else None
                    principal_obj = None
                    if principal_name:
                        try:
                            principal_obj = Principal.objects.get(name__iexact=principal_name)
                        except Principal.DoesNotExist:
                            errors.append(f"Row {row_num}: Principal '{principal_name}' not found for vessel '{vessel_name}'. Please import or create it first. Skipping vessel.")
                            continue

                    vessel_data = {
                        'name': vessel_name,
                        'imo_number': imo_number,
                        'vessel_type': row[2].strip() if len(row) > 2 else '',
                        'flag_state': row[3].strip() if len(row) > 3 else '',
                        'associated_principal': principal_obj,
                    }
                    temp_form = VesselForm(vessel_data)
                    if temp_form.is_valid():
                        vessel, created = Vessel.objects.update_or_create(
                            imo_number=imo_number,
                            defaults=temp_form.cleaned_data
                        )
                        if created:
                            imported_count += 1
                            create_audit_log(
                                request.user,
                                'CREATE',
                                model_instance=vessel,
                                description=f"Imported new Vessel: {vessel.name} (IMO: {vessel.imo_number}).",
                                ip_address=request.META.get('REMOTE_ADDR')
                            )
                        else:
                            updated_count += 1
                            create_audit_log(
                                request.user,
                                'UPDATE',
                                model_instance=vessel,
                                description=f"Updated existing Vessel via import: {vessel.name} (IMO: {vessel.imo_number}).",
                                ip_address=request.META.get('REMOTE_ADDR')
                            )
                    else:
                        error_messages = "; ".join([f"{k}: {', '.join(v)}" for k, v in temp_form.errors.items()])
                        errors.append(f"Row {row_num}: Validation error for '{vessel_name}': {error_messages}. Row content: {row[:5]}...")


                except Exception as e:
                    errors.append(f'Row {row_num}: Error processing row for "{row[0].strip() if row else "N/A"}": {e}')

            if imported_count > 0:
                messages.success(request, f'{imported_count} new vessels imported successfully!')
            if updated_count > 0:
                messages.info(request, f'{updated_count} existing vessels updated successfully!')
            if errors:
                display_errors = errors[:5]
                for error in display_errors:
                    messages.error(request, error)
                if len(errors) > 5:
                    messages.error(request, f'And {len(errors) - 5} more errors. Check your CSV file for details.')
                messages.warning(request, f'Total issues encountered: {len(errors)}.')

            return redirect('vessel_list')

        else:
            messages.error(request, 'No file uploaded.')
            return redirect('import_vessel_csv')
    return render(request, 'crew_management/import_vessel_csv.html')

@login_required
@user_passes_test(is_staff)
def export_vessel_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="vessels_export_' + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + '.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'IMO Number', 'Vessel Type', 'Flag State', 'Principal Name'])

    vessels = Vessel.objects.all().order_by('name')

    for vessel in vessels:
        writer.writerow([
            vessel.name,
            vessel.imo_number if vessel.imo_number else '',
            vessel.vessel_type if vessel.vessel_type else '',
            vessel.flag_state if vessel.flag_state else '',
            vessel.associated_principal.name if vessel.associated_principal else '',
        ])
    create_audit_log(
        request.user,
        'EXPORT',
        description=f"Exported Vessels CSV.",
        ip_address=request.META.get('REMOTE_ADDR')
    )
    return response

# --- Document Management Views ---

@login_required
def crew_document_list(request, pk):
    crew_member = get_object_or_404(CrewMember, pk=pk)
    if not request.user.is_staff and (not crew_member.user or crew_member.user != request.user):
        messages.error(request, "You are not authorized to view documents for this profile.")
        return redirect('dashboard')
    documents = Document.objects.filter(crew_member=crew_member).order_by('document_type', 'expiry_date')
    return render(request, 'crew_management/document_list_for_crew.html', {'crew_member': crew_member, 'documents': documents})

@login_required
@user_passes_test(is_staff)
def crew_document_add(request, pk):
    crew_member = get_object_or_404(CrewMember, pk=pk)
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.crew_member = crew_member
            document.save()
            messages.success(request, f"Document '{document.document_name}' added successfully for {crew_member.first_name}.")
            create_audit_log(
                request.user,
                'CREATE',
                model_instance=document,
                description=f"Added Document '{document.document_name}' for {crew_member.first_name} {crew_member.last_name}.",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return redirect('crew_document_list', pk=crew_member.pk)
        else:
            messages.error(request, "Error adding document. Please check the form.")
    else:
        form = DocumentForm()

    context = {
        'form': form,
        'crew_member': crew_member,
        'title': f"Add Document for {crew_member.first_name} {crew_member.last_name}",
        'button_text': "Add Document",
    }
    return render(request, 'crew_management/document_form.html', context)


@login_required
def document_detail(request, pk):
    document = get_object_or_404(Document, pk=pk)
    crew_member = document.crew_member
    if not request.user.is_staff and (not crew_member.user or crew_member.user != request.user):
        messages.error(request, "You are not authorized to view this document.")
        return redirect('dashboard')
    return render(request, 'crew_management/document_detail.html', {'document': document, 'crew_member': crew_member})


@login_required
@user_passes_test(is_staff)
def document_edit(request, pk):
    document = get_object_or_404(Document, pk=pk)
    crew_member = document.crew_member
    if request.method == 'POST':
        # Initial data capture (excluding file fields for simpler diffing)
        initial_data = {field.name: getattr(document, field.name) for field in document._meta.fields if field.name not in ['id', 'crew_member', 'document_file', 'created_at', 'updated_at']}

        form = DocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            updated_instance = form.save()
            messages.success(request, f"Document '{document.document_name}' updated successfully!")

            changed_fields_detail = {}
            for field_name, new_value in form.cleaned_data.items():
                if field_name not in ['id', 'crew_member', 'document_file', 'created_at', 'updated_at']:
                    old_value = initial_data.get(field_name)
                    # For Date fields, ensure comparison is type-consistent
                    if isinstance(old_value, datetime.date) and isinstance(new_value, datetime.date):
                        pass # direct comparison is fine
                    elif isinstance(old_value, models.fields.files.ImageFieldFile) or isinstance(new_value, models.fields.files.ImageFieldFile):
                        # File fields require special handling, might just log "file uploaded/changed"
                        # For now, if file field is not in 'excluded', it will be compared as path
                        pass
                    if old_value != new_value:
                        changed_fields_detail[field_name] = {
                            'old': str(old_value),
                            'new': str(new_value)
                        }

            description_parts = [f"Updated Document '{updated_instance.document_name}' for {crew_member.first_name} {crew_member.last_name}."]
            if changed_fields_detail:
                description_parts.append("Changes:")
                for field, values in changed_fields_detail.items():
                    description_parts.append(f"  {field}: '{values['old']}' -> '{values['new']}'")
            else:
                description_parts.append("No significant data changes detected.")

            create_audit_log(
                request.user,
                'UPDATE',
                model_instance=updated_instance,
                description="\n".join(description_parts),
                ip_address=request.META.get('REMOTE_ADDR'),
                changes=changed_fields_detail
            )
            return redirect('document_detail', pk=document.pk)
        else:
            messages.error(request, "Error updating document. Please check the form.")
    else:
        form = DocumentForm(instance=document)

    context = {
        'form': form,
        'document': document,
        'crew_member': crew_member,
        'title': f"Edit Document: {document.document_name}",
        'button_text': "Save Changes",
    }
    return render(request, 'crew_management/document_form.html', context)


@login_required
@user_passes_test(is_staff)
def document_delete(request, pk):
    document = get_object_or_404(Document, pk=pk)
    crew_pk = document.crew_member.pk
    if request.method == 'POST' or request.method == 'GET':
        create_audit_log(
            request.user,
            'DELETE',
            model_instance=document,
            description=f"Deleted Document '{document.document_name}' for {document.crew_member.first_name} {document.crew_member.last_name}.",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        document.delete()
        messages.success(request, f"Document '{document.document_name}' deleted successfully.")
    else:
        messages.warning(request, "Deletion requires a POST request. Please confirm deletion via the provided button/form.")
    return redirect('crew_document_list', pk=crew_pk)


# --- Experience History Management Views ---

@login_required
def crew_experience_list(request, crew_pk):
    crew_member = get_object_or_404(CrewMember, pk=crew_pk)
    if not request.user.is_staff and (not crew_member.user or crew_member.user != request.user):
        messages.error(request, "You are not authorized to view this profile's experience history.")
        return redirect('dashboard')
    experiences = ExperienceHistory.objects.filter(crew_member=crew_member).order_by('-sign_on_date')
    return render(request, 'crew_management/experience_list_for_crew.html', {'crew': crew_member, 'experiences': experiences})


@login_required
@user_passes_test(is_staff)
def experience_add(request, crew_pk):
    crew_member = get_object_or_404(CrewMember, pk=crew_pk)
    if request.method == 'POST':
        form = ExperienceHistoryForm(request.POST)
        if form.is_valid():
            experience = form.save(commit=False)
            experience.crew_member = crew_member
            experience.save()
            messages.success(request, f"Experience record added successfully for {crew_member.first_name}.")
            create_audit_log(
                request.user,
                'CREATE',
                model_instance=experience,
                description=f"Added Experience record for {crew_member.first_name} {crew_member.last_name} on vessel '{experience.vessel_name}'.",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return redirect('crew_experience_list', crew_pk=crew_member.pk)
        else:
            messages.error(request, "Error adding experience record. Please check the form.")
    else:
        form = ExperienceHistoryForm()

    context = {
        'form': form,
        'crew': crew_member,
        'title': f"Add Experience for {crew_member.first_name} {crew_member.last_name}",
        'button_text': "Add Record",
    }
    return render(request, 'crew_management/experience_form.html', context)


@login_required
def experience_detail(request, pk):
    experience = get_object_or_404(ExperienceHistory, pk=pk)
    crew_member = experience.crew_member
    if not request.user.is_staff and (not crew_member.user or crew_member.user != request.user):
        messages.error(request, "You are not authorized to view this experience record.")
        return redirect('dashboard')
    return render(request, 'crew_management/experience_detail.html', {'experience': experience, 'crew': crew_member})


@login_required
@user_passes_test(is_staff)
def experience_edit(request, pk):
    experience = get_object_or_404(ExperienceHistory, pk=pk)
    crew_member = experience.crew_member
    if request.method == 'POST':
        initial_data = {field.name: getattr(experience, field.name) for field in experience._meta.fields if field.name not in ['id', 'crew_member']}
        form = ExperienceHistoryForm(request.POST, instance=experience)
        if form.is_valid():
            updated_instance = form.save()
            messages.success(request, f"Experience record for {experience.vessel_name} updated successfully!")

            changed_fields_detail = {}
            for field_name, new_value in form.cleaned_data.items():
                if field_name not in ['id', 'crew_member']:
                    old_value = initial_data.get(field_name)
                    if old_value != new_value:
                        changed_fields_detail[field_name] = {
                            'old': str(old_value),
                            'new': str(new_value)
                        }

            description_parts = [f"Updated Experience record for {crew_member.first_name} {crew_member.last_name} on vessel '{updated_instance.vessel_name}'."]
            if changed_fields_detail:
                description_parts.append("Changes:")
                for field, values in changed_fields_detail.items():
                    description_parts.append(f"  {field}: '{values['old']}' -> '{values['new']}'")
            else:
                description_parts.append("No significant data changes detected.")

            create_audit_log(
                request.user,
                'UPDATE',
                model_instance=updated_instance,
                description="\n".join(description_parts),
                ip_address=request.META.get('REMOTE_ADDR'),
                changes=changed_fields_detail
            )
            return redirect('experience_detail', pk=experience.pk)
        else:
            messages.error(request, "Error updating experience record. Please check the form.")
    else:
        form = ExperienceHistoryForm(instance=experience)

    context = {
        'form': form,
        'experience': experience,
        'crew': crew_member,
        'title': f"Edit Experience for {crew_member.first_name} {crew_member.last_name}",
        'button_text': "Save Changes",
    }
    return render(request, 'crew_management/experience_form.html', context)


@login_required
@user_passes_test(is_staff)
def experience_delete(request, pk):
    experience = get_object_or_404(ExperienceHistory, pk=pk)
    crew_pk = experience.crew_member.pk
    if request.method == 'POST' or request.method == 'GET':
        create_audit_log(
            request.user,
            'DELETE',
            model_instance=experience,
            description=f"Deleted Experience record for {experience.crew_member.first_name} {experience.crew_member.last_name} on vessel '{experience.vessel_name}'.",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        experience.delete()
        messages.success(request, "Experience record deleted successfully.")
    else:
        messages.warning(request, "Deletion requires a POST request.")
    return redirect('crew_experience_list', crew_pk=crew_pk)


# --- Next of Kin Management Views ---

@login_required
def crew_nextofkin_list(request, crew_pk):
    crew_member = get_object_or_404(CrewMember, pk=crew_pk)
    if not request.user.is_staff and (not crew_member.user or crew_member.user != request.user):
        messages.error(request, "You are not authorized to view this profile's next of kin records.")
        return redirect('dashboard')
    next_of_kins = NextOfKin.objects.filter(crew_member=crew_member).order_by('full_name')
    return render(request, 'crew_management/nextofkin_list_for_crew.html', {'crew': crew_member, 'next_of_kins': next_of_kins})


@login_required
@user_passes_test(is_staff)
def nextofkin_add(request, crew_pk):
    crew_member = get_object_or_404(CrewMember, pk=crew_pk)
    if request.method == 'POST':
        form = NextOfKinForm(request.POST, request.FILES)
        if form.is_valid():
            nextofkin = form.save(commit=False)
            nextofkin.crew_member = crew_member
            nextofkin.save()
            messages.success(request, f"Next of Kin record added successfully for {crew_member.first_name}.")
            create_audit_log(
                request.user,
                'CREATE',
                model_instance=nextofkin,
                description=f"Added Next of Kin '{nextofkin.full_name}' for {crew_member.first_name} {crew_member.last_name}.",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return redirect('crew_nextofkin_list', crew_pk=crew_member.pk)
        else:
            messages.error(request, "Error adding Next of Kin record. Please check the form.")
    else:
        form = NextOfKinForm()

    context = {
        'form': form,
        'crew': crew_member,
        'title': f"Add Next of Kin for {crew_member.first_name} {crew_member.last_name}",
        'button_text': "Add Record",
    }
    return render(request, 'crew_management/nextofkin_form.html', context)


@login_required
def nextofkin_detail(request, pk):
    nextofkin = get_object_or_404(NextOfKin, pk=pk)
    crew_member = nextofkin.crew_member
    if not request.user.is_staff and (not crew_member.user or crew_member.user != request.user):
        messages.error(request, "You are not authorized to view this next of kin record.")
        return redirect('dashboard')
    return render(request, 'crew_management/nextofkin_detail.html', {'nextofkin': nextofkin, 'crew': crew_member})


@login_required
@user_passes_test(is_staff)
def nextofkin_edit(request, pk):
    nextofkin = get_object_or_404(NextOfKin, pk=pk)
    crew_member = nextofkin.crew_member
    if request.method == 'POST':
        initial_data = {field.name: getattr(nextofkin, field.name) for field in nextofkin._meta.fields if field.name not in ['id', 'crew_member', 'cnic_copy']}
        form = NextOfKinForm(request.POST, request.FILES, instance=nextofkin)
        if form.is_valid():
            updated_instance = form.save()
            messages.success(request, f"Next of Kin record for {nextofkin.full_name} updated successfully!")

            changed_fields_detail = {}
            for field_name, new_value in form.cleaned_data.items():
                if field_name not in ['id', 'crew_member', 'cnic_copy']:
                    old_value = initial_data.get(field_name)
                    if old_value != new_value:
                        changed_fields_detail[field_name] = {
                            'old': str(old_value),
                            'new': str(new_value)
                        }

            description_parts = [f"Updated Next of Kin '{updated_instance.full_name}' for {crew_member.first_name} {crew_member.last_name}."]
            if changed_fields_detail:
                description_parts.append("Changes:")
                for field, values in changed_fields_detail.items():
                    description_parts.append(f"  {field}: '{values['old']}' -> '{values['new']}'")
            else:
                description_parts.append("No significant data changes detected.")

            create_audit_log(
                request.user,
                'UPDATE',
                model_instance=updated_instance,
                description="\n".join(description_parts),
                ip_address=request.META.get('REMOTE_ADDR'),
                changes=changed_fields_detail
            )
            return redirect('nextofkin_detail', pk=nextofkin.pk)
        else:
            messages.error(request, "Error updating Next of Kin record. Please check the form.")
    else:
        form = NextOfKinForm(instance=nextofkin)

    context = {
        'form': form,
        'nextofkin': nextofkin,
        'crew': crew_member,
        'title': f"Edit Next of Kin for {crew_member.first_name} {crew_member.last_name}",
        'button_text': "Save Changes",
    }
    return render(request, 'crew_management/nextofkin_form.html', context)


@login_required
@user_passes_test(is_staff)
def nextofkin_delete(request, pk):
    nextofkin = get_object_or_404(NextOfKin, pk=pk)
    crew_pk = nextofkin.crew_member.pk
    if request.method == 'POST' or request.method == 'GET':
        create_audit_log(
            request.user,
            'DELETE',
            model_instance=nextofkin,
            description=f"Deleted Next of Kin '{nextofkin.full_name}' for {nextofkin.crew_member.first_name} {nextofkin.crew_member.last_name}.",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        nextofkin.delete()
        messages.success(request, "Next of Kin record deleted successfully.")
    else:
        messages.warning(request, "Deletion requires a POST request.")
    return redirect('crew_nextofkin_list', crew_pk=crew_pk)


# --- Communication Log Management Views ---

@login_required
def crew_communication_log_list(request, crew_pk):
    crew_member = get_object_or_404(CrewMember, pk=crew_pk)
    if not request.user.is_staff and (not crew_member.user or crew_member.user != request.user):
        messages.error(request, "You are not authorized to view this profile's communication logs.")
        return redirect('dashboard')
    logs = CommunicationLog.objects.filter(crew_member=crew_member).order_by('-date')
    return render(request, 'crew_management/communicationlog_list_for_crew.html', {'crew': crew_member, 'logs': logs})


@login_required
@user_passes_test(is_staff)
def communicationlog_add(request, crew_pk):
    crew_member = get_object_or_404(CrewMember, pk=crew_pk)
    if request.method == 'POST':
        form = CommunicationLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.crew_member = crew_member
            log.user_name = request.user.username
            log.save()
            messages.success(request, f"Communication log added successfully for {crew_member.first_name}.")
            create_audit_log(
                request.user,
                'CREATE',
                model_instance=log,
                description=f"Added Communication Log for {crew_member.first_name} {crew_member.last_name} (Purpose: {log.purpose_of_call}).",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return redirect('crew_communication_log_list', crew_pk=crew_member.pk)
        else:
            messages.error(request, "Error adding communication log. Please check the form.")
    else:
        form = CommunicationLogForm()

    context = {
        'form': form,
        'crew': crew_member,
        'title': f"Add Communication Log for {crew_member.first_name} {crew_member.last_name}",
        'button_text': "Add Log Entry",
    }
    return render(request, 'crew_management/communicationlog_form.html', context)


@login_required
def communicationlog_detail(request, pk):
    log = get_object_or_404(CommunicationLog, pk=pk)
    crew_member = log.crew_member
    if not request.user.is_staff and (not crew_member.user or crew_member.user != request.user):
        messages.error(request, "You are not authorized to view this communication log.")
        return redirect('dashboard')
    return render(request, 'crew_management/communicationlog_detail.html', {'log': log, 'crew': crew_member})


@login_required
@user_passes_test(is_staff)
def communicationlog_edit(request, pk):
    log = get_object_or_404(CommunicationLog, pk=pk)
    crew_member = log.crew_member
    if request.method == 'POST':
        initial_data = {field.name: getattr(log, field.name) for field in log._meta.fields if field.name not in ['id', 'crew_member', 'user_name', 'date']} # Exclude auto/read-only fields
        form = CommunicationLogForm(request.POST, instance=log)
        if form.is_valid():
            updated_instance = form.save()
            messages.success(request, f"Communication log for {log.contact_person_name} updated successfully!")

            changed_fields_detail = {}
            for field_name, new_value in form.cleaned_data.items():
                if field_name not in ['id', 'crew_member', 'user_name', 'date']:
                    old_value = initial_data.get(field_name)
                    if old_value != new_value:
                        changed_fields_detail[field_name] = {
                            'old': str(old_value),
                            'new': str(new_value)
                        }

            description_parts = [f"Updated Communication Log for {crew_member.first_name} {crew_member.last_name} (Contact: {updated_instance.contact_person_name})."]
            if changed_fields_detail:
                description_parts.append("Changes:")
                for field, values in changed_fields_detail.items():
                    description_parts.append(f"  {field}: '{values['old']}' -> '{values['new']}'")
            else:
                description_parts.append("No significant data changes detected.")

            create_audit_log(
                request.user,
                'UPDATE',
                model_instance=updated_instance,
                description="\n".join(description_parts),
                ip_address=request.META.get('REMOTE_ADDR'),
                changes=changed_fields_detail
            )
            return redirect('communicationlog_detail', pk=log.pk)
        else:
            messages.error(request, "Error updating communication log. Please check the form.")
    else:
        form = CommunicationLogForm(instance=log)

    context = {
        'form': form,
        'log': log,
        'crew': crew_member,
        'title': f"Edit Communication Log for {crew_member.first_name} {crew_member.last_name}",
        'button_text': "Save Changes",
    }
    return render(request, 'crew_management/communicationlog_form.html', context)


@login_required
@user_passes_test(is_staff)
def communicationlog_delete(request, pk):
    log = get_object_or_404(CommunicationLog, pk=pk)
    crew_pk = log.crew_member.pk
    if request.method == 'POST' or request.method == 'GET':
        create_audit_log(
            request.user,
            'DELETE',
            model_instance=log,
            description=f"Deleted Communication Log for {log.crew_member.first_name} {log.crew_member.last_name} (Purpose: {log.purpose_of_call}).",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        log.delete()
        messages.success(request, "Communication log entry deleted successfully.")
    else:
        messages.warning(request, "Deletion requires a POST request.")
    return redirect('crew_communication_log_list', crew_pk=crew_pk)


# --- Professional Reference Management Views ---

@login_required
def crew_professional_reference_list(request, crew_pk):
    crew_member = get_object_or_404(CrewMember, pk=crew_pk)
    if not request.user.is_staff and (not crew_member.user or crew_member.user != request.user):
        messages.error(request, "You are not authorized to view this profile's professional references.")
        return redirect('dashboard')
    references = ProfessionalReference.objects.filter(crew_member=crew_member).order_by('-date')
    return render(request, 'crew_management/professionalreference_list_for_crew.html', {'crew': crew_member, 'references': references})


@login_required
@user_passes_test(is_staff)
def professionalreference_add(request, crew_pk):
    crew_member = get_object_or_404(CrewMember, pk=crew_pk)
    if request.method == 'POST':
        form = ProfessionalReferenceForm(request.POST)
        if form.is_valid():
            reference = form.save(commit=False)
            reference.crew_member = crew_member
            reference.save()
            messages.success(request, f"Professional reference added successfully for {crew_member.first_name}.")
            create_audit_log(
                request.user,
                'CREATE',
                model_instance=reference,
                description=f"Added Professional Reference from '{reference.company_name}' for {crew_member.first_name} {crew_member.last_name}.",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return redirect('crew_professional_reference_list', crew_pk=crew_member.pk)
        else:
            messages.error(request, "Error adding professional reference. Please check the form.")
    else:
        form = ProfessionalReferenceForm()

    context = {
        'form': form,
        'crew': crew_member,
        'title': f"Add Professional Reference for {crew_member.first_name} {crew_member.last_name}",
        'button_text': "Add Reference",
    }
    return render(request, 'crew_management/professionalreference_form.html', context)


@login_required
def professionalreference_detail(request, pk):
    reference = get_object_or_404(ProfessionalReference, pk=pk)
    crew_member = reference.crew_member
    if not request.user.is_staff and (not crew_member.user or crew_member.user != request.user):
        messages.error(request, "You are not authorized to view this professional reference.")
        return redirect('dashboard')
    return render(request, 'crew_management/professionalreference_detail.html', {'reference': reference, 'crew': crew_member})


@login_required
@user_passes_test(is_staff)
def professionalreference_edit(request, pk):
    reference = get_object_or_404(ProfessionalReference, pk=pk)
    crew_member = reference.crew_member
    if request.method == 'POST':
        initial_data = {field.name: getattr(reference, field.name) for field in reference._meta.fields if field.name not in ['id', 'crew_member', 'date']}
        form = ProfessionalReferenceForm(request.POST, instance=reference)
        if form.is_valid():
            updated_instance = form.save()
            messages.success(request, f"Professional reference for {reference.contact_person} updated successfully!")

            changed_fields_detail = {}
            for field_name, new_value in form.cleaned_data.items():
                if field_name not in ['id', 'crew_member', 'date']:
                    old_value = initial_data.get(field_name)
                    if old_value != new_value:
                        changed_fields_detail[field_name] = {
                            'old': str(old_value),
                            'new': str(new_value)
                        }

            description_parts = [f"Updated Professional Reference for {crew_member.first_name} {crew_member.last_name} (Contact: {updated_instance.contact_person})."]
            if changed_fields_detail:
                description_parts.append("Changes:")
                for field, values in changed_fields_detail.items():
                    description_parts.append(f"  {field}: '{values['old']}' -> '{values['new']}'")
            else:
                description_parts.append("No significant data changes detected.")

            create_audit_log(
                request.user,
                'UPDATE',
                model_instance=updated_instance,
                description="\n".join(description_parts),
                ip_address=request.META.get('REMOTE_ADDR'),
                changes=changed_fields_detail
            )
            return redirect('professionalreference_detail', pk=reference.pk)
        else:
            messages.error(request, "Error updating professional reference. Please check the form.")
    else:
        form = ProfessionalReferenceForm(instance=reference)

    context = {
        'form': form,
        'reference': reference,
        'crew': crew_member,
        'title': f"Edit Professional Reference for {crew_member.first_name} {crew_member.last_name}",
        'button_text': "Save Changes",
    }
    return render(request, 'crew_management/professionalreference_form.html', context)


@login_required
@user_passes_test(is_staff)
def professionalreference_delete(request, pk):
    reference = get_object_or_404(ProfessionalReference, pk=pk)
    crew_pk = reference.crew_member.pk
    if request.method == 'POST' or request.method == 'GET':
        create_audit_log(
            request.user,
            'DELETE',
            model_instance=reference,
            description=f"Deleted Professional Reference from '{reference.company_name}' for {reference.crew_member.first_name} {reference.crew_member.last_name}.",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        reference.delete()
        messages.success(request, "Professional reference deleted successfully.")
    else:
        messages.warning(request, "Deletion requires a POST request.")
    return redirect('crew_professional_reference_list', crew_pk=crew_pk)


# --- Appraisal Management Views ---

@login_required
def crew_appraisal_list(request, crew_pk):
    crew_member = get_object_or_404(CrewMember, pk=crew_pk)
    if not request.user.is_staff and (not crew_member.user or crew_member.user != request.user):
        messages.error(request, "You are not authorized to view this profile's appraisals.")
        return redirect('dashboard')
    appraisals = Appraisal.objects.filter(crew_member=crew_member).order_by('-evaluation_date')
    return render(request, 'crew_management/appraisal_list_for_crew.html', {'crew': crew_member, 'appraisals': appraisals})


@login_required
@user_passes_test(is_staff)
def appraisal_add(request, crew_pk):
    crew_member = get_object_or_404(CrewMember, pk=crew_pk)
    if request.method == 'POST':
        form = AppraisalForm(request.POST)
        if form.is_valid():
            appraisal = form.save(commit=False)
            appraisal.crew_member = crew_member
            appraisal.save()
            messages.success(request, f"Appraisal added successfully for {crew_member.first_name}.")
            create_audit_log(
                request.user,
                'CREATE',
                model_instance=appraisal,
                description=f"Added Appraisal for {crew_member.first_name} {crew_member.last_name} on vessel '{appraisal.vessel.name if appraisal.vessel else 'N/A'}'.",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return redirect('crew_appraisal_list', crew_pk=crew_member.pk)
        else:
            messages.error(request, "Error adding appraisal. Please check the form.")
    else:
        form = AppraisalForm()

    context = {
        'form': form,
        'crew': crew_member,
        'title': f"Add Appraisal for {crew_member.first_name} {crew_member.last_name}",
        'button_text': "Add Appraisal",
    }
    return render(request, 'crew_management/appraisal_form.html', context)


@login_required
def appraisal_detail(request, pk):
    appraisal = get_object_or_404(Appraisal, pk=pk)
    crew_member = appraisal.crew_member
    if not request.user.is_staff and (not crew_member.user or crew_member.user != request.user):
        messages.error(request, "You are not authorized to view this appraisal.")
        return redirect('dashboard')
    return render(request, 'crew_management/appraisal_detail.html', {'appraisal': appraisal, 'crew': crew_member})


@login_required
@user_passes_test(is_staff)
def appraisal_edit(request, pk):
    appraisal = get_object_or_404(Appraisal, pk=pk)
    crew_member = appraisal.crew_member
    if request.method == 'POST':
        initial_data = {field.name: getattr(appraisal, field.name) for field in appraisal._meta.fields if field.name not in ['id', 'crew_member']}
        form = AppraisalForm(request.POST, instance=appraisal)
        if form.is_valid():
            updated_instance = form.save()
            messages.success(request, f"Appraisal for {appraisal.seafarer_name} updated successfully!")

            changed_fields_detail = {}
            for field_name, new_value in form.cleaned_data.items():
                if field_name not in ['id', 'crew_member']:
                    old_value = initial_data.get(field_name)
                    if field_name == 'vessel': # Handle FK for vessel
                        old_value_display = str(Vessel.objects.filter(pk=old_value).first()) if old_value else 'None'
                        new_value_display = str(new_value) if new_value else 'None'
                    else:
                        old_value_display = str(old_value)
                        new_value_display = str(new_value)

                    if old_value != new_value:
                        changed_fields_detail[field_name] = {
                            'old': old_value_display,
                            'new': new_value_display
                        }

            description_parts = [f"Updated Appraisal for {crew_member.first_name} {crew_member.last_name} on vessel '{updated_instance.vessel.name if updated_instance.vessel else 'N/A'}'. Estimated score: {updated_instance.overall_score_obtained}/{updated_instance.total_score}."]
            if changed_fields_detail:
                description_parts.append("Changes:")
                for field, values in changed_fields_detail.items():
                    description_parts.append(f"  {field}: '{values['old']}' -> '{values['new']}'")
            else:
                description_parts.append("No significant data changes detected.")

            create_audit_log(
                request.user,
                'UPDATE',
                model_instance=updated_instance,
                description="\n".join(description_parts),
                ip_address=request.META.get('REMOTE_ADDR'),
                changes=changed_fields_detail
            )
            return redirect('appraisal_detail', pk=appraisal.pk)
        else:
            messages.error(request, "Error updating appraisal. Please check the form.")
    else:
        form = AppraisalForm(instance=appraisal)

    context = {
        'form': form,
        'appraisal': appraisal,
        'crew': crew_member,
        'title': f"Edit Appraisal for {crew_member.first_name} {crew_member.last_name}",
        'button_text': "Save Changes",
    }
    return render(request, 'crew_management/appraisal_form.html', context)


@login_required
@user_passes_test(is_staff)
def appraisal_delete(request, pk):
    appraisal = get_object_or_404(Appraisal, pk=pk)
    crew_pk = appraisal.crew_member.pk
    if request.method == 'POST' or request.method == 'GET':
        create_audit_log(
            request.user,
            'DELETE',
            model_instance=appraisal,
            description=f"Deleted Appraisal for {appraisal.crew_member.first_name} {appraisal.crew_member.last_name} on vessel '{appraisal.vessel.name if appraisal.vessel else 'N/A'}'.",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        appraisal.delete()
        messages.success(request, "Appraisal record deleted successfully.")
    else:
        messages.warning(request, "Deletion requires a POST request.")
    return redirect('crew_appraisal_list', crew_pk=crew_pk)

# --- Audit Log View (Access restricted to Superusers) ---
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger # For pagination
from django.db.models import F, Q # For F-expressions and Q-objects

@login_required
# REMOVE @user_passes_test(is_superuser_only) from here
def audit_log_list(request):
    # Manual check for superuser access
    if not request.user.is_superuser:
        messages.error(request, "You are not authorized to view the Audit Log. Only superusers can access this feature.")
        return redirect('dashboard') # Redirect to dashboard instead of login page

    logs = AuditLog.objects.all()

    # --- Filtering Logic (remains the same) ---
    user_id = request.GET.get('user')
    action_type = request.GET.get('action_type')
    model_name = request.GET.get('model_name')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if user_id:
        logs = logs.filter(user_id=user_id)
    if action_type:
        logs = logs.filter(action_type=action_type)
    if model_name:
        logs = logs.filter(model_name=model_name)
    if start_date_str:
        try:
            start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            logs = logs.filter(timestamp__gte=start_date)
        except ValueError:
            messages.error(request, "Invalid start date format. Use YYYY-MM-DD.")
    if end_date_str:
        try:
            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
            logs = logs.filter(timestamp__lt=end_date + datetime.timedelta(days=1))
        except ValueError:
            messages.error(request, "Invalid end date format. Use YYYY-MM-DD.")

    logs = logs.order_by('-timestamp')

    # --- Pagination (remains the same) ---
    paginator = Paginator(logs, 25)
    page = request.GET.get('page')
    try:
        logs_paged = paginator.page(page)
    except PageNotAnInteger:
        logs_paged = paginator.page(1)
    except EmptyPage:
        logs_paged = paginator.page(paginator.num_pages)

    # Prepare filter options for the template (remains the same)
    users_with_logs = User.objects.filter(auditlog__isnull=False).distinct().order_by('username')
    action_types_from_choices = AuditLog.ACTION_CHOICES
    model_names_with_logs = AuditLog.objects.values_list('model_name', flat=True).distinct().exclude(model_name__isnull=True).order_by('model_name')

    context = {
        'logs': logs_paged,
        'users_with_logs': users_with_logs,
        'action_types_from_choices': action_types_from_choices,
        'model_names_with_logs': model_names_with_logs,
        'selected_user_id': user_id,
        'selected_action_type': action_type,
        'selected_model_name': model_name,
        'selected_start_date': start_date_str,
        'selected_end_date': end_date_str,
        'title': "System Audit Log"
    }
    return render(request, 'crew_management/audit_log_list.html', context)

from . import utils

@login_required
def dashboard(request):
    # ... existing total_crew, crew_status_counts ...

    # Get alerts using the new utility function
    alerts_data = utils.get_alert_documents_and_signoffs()

    # ... existing upcoming_sign_offs (you might replace this with alerts_data['upcoming_signoffs_crew']) ...

    context = {
        # ... existing context variables ...
        'expiring_documents': alerts_data['expiring_soon_docs'], # Use the 60-day data
        'expired_documents': alerts_data['expired_docs'],
        'upcoming_sign_offs': alerts_data['upcoming_signoffs_crew'], # Use the 60-day data
    }
    return render(request, 'crew_management/dashboard.html', context)

# crew_management/views.py

# ... (existing imports) ...
from django.conf import settings # Ensure settings is imported
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

# Import the utility functions
from crew_management import utils


# ... (your existing create_audit_log, is_staff, is_superuser_only, and all other views) ...

@login_required
@user_passes_test(is_superuser_only) # Only superusers can view/send alerts
def view_and_send_alerts(request):
    # This view will generate the content for display and optionally send.

    # --- 1. Get Alert Data ---
    alerts_data = utils.get_alert_documents_and_signoffs()
    expiring_soon_docs = alerts_data['expiring_soon_docs']
    expired_docs = alerts_data['expired_docs']
    upcoming_signoffs_crew = alerts_data['upcoming_signoffs_crew']

    # --- 2. Generate Crew Recommendations ---
    all_recommendations = {}
    for signing_off_crew in upcoming_signoffs_crew:
        recommendations = utils.get_crew_recommendations(signing_off_crew)
        if recommendations:
            all_recommendations[signing_off_crew] = recommendations

    # --- Prepare Email Content Context (same as for the management command) ---
    email_context = {
        'expiring_soon_docs': expiring_soon_docs,
        'expired_docs': expired_docs,
        'upcoming_signoffs_crew': upcoming_signoffs_crew,
        'all_recommendations': all_recommendations,
        'current_date': datetime.date.today(),
        'alert_days_doc_expiry': settings.ALERT_DAYS_DOCUMENT_EXPIRY,
        'alert_days_crew_signoff': settings.ALERT_DAYS_CREW_SIGNOFF,
    }

    # --- Optional: Trigger Email Sending if requested (e.g., via POST or a specific GET param) ---
    # For user safety and idempotency, it's best to trigger sending via a POST request
    # or to have a separate "confirm and send" step.
    # For the immediate "generate and send at same time" click, we'll keep it simple for now,
    # but be aware of implications.
    email_sent_status = False
    if request.method == 'POST' and request.POST.get('send_now') == 'true':
        subject = f"CMS Daily Alerts & Crew Recommendations - {datetime.date.today().strftime('%Y-%m-%d')}"
        recipient_list = [settings.ALERT_RECIPIENT_EMAIL]
        html_message = render_to_string('crew_management/emails/alert_email.html', email_context)
        plain_message = strip_tags(html_message)

        try:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                recipient_list,
                html_message=html_message,
                fail_silently=False,
            )
            messages.success(request, f"Alert email successfully sent to {settings.ALERT_RECIPIENT_EMAIL}.")
            email_sent_status = True
            create_audit_log(
                request.user,
                'EMAIL_SENT',
                description=f"Manual trigger: Alert email sent to {settings.ALERT_RECIPIENT_EMAIL}.",
                ip_address=request.META.get('REMOTE_ADDR')
            )
        except Exception as e:
            messages.error(request, f"Error sending alert email: {e}")
            create_audit_log(
                request.user,
                'EMAIL_FAIL',
                description=f"Manual trigger: Failed to send alert email to {settings.ALERT_RECIPIENT_EMAIL}. Error: {e}",
                ip_address=request.META.get('REMOTE_ADDR')
            )

    # Render the email preview page
    context = {
        'email_html_content': html_message if 'html_message' in locals() else render_to_string('crew_management/emails/alert_email.html', email_context),
        'email_sent': email_sent_status,
        'title': "Alert Email Preview & Manual Send",
        'recipient_email': settings.ALERT_RECIPIENT_EMAIL,
    }
    return render(request, 'crew_management/alert_email_preview.html', context)