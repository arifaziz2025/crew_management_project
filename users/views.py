from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib import messages
# Import CrewMember model to link user to their profile
from crew_management.models import CrewMember # <--- ADD THIS LINE

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, f"Welcome, {user.username}!")

            # --- Conditional Redirect Logic ---
            if user.is_staff:
                # Staff users go to the dashboard
                return redirect('dashboard')
            else:
                # Non-staff users (crew) try to go to their own profile page
                try:
                    # Find the CrewMember profile linked to this user
                    crew_profile = CrewMember.objects.get(user=user)
                    # Redirect to their specific profile page
                    return redirect('crew_profile_detail', pk=crew_profile.pk)
                except CrewMember.DoesNotExist:
                    # If a non-staff user logs in but has no linked CrewMember profile
                    messages.warning(request, "Your user account is not linked to a crew profile. Please contact support.")
                    # Optionally redirect to a generic page or log them out
                    auth_logout(request) # Log them out if no profile found
                    return redirect('login')
            # --- End Conditional Redirect Logic ---
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

# ... (rest of your views.py, like logout_view)

def logout_view(request):
    auth_logout(request) # Log the user out
    messages.info(request, "You have been logged out.")
    # Redirect to the URL specified in LOGOUT_REDIRECT_URL (which is 'login')
    return redirect('login')