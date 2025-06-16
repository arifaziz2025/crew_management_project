# crew_management/utils.py

from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, F # Import Sum and F for aggregation
from .models import CrewMember, Document, Principal, Vessel, MonthlyAllotment, FinancialObligation # Import new models


def get_alert_documents_and_signoffs():
    """
    Identifies documents expiring soon and crew members with upcoming sign-offs.
    Checks based on thresholds defined in settings.
    """
    today = timezone.now().date()
    expiry_threshold_date = today + timedelta(days=settings.ALERT_DAYS_DOCUMENT_EXPIRY)
    signoff_threshold_date = today + timedelta(days=settings.ALERT_DAYS_CREW_SIGNOFF)

    # Documents expiring within the threshold
    expiring_soon_docs = Document.objects.filter(
        expiry_date__gte=today,
        expiry_date__lte=expiry_threshold_date
    ).order_by('expiry_date')

    # Documents already expired
    expired_docs = Document.objects.filter(
        expiry_date__lt=today
    ).order_by('-expiry_date')

    # Crew with upcoming sign-offs within the threshold
    upcoming_signoffs_crew = CrewMember.objects.filter(
        relieving_plan_date__gte=today,
        relieving_plan_date__lte=signoff_threshold_date
    ).order_by('relieving_plan_date')

    return {
        'expiring_soon_docs': expiring_soon_docs,
        'expired_docs': expired_docs,
        'upcoming_signoffs_crew': upcoming_signoffs_crew,
    }

def get_crew_recommendations(signing_off_crew_member, num_recommendations=settings.ALERT_RECOMMENDATION_COUNT):
    """
    Recommends available crew members based on matching criteria and "first-come, first-serve".
    Matching criteria:
    - Current rank matches
    - Worked for the same principal (current principal of signing-off crew)
    - Possess the same licenses/documents as the signing-off crew, valid for next 1 year.
    - Signed off first (among available crew).
    """
    if not signing_off_crew_member:
        return []

    # Get required documents and their validity for the signing-off crew member
    # We only care about specific types of documents/licenses for matching
    required_docs_info = signing_off_crew_member.documents.filter(
        document_type__in=['License', 'Training', 'Flag'] # Adjust document types to match qualifications
    ).values_list('document_name', 'document_type', 'expiry_date')

    # Define the required validity period for candidate documents
    required_valid_until = timezone.now().date() + timedelta(days=365) # Valid for next 1 year (approx)

    # 1. Filter for available crew matching rank and principal
    potential_candidates = CrewMember.objects.filter(
        crew_status='Available',
        current_rank=signing_off_crew_member.current_rank,
        principal=signing_off_crew_member.principal # Must have worked for the same principal
    ).order_by('last_sign_off_date') # "First-come, first-serve" - signed off earliest

    # 2. Iterate through candidates to check document matching
    qualified_candidates = []
    for candidate in potential_candidates:
        candidate_docs = Document.objects.filter(crew_member=candidate)
        has_all_required_docs = True

        for req_doc_name, req_doc_type, req_expiry_date_orig in required_docs_info:
            # Find a matching document in the candidate's list
            matching_candidate_doc = candidate_docs.filter(
                document_name=req_doc_name,
                document_type=req_doc_type
            ).first()

            if not matching_candidate_doc:
                has_all_required_docs = False
                break # Candidate is missing a required document

            # Check if the found document is valid for the required period
            if matching_candidate_doc.expiry_date and matching_candidate_doc.expiry_date < required_valid_until:
                has_all_required_docs = False
                break # Document not valid for long enough

        if has_all_required_docs:
            qualified_candidates.append(candidate)
            if len(qualified_candidates) >= num_recommendations:
                break # Found enough recommendations

    return qualified_candidates

def get_financial_summary():
    """
    Calculates key financial summary figures for the dashboard.
    """
    total_allotments_pending = MonthlyAllotment.objects.filter(
        status='PENDING'
    ).aggregate(total=Sum('amount'))['total'] or 0

    total_allotments_paid = MonthlyAllotment.objects.filter(
        status='PAID'
    ).aggregate(total=Sum('amount'))['total'] or 0

    total_obligations_outstanding = FinancialObligation.objects.filter(
        status='OUTSTANDING'
    ).aggregate(total=Sum(F('amount_due') - F('amount_paid')))['total'] or 0
    
    total_obligations_paid = FinancialObligation.objects.filter(
        status='PAID'
    ).aggregate(total=Sum('amount_paid'))['total'] or 0

    # You might want to define a default currency or aggregate by currency
    # For simplicity, this sums across all currencies. Consider currency management if multi-currency is complex.

    return {
        'total_allotments_pending': total_allotments_pending,
        'total_allotments_paid': total_allotments_paid,
        'total_obligations_outstanding': total_obligations_outstanding,
        'total_obligations_paid': total_obligations_paid,
    }