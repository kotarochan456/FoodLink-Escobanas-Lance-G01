from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from .forms import RegistrationForm, ProfileForm, LoginForm, RoleChoiceForm
from .models import User
from listings.models import FoodListing

@require_http_methods(['GET', 'POST'])
def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                user = form.save(commit=False)
                user.role = form.cleaned_data['role']
                user.is_staff = user.is_superuser = False
                user.save()
        except IntegrityError:
            form.add_error(None, 'That username or email is already in use. Please choose another.')
        else:
            messages.success(request, 'Account created successfully. You can now log in.')
            return redirect('login')
    return render(request, 'accounts/form.html', {'form': form, 'title': 'Create your FoodLink account', 'button': 'Register'})

class AccountLoginView(LoginView):
    authentication_form = LoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    def get_success_url(self):
        # Always enter through the role dispatcher, including after a protected-page redirect.
        from django.urls import reverse
        return reverse('dashboard')

class AccountLogoutView(LogoutView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.success(request, 'You have been logged out.')
        return response

def role_required(role):
    def decorate(view):
        @never_cache
        @login_required
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if request.user.role != role:
                raise PermissionDenied('This dashboard belongs to another role.')
            return view(request, *args, **kwargs)
        return wrapped
    return decorate

@never_cache
@login_required
def dashboard(request):
    if request.user.role == User.Role.ADMIN:
        return redirect('admin_dashboard')
    if request.user.role == User.Role.DONOR:
        return redirect('donor_dashboard')
    if request.user.role == User.Role.RECIPIENT:
        return redirect('recipient_dashboard')
    if request.user.role is None:
        return redirect('choose_role')
    raise PermissionDenied

@role_required(User.Role.DONOR)
def donor_dashboard(request):
    return render(request, 'accounts/donor_dashboard.html', {
        'listing_count': FoodListing.objects.filter(donor=request.user).count(),
        'available_count': FoodListing.objects.filter(donor=request.user).available().count(),
    })

@role_required(User.Role.RECIPIENT)
def recipient_dashboard(request):
    return render(request, 'accounts/recipient_dashboard.html', {
        'available_count': FoodListing.objects.available().count(),
    })

@never_cache
@login_required
@require_http_methods(['GET', 'POST'])
def choose_role(request):
    if request.user.role is not None:
        return redirect('dashboard')
    form = RoleChoiceForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        # Only accounts still awaiting their first choice can be changed.
        # Repeated submissions cannot switch a chosen role or undo Admin promotion.
        changed = User.objects.filter(pk=request.user.pk, role__isnull=True).update(
            role=form.cleaned_data['role'])
        if changed:
            messages.success(request, 'Your account preference has been saved.')
        return redirect('dashboard')
    return render(request, 'accounts/choose_role.html', {'form': form})

@role_required(User.Role.ADMIN)
def admin_dashboard(request):
    return render(request, 'accounts/admin_dashboard.html', {
        'listing_count': FoodListing.objects.count(),
        'donor_count': User.objects.filter(role=User.Role.DONOR).count(),
        'recipient_count': User.objects.filter(role=User.Role.RECIPIENT).count(),
        'pending_count': User.objects.filter(role__isnull=True).count(),
        'active_count': User.objects.filter(is_active=True).count(),
    })

@role_required(User.Role.ADMIN)
@require_http_methods(['GET'])
def manage_roles(request):
    accounts = User.objects.order_by('username', 'pk')
    page = Paginator(accounts, 20).get_page(request.GET.get('page'))
    return render(request, 'accounts/manage_roles.html', {'page_obj': page})

@role_required(User.Role.ADMIN)
@require_http_methods(['GET', 'POST'])
def promote_user(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        with transaction.atomic():
            # Conditional update makes repeat/concurrent submissions harmless.
            changed = User.objects.filter(pk=target.pk, role__in=[User.Role.DONOR, User.Role.RECIPIENT],
                                          is_active=True).update(role=User.Role.ADMIN)
            if changed:
                LogEntry.objects.create(
                    user_id=request.user.pk,
                    content_type=ContentType.objects.get_for_model(User),
                    object_id=str(target.pk), object_repr=target.username,
                    action_flag=CHANGE,
                    change_message='Promoted user to Admin through FoodLink role management.',
                )
        if changed:
            messages.success(request, f'{target.username} is now an Admin.')
        else:
            messages.info(request, 'No change: the account must be an active Donor or Recipient to be promoted.')
        return redirect('manage_roles')
    return render(request, 'accounts/promote_member.html', {'target_account': target})

@never_cache
@login_required
def profile(request):
    return render(request, 'accounts/profile.html')

@never_cache
@login_required
@require_http_methods(['GET', 'POST'])
def profile_edit(request):
    # No URL id or posted id is used: the owner is always the current session user.
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        try:
            with transaction.atomic():
                user = form.save(commit=False)
                user.save(update_fields=list(form.Meta.fields))
        except IntegrityError:
            form.add_error(None, 'That username or email is already in use.')
        else:
            messages.success(request, 'Your profile has been updated.')
            return redirect('profile')
    return render(request, 'accounts/form.html', {'form': form, 'title': 'Edit your profile', 'button': 'Save changes'})
