from datetime import timedelta
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from accounts.models import User
from .models import FoodListing


class ListingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        def user(name, role):
            return User.objects.create_user(username=name, email=name+'@example.com', password='Test-Only-7291!',
                first_name='Test', last_name='User', contact_number='09912345678', location='Cebu', role=role)
        cls.donor = user('owner', 'DONOR')
        cls.other = user('other', 'DONOR')
        cls.recipient = user('reader', 'RECIPIENT')
        cls.admin = user('manager', 'ADMIN')
        cls.pending = user('pending', None)
        cls.listing = FoodListing.objects.create(donor=cls.donor, **cls.data())

    @staticmethod
    def data(**changes):
        data = dict(name='Vegetable meals', description='Freshly cooked. Contains soy.', category='COOKED',
                    quantity=5, unit='portions', pickup_location='Community hall', status='AVAILABLE',
                    available_from=timezone.now()-timedelta(hours=1), expires_at=timezone.now()+timedelta(hours=4))
        data.update(changes)
        return data

    def url(self, action, pk=None):
        return reverse('listings:'+action, args=[pk or self.listing.pk] if action in ['detail','update','delete'] else [])

    def test_anonymous_redirects_all_routes(self):
        for action in ['list','detail','create','update','delete']:
            for method in [self.client.get,self.client.post]:
                self.assertEqual(method(self.url(action)).status_code,302)

    def test_owner_full_ui_crud_and_owner_spoof_ignored(self):
        self.client.force_login(self.donor)
        response=self.client.post(self.url('create'), self.data(donor=self.other.pk),follow=True)
        self.assertContains(response,'Food listing created successfully.')
        listing=FoodListing.objects.latest('pk')
        self.assertEqual(listing.donor,self.donor)
        response=self.client.post(self.url('update',listing.pk),self.data(name='Updated meals',donor=self.other.pk),follow=True)
        self.assertContains(response,'Food listing updated successfully.')
        listing.refresh_from_db();self.assertEqual(listing.name,'Updated meals');self.assertEqual(listing.donor,self.donor)
        self.assertContains(self.client.get(self.url('delete',listing.pk)),'Delete food listing?')
        self.assertTrue(FoodListing.objects.filter(pk=listing.pk).exists())
        self.assertRedirects(self.client.post(self.url('delete',listing.pk)),self.url('list'))
        self.assertFalse(FoodListing.objects.filter(pk=listing.pk).exists())

    def test_other_donor_cannot_read_or_modify(self):
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(self.url('list')),self.listing.name)
        for action in ['detail','update','delete']:
            self.assertEqual(self.client.get(self.url(action)).status_code,404)
        for action in ['update','delete']:
            self.assertEqual(self.client.post(self.url(action),self.data()).status_code,404)
        self.listing.refresh_from_db();self.assertEqual(self.listing.donor,self.donor)

    def test_recipient_read_only(self):
        self.client.force_login(self.recipient)
        self.assertContains(self.client.get(self.url('list')),self.listing.name)
        self.assertContains(self.client.get(self.url('detail')),self.listing.description)
        for action in ['create','update','delete']:
            for method in [self.client.get,self.client.post]:
                self.assertEqual(method(self.url(action),self.data()).status_code,403)

    def test_recipient_cannot_open_hidden_listing_by_url(self):
        self.client.force_login(self.recipient)
        for changes in [dict(status='COMPLETED'),dict(expires_at=timezone.now()-timedelta(minutes=1)),
                        dict(available_from=timezone.now()+timedelta(hours=1))]:
            FoodListing.objects.filter(pk=self.listing.pk).update(**self.data(**changes))
            self.assertEqual(self.client.get(self.url('detail')).status_code,404)
            self.assertNotContains(self.client.get(self.url('list')),self.listing.name)
        FoodListing.objects.filter(pk=self.listing.pk).update(**self.data())
        User.objects.filter(pk=self.donor.pk).update(is_active=False)
        self.assertEqual(self.client.get(self.url('detail')).status_code,404)

    def test_admin_can_manage_without_staff_permission(self):
        self.client.force_login(self.admin)
        self.assertFalse(self.admin.is_staff)
        self.assertContains(self.client.get(self.url('list')),self.listing.name)
        self.assertRedirects(self.client.post(self.url('update'),self.data(status='COMPLETED')),self.url('detail'))
        self.listing.refresh_from_db();self.assertEqual(self.listing.status,'COMPLETED')
        self.assertRedirects(self.client.post(self.url('delete')),self.url('list'))
        self.assertEqual(self.client.post(self.url('create'),self.data()).status_code,403)

    def test_pending_role_choice_gate(self):
        self.client.force_login(self.pending)
        for action in ['list','detail','create','update','delete']:
            self.assertRedirects(self.client.get(self.url(action)),reverse('choose_role'))
            self.assertRedirects(self.client.post(self.url(action),self.data()),reverse('choose_role'))

    def test_validation_required_formats_and_business_rules(self):
        self.client.force_login(self.donor)
        for field in self.data():
            response=self.client.post(self.url('create'),self.data(**{field:''}))
            self.assertIn(field,response.context['form'].errors)
        for changes,field in [({'quantity':0},'quantity'),({'quantity':-1},'quantity'),({'quantity':'a'},'quantity'),
            ({'category':'INVALID'},'category'),({'status':'RESERVED'},'status'),({'name':' '*3},'name'),
            ({'available_from':'bad'},'available_from'),({'expires_at':timezone.now()-timedelta(minutes=1)},'expires_at'),
            ({'available_from':timezone.now()+timedelta(days=2)},'expires_at')]:
            response=self.client.post(self.url('create'),self.data(**changes))
            self.assertTrue(response.context['form'].errors)
            self.assertIn(field,response.context['form'].errors)
        self.assertEqual(FoodListing.objects.count(),1)

    def test_expired_listing_can_be_marked_completed(self):
        self.client.force_login(self.donor)
        self.assertRedirects(self.client.post(self.url('update'),self.data(status='COMPLETED',
            expires_at=timezone.now()-timedelta(minutes=1))),self.url('detail'))

    def test_database_constraints(self):
        for changes in [dict(quantity=0),dict(status='INVALID'),dict(expires_at=timezone.now()-timedelta(days=1))]:
            with self.assertRaises(IntegrityError),transaction.atomic():
                FoodListing.objects.filter(pk=self.listing.pk).update(**changes)

    def test_csrf_mutations_and_read_only_methods(self):
        client=Client(enforce_csrf_checks=True);client.force_login(self.donor)
        for action in ['create','update','delete']:
            self.assertEqual(client.post(self.url(action),self.data()).status_code,403)
        for action in ['list','detail']:
            self.client.force_login(self.donor)
            self.assertEqual(self.client.post(self.url(action)).status_code,405)

    def test_missing_record_and_html_escaping(self):
        self.client.force_login(self.donor)
        self.assertEqual(self.client.get(self.url('detail',99999)).status_code,404)
        FoodListing.objects.filter(pk=self.listing.pk).update(name='<script>alert(1)</script>')
        response=self.client.get(self.url('detail'))
        self.assertContains(response,'&lt;script&gt;')
        self.assertNotContains(response,'<script>alert(1)</script>')

    def test_search_filters_preserve_role_visibility(self):
        FoodListing.objects.create(donor=self.other, **self.data(name='Banana bread',category='BAKERY'))
        self.client.force_login(self.recipient)
        response=self.client.get(self.url('list'),{'q':'banana','category':'BAKERY','location':'hall'})
        self.assertContains(response,'Banana bread');self.assertNotContains(response,'Vegetable meals')
        self.client.force_login(self.donor)
        self.assertNotContains(self.client.get(self.url('list'),{'q':'banana'}),'Banana bread')
        response=self.client.get(self.url('list'),{'category':'INVALID'})
        self.assertIn('category',response.context['filter_form'].errors)
        self.assertEqual(response.context['page_obj'].paginator.count,0)

    def test_pagination_keeps_filters(self):
        for i in range(13):
            FoodListing.objects.create(donor=self.donor, **self.data(name=f'Meal {i}'))
        self.client.force_login(self.recipient)
        response=self.client.get(self.url('list'),{'q':'Meal','page':2})
        self.assertEqual(response.context['page_obj'].number,2)
        self.assertContains(response,'q=Meal&amp;page=1')

    def test_dashboard_counts_and_role_actions(self):
        for user, route, text in [(self.donor,'donor_dashboard','Share food'),
            (self.recipient,'recipient_dashboard','Browse food'),(self.admin,'admin_dashboard','Manage food listings')]:
            self.client.force_login(user)
            response=self.client.get(reverse(route))
            self.assertContains(response,text)
            self.assertContains(response,reverse('listings:list'))
