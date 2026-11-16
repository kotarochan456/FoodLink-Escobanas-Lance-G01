"""PostgreSQL integration tests. Use a disposable test database, not live Supabase."""
from django.contrib.admin.models import LogEntry
from django.db import IntegrityError, transaction
from django.test import TestCase, Client
from django.urls import reverse
from .models import User

PASSWORD = 'FoodLink!Secure7291'

class AccountTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        def create(name, role):
            return User.objects.create_user(username=name, email=f'{name}@example.com', password=PASSWORD,
                first_name=name.title(), last_name='Cruz', contact_number='09171234567', location='Cebu', role=role)
        cls.donor = create('donor', 'DONOR')
        cls.recipient = create('recipient', 'RECIPIENT')
        cls.pending = create('pending', None)
        cls.admin = User.objects.create_superuser(username='admin', email='admin@example.com', password=PASSWORD,
            first_name='Admin', last_name='One', contact_number='09171234567', location='Cebu')

    def data(self, **changes):
        values = dict(username='newuser', email='new@example.com', first_name='New', last_name='User',
            contact_number='09171234567', location='Cebu', role='DONOR', password1=PASSWORD, password2=PASSWORD)
        values.update(changes)
        return values

    def test_registration_choices_password_hash_and_no_staff(self):
        for role in ['DONOR','RECIPIENT']:
            data = self.data(username=role+'new', email=role+'@new.example.com', role=role, is_staff=True, is_superuser=True)
            self.assertRedirects(self.client.post(reverse('register'), data), reverse('login'))
            user = User.objects.get(username=data['username'])
            self.assertEqual(user.role, role)
            self.assertFalse(user.is_staff or user.is_superuser)
            self.assertTrue(user.check_password(PASSWORD))
            self.assertNotEqual(user.password, PASSWORD)

    def test_registration_rejects_missing_and_privileged_roles(self):
        for role in ['', 'ADMIN', 'MEMBER', 'other']:
            response = self.client.post(reverse('register'), self.data(role=role))
            self.assertIn('role', response.context['form'].errors)
        data = self.data(); data.pop('role')
        self.assertIn('role', self.client.post(reverse('register'), data).context['form'].errors)
        self.assertEqual(User.objects.count(), 4)

    def test_required_registration_fields(self):
        for field in self.data():
            self.assertIn(field, self.client.post(reverse('register'), self.data(**{field:''})).context['form'].errors)

    def test_invalid_fields_passwords_and_duplicates(self):
        for changes, field in [({'email':'invalid'},'email'), ({'username':'name@example.com'},'username'),
            ({'contact_number':'abc'},'contact_number'), ({'password2':'different'},'password2'),
            ({'password1':'123','password2':'123'},'password2'), ({'username':'DONOR'},'username'),
            ({'email':'DONOR@EXAMPLE.COM'},'email')]:
            self.assertIn(field, self.client.post(reverse('register'), self.data(**changes)).context['form'].errors)

    def test_database_unique_and_role_constraints(self):
        for changes in [dict(username='DONOR',email='unique@example.com',role='DONOR'),
                        dict(username='unique',email='DONOR@EXAMPLE.COM',role='DONOR'),
                        dict(username='unique',email='unique@example.com',role='MEMBER')]:
            with self.assertRaises(IntegrityError), transaction.atomic():
                User.objects.create(**changes)

    def test_username_email_login_all_roles(self):
        for user, route in [(self.donor,'donor_dashboard'),(self.recipient,'recipient_dashboard'),(self.admin,'admin_dashboard')]:
            for identifier in [user.username.upper(),user.email.upper()]:
                self.client.logout()
                response = self.client.post(reverse('login'), {'username':identifier,'password':PASSWORD}, follow=True)
                self.assertEqual(response.request['PATH_INFO'], reverse(route))

    def test_invalid_and_inactive_login(self):
        self.assertContains(self.client.post(reverse('login'),{'username':'donor','password':'wrong'}), 'Incorrect username/email')
        self.donor.is_active=False;self.donor.save()
        self.assertFalse(self.client.login(username='donor',password=PASSWORD))

    def test_dashboard_isolation_all_pairs(self):
        routes = {'DONOR':'donor_dashboard','RECIPIENT':'recipient_dashboard','ADMIN':'admin_dashboard'}
        for user in [self.donor,self.recipient,self.admin]:
            self.client.force_login(user)
            for role, route in routes.items():
                self.assertEqual(self.client.get(reverse(route)).status_code, 200 if user.role==role else 403)

    def test_anonymous_protected_routes(self):
        for name in ['dashboard','donor_dashboard','recipient_dashboard','admin_dashboard','profile','profile_edit','choose_role','manage_roles']:
            self.assertEqual(self.client.get(reverse(name)).status_code,302)

    def test_logout_clears_session_and_get_rejected(self):
        self.client.force_login(self.donor)
        self.assertEqual(self.client.get(reverse('logout')).status_code,405)
        self.assertRedirects(self.client.post(reverse('logout')),reverse('login'))
        self.assertNotIn('_auth_user_id',self.client.session)
        self.assertEqual(self.client.get(reverse('profile')).status_code,302)

    def test_pending_login_forces_choice(self):
        response=self.client.post(reverse('login'),{'username':'pending','password':PASSWORD},follow=True)
        self.assertEqual(response.request['PATH_INFO'],reverse('choose_role'))
        self.assertContains(response,'must choose one')

    def test_pending_session_cannot_bypass_choice(self):
        self.client.force_login(self.pending)
        urls=[reverse(n) for n in ['dashboard','member_dashboard','donor_dashboard','recipient_dashboard',
              'admin_dashboard','profile','profile_edit','manage_roles','register','login']]
        urls += ['/admin/',reverse('promote_user',args=[self.donor.pk])]
        for url in urls:
            for method in [self.client.get,self.client.post]:
                self.assertRedirects(method(url),reverse('choose_role'))
        self.assertRedirects(self.client.post(reverse('logout')),reverse('login'))

    def test_choice_required_and_rejects_admin_and_legacy_member(self):
        self.client.force_login(self.pending)
        for data in [{},{'role':''},{'role':'ADMIN'},{'role':'MEMBER'}]:
            response=self.client.post(reverse('choose_role'),data)
            self.assertIn('role',response.context['form'].errors)
            self.pending.refresh_from_db();self.assertIsNone(self.pending.role)

    def test_pending_can_choose_either_role_once(self):
        for role,route in [('DONOR','donor_dashboard'),('RECIPIENT','recipient_dashboard')]:
            User.objects.filter(pk=self.pending.pk).update(role=None)
            self.pending.refresh_from_db();self.client.force_login(self.pending)
            response=self.client.post(reverse('choose_role'),{'role':role},follow=True)
            self.assertEqual(response.request['PATH_INFO'],reverse(route))
            self.client.post(reverse('choose_role'),{'role':'ADMIN'})
            self.pending.refresh_from_db();self.assertEqual(self.pending.role,role)

    def test_profile_only_updates_owner_and_not_role(self):
        self.client.force_login(self.donor)
        data=self.data(username='renamed',email='renamed@example.com',role='ADMIN',id=self.recipient.pk,is_staff=True,is_superuser=True)
        self.assertRedirects(self.client.post(reverse('profile_edit'),data),reverse('profile'))
        self.donor.refresh_from_db();self.recipient.refresh_from_db()
        self.assertEqual(self.donor.username,'renamed');self.assertEqual(self.recipient.username,'recipient')
        self.assertEqual(self.donor.role,'DONOR');self.assertFalse(self.donor.is_staff or self.donor.is_superuser)
        self.assertNotContains(self.client.get(reverse('profile')),'recipient@example.com')
        self.client.logout();self.assertTrue(self.client.login(username='renamed@example.com',password=PASSWORD))

    def test_profile_required_and_unique_fields(self):
        self.client.force_login(self.donor)
        for field in ['username','email','first_name','last_name','contact_number','location']:
            self.assertIn(field,self.client.post(reverse('profile_edit'),self.data(**{field:''})).context['form'].errors)
        for field,value in [('username','RECIPIENT'),('email','RECIPIENT@EXAMPLE.COM')]:
            self.assertIn(field,self.client.post(reverse('profile_edit'),self.data(**{field:value})).context['form'].errors)

    def test_admin_promotes_donor_and_recipient_and_logs_once(self):
        self.client.force_login(self.admin)
        for user in [self.donor,self.recipient]:
            url=reverse('promote_user',args=[user.pk])
            self.assertContains(self.client.get(url),'Confirm promotion')
            user.refresh_from_db();self.assertNotEqual(user.role,'ADMIN')
            self.assertRedirects(self.client.post(url),reverse('manage_roles'))
            self.client.post(url)
            user.refresh_from_db();self.assertEqual(user.role,'ADMIN')
            self.assertFalse(user.is_staff or user.is_superuser)
            self.assertEqual(LogEntry.objects.filter(object_id=str(user.pk),user=self.admin).count(),1)

    def test_promoted_admin_can_promote(self):
        User.objects.filter(pk=self.donor.pk).update(role='ADMIN')
        self.donor.refresh_from_db();self.client.force_login(self.donor)
        self.assertContains(self.client.get(reverse('admin_dashboard')),'Manage user roles')
        self.client.post(reverse('promote_user',args=[self.recipient.pk]))
        self.recipient.refresh_from_db();self.assertEqual(self.recipient.role,'ADMIN')

    def test_public_roles_cannot_manage_or_promote(self):
        for user in [self.donor,self.recipient]:
            self.client.force_login(user)
            self.assertEqual(self.client.get(reverse('manage_roles')).status_code,403)
            self.assertEqual(self.client.post(reverse('promote_user',args=[user.pk])).status_code,403)
            user.refresh_from_db();self.assertNotEqual(user.role,'ADMIN')

    def test_pending_inactive_and_missing_cannot_be_promoted(self):
        self.client.force_login(self.admin)
        self.client.post(reverse('promote_user',args=[self.pending.pk]))
        self.pending.refresh_from_db();self.assertIsNone(self.pending.role)
        self.donor.is_active=False;self.donor.save()
        self.client.post(reverse('promote_user',args=[self.donor.pk]))
        self.donor.refresh_from_db();self.assertEqual(self.donor.role,'DONOR')
        self.assertEqual(self.client.post(reverse('promote_user',args=[999999])).status_code,404)

    def test_csrf_all_mutations(self):
        client=Client(enforce_csrf_checks=True)
        for route in ['login','register']:
            self.assertEqual(client.post(reverse(route),{}).status_code,403)
        client.force_login(self.pending)
        self.assertEqual(client.post(reverse('choose_role'),{'role':'DONOR'}).status_code,403)
        client.force_login(self.admin)
        for url in [reverse('logout'),reverse('profile_edit'),reverse('promote_user',args=[self.donor.pk])]:
            self.assertEqual(client.post(url,{}).status_code,403)

    def test_next_cannot_override_role_routing(self):
        response=self.client.post(reverse('login')+'?next=https://example.com',{'username':'donor','password':PASSWORD},follow=True)
        self.assertEqual(response.request['PATH_INFO'],reverse('donor_dashboard'))

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

