from django import forms
from django.utils import timezone
from .models import FoodListing


class FoodListingForm(forms.ModelForm):
    class Meta:
        model = FoodListing
        fields = ['name', 'description', 'category', 'quantity', 'unit', 'pickup_location',
                  'available_from', 'expires_at', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'available_from': forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}),
            'expires_at': forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}),
        }
        help_texts = {
            'description': 'Describe the food, ingredients, and known allergens. Do not offer unsafe food.',
            'available_from': 'All times are in Philippine time (Asia/Manila).',
            'expires_at': 'Recipients cannot see the listing after this time.',
            'status': 'Mark completed when the food is no longer available.',
        }

    def clean(self):
        data = super().clean()
        expiry = data.get('expires_at')
        if data.get('status') == FoodListing.Status.AVAILABLE and expiry and expiry <= timezone.now():
            self.add_error('expires_at', 'An available listing must have an expiry in the future.')
        return data
