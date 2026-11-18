from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class FoodListingQuerySet(models.QuerySet):
    def available(self):
        now = timezone.now()
        return self.filter(status='AVAILABLE', available_from__lte=now, expires_at__gt=now,
                           donor__is_active=True)


class FoodListing(models.Model):
    class Category(models.TextChoices):
        COOKED = 'COOKED', 'Cooked meals'
        PRODUCE = 'PRODUCE', 'Fruit and vegetables'
        BAKERY = 'BAKERY', 'Bread and bakery'
        PACKAGED = 'PACKAGED', 'Packaged food'
        OTHER = 'OTHER', 'Other'

    class Status(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Available'
        COMPLETED = 'COMPLETED', 'Completed / no longer available'

    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                              related_name='food_listings')
    name = models.CharField(max_length=150)
    description = models.TextField(max_length=2000)
    category = models.CharField(max_length=12, choices=Category.choices)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], help_text='Number of portions or items available.')
    unit = models.CharField(max_length=40, help_text='For example: portions, bags, or cans.')
    pickup_location = models.CharField(max_length=200)
    available_from = models.DateTimeField('Available from')
    expires_at = models.DateTimeField('Best consumed before / expiry')
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.AVAILABLE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = FoodListingQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at', '-pk']
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gt=0), name='listing_quantity_positive'),
            models.CheckConstraint(condition=Q(expires_at__gt=F('available_from')), name='listing_dates_ordered'),
            models.CheckConstraint(condition=Q(status__in=['AVAILABLE', 'COMPLETED']), name='listing_valid_status'),
        ]
        indexes = [models.Index(fields=['status', 'expires_at'], name='listing_availability_idx')]

    def clean(self):
        super().clean()
        if self.available_from and self.expires_at and self.expires_at <= self.available_from:
            raise ValidationError({'expires_at': 'Expiry must be later than the availability time.'})

    @property
    def availability_label(self):
        if self.status == self.Status.COMPLETED:
            return 'Completed'
        if self.expires_at <= timezone.now():
            return 'Expired'
        if self.available_from > timezone.now():
            return 'Scheduled'
        return 'Available'

    def __str__(self):
        return self.name