class LegacyRoleMigrationTests(TransactionTestCase):
    """Verify the actual migration preserves account identity and passwords."""
    def test_existing_members_must_choose_and_admins_stay_admin(self):
        old_target=[('accounts','0001_initial')]
        new_target=[('accounts','0002_donor_recipient_roles')]
        executor=MigrationExecutor(connection)
        executor.migrate(old_target)
        try:
            OldUser=executor.loader.project_state(old_target).apps.get_model('accounts','User')
            member=OldUser.objects.create(username='legacy',email='legacy@example.com',role='MEMBER',
                password='existing-hash',first_name='Legacy',last_name='User',contact_number='09171234567',location='Cebu')
            admin=OldUser.objects.create(username='legacyadmin',email='legacyadmin@example.com',role='ADMIN',
                password='admin-hash',first_name='Existing',last_name='Admin',contact_number='09171234567',location='Cebu',
                is_staff=True,is_superuser=True)
            executor=MigrationExecutor(connection);executor.migrate(new_target)
            NewUser=executor.loader.project_state(new_target).apps.get_model('accounts','User')
            migrated=NewUser.objects.get(pk=member.pk)
            self.assertIsNone(migrated.role)
            self.assertEqual(migrated.password,'existing-hash')
            self.assertEqual(migrated.email,'legacy@example.com')
            self.assertEqual(migrated.contact_number,'09171234567')
            self.assertEqual(migrated.location,'Cebu')
            kept_admin=NewUser.objects.get(pk=admin.pk)
            self.assertEqual(kept_admin.role,'ADMIN')
            self.assertTrue(kept_admin.is_staff and kept_admin.is_superuser)
            self.assertEqual(kept_admin.password,'admin-hash')
        finally:
            MigrationExecutor(connection).migrate(new_target)
