from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from accounts.models import User
from .forms import FoodListingForm
from .models import FoodListing


def visible_listings(user):
    listings = FoodListing.objects.select_related('donor')
    if user.role == User.Role.ADMIN:
        return listings
    if user.role == User.Role.DONOR:
        return listings.filter(donor=user)
    if user.role == User.Role.RECIPIENT:
        return listings.available()
    raise PermissionDenied


def editable_listing(user, pk):
    if user.role not in (User.Role.DONOR, User.Role.ADMIN):
        raise PermissionDenied
    return get_object_or_404(visible_listings(user), pk=pk)


@never_cache
@login_required
@require_http_methods(['GET'])
def listing_list(request):
    page = Paginator(visible_listings(request.user), 12).get_page(request.GET.get('page'))
    return render(request, 'listings/list.html', {'page_obj': page})


@never_cache
@login_required
@require_http_methods(['GET'])
def listing_detail(request, pk):
    listing = get_object_or_404(visible_listings(request.user), pk=pk)
    return render(request, 'listings/detail.html', {'listing': listing})


@never_cache
@login_required
@require_http_methods(['GET', 'POST'])
def listing_create(request):
    if request.user.role != User.Role.DONOR:
        raise PermissionDenied
    form = FoodListingForm(request.POST if request.method == 'POST' else None,
                           initial={'pickup_location': request.user.location})
    if request.method == 'POST' and form.is_valid():
        listing = form.save(commit=False)
        listing.donor = request.user
        listing.save()
        messages.success(request, 'Food listing created successfully.')
        return redirect('listings:detail', pk=listing.pk)
    return render(request, 'listings/form.html', {'form': form, 'title': 'Share food'})


@never_cache
@login_required
@require_http_methods(['GET', 'POST'])
def listing_update(request, pk):
    listing = editable_listing(request.user, pk)
    form = FoodListingForm(request.POST if request.method == 'POST' else None, instance=listing)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Food listing updated successfully.')
        return redirect('listings:detail', pk=listing.pk)
    return render(request, 'listings/form.html', {'form': form, 'title': 'Edit food listing', 'listing': listing})


@never_cache
@login_required
@require_http_methods(['GET', 'POST'])
def listing_delete(request, pk):
    listing = editable_listing(request.user, pk)
    if request.method == 'POST':
        listing.delete()
        messages.success(request, 'Food listing deleted successfully.')
        return redirect('listings:list')
    return render(request, 'listings/delete.html', {'listing': listing})
