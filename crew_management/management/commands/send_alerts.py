# crew_management/management/commands/send_alerts.py

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import datetime # Import datetime for date formatting in emails

# Import the utility functions we just created
from crew_management import utils
from crew_management.models import CrewMember # Needed for individual crew member context

class Command(BaseCommand):
    help = 'Sends email alerts for document expiries, upcoming sign-offs, and crew recommendations.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting daily alert and recommendation process...'))

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

        # --- 3. Prepare Email Content ---
        subject = f"CMS Daily Alerts & Crew Recommendations - {datetime.date.today().strftime('%Y-%m-%d')}"
        recipient_list = [settings.ALERT_RECIPIENT_EMAIL]

        # Context for the email template
        email_context = {
            'expiring_soon_docs': expiring_soon_docs,
            'expired_docs': expired_docs,
            'upcoming_signoffs_crew': upcoming_signoffs_crew,
            'all_recommendations': all_recommendations,
            'current_date': datetime.date.today(),
            'alert_days_doc_expiry': settings.ALERT_DAYS_DOCUMENT_EXPIRY,
            'alert_days_crew_signoff': settings.ALERT_DAYS_CREW_SIGNOFF,
        }

        # Render HTML content from a template
        # We need to create this email_alert.html template next
        html_message = render_to_string('crew_management/emails/alert_email.html', email_context)
        plain_message = strip_tags(html_message) # Fallback for plain-text email clients

        # --- 4. Send Email ---
        try:
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                recipient_list,
                html_message=html_message,
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f"Alert email sent successfully to {', '.join(recipient_list)}."))
        except Exception as e:
            raise CommandError(f"Error sending alert email: {e}")

        self.stdout.write(self.style.SUCCESS('Daily alert and recommendation process completed.'))