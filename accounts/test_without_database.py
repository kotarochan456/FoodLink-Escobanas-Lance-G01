"""Database-independent checks. Database operations are mocked explicitly."""
import importlib
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.template.loader import get_template
from django.test import SimpleTestCase, RequestFactory, Client
from django.urls import reverse
from .models import User, username_validator, phone_validator
from .forms import RegistrationForm, ProfileForm, RoleChoiceForm
from .backends import UsernameOrEmailBackend
from .middleware import RequireRoleChoiceMiddleware
from . import views

class NoDatabaseTests(SimpleTestCase):
    def request_for(self, role, method='get', data=None):
        request=getattr(RequestFactory(),method)('/',data or {})
        request.user=User(pk=1,username='actor',role=role)
        return request

    def test_templates_compile_and_role_dashboards_render(self):
        for name in ['base.html','403.html','accounts/form.html','accounts/login.html','accounts/profile.html',
                     'accounts/donor_dashboard.html','accounts/recipient_dashboard.html','accounts/admin_dashboard.html',
                     'accounts/choose_role.html','accounts/manage_roles.html','accounts/promote_member.html']:
            get_template(name)
        with patch('accounts.views.FoodListing.objects') as listings:
            listings.filter.return_value.count.return_value = 0
            listings.filter.return_value.available.return_value.count.return_value = 0
            listings.available.return_value.count.return_value = 0
            for role,view in [('DONOR',views.donor_dashboard),('RECIPIENT',views.recipient_dashboard)]:
                self.assertEqual(view(self.request_for(role)).status_code,200)

    def test_public_pages_render(self):
        for name in ['login','register']:
            self.assertEqual(self.client.get(reverse(name)).status_code,200)

    def test_required_fields_no_privilege_fields(self):
        for form in [RegistrationForm(),ProfileForm()]:
            for field in ['first_name','last_name','username','email','contact_number','location']:
                self.assertTrue(form.fields[field].required)
            for field in ['is_staff','is_superuser','id']:
                self.assertNotIn(field,form.fields)
        self.assertNotIn('role',ProfileForm().fields)
        role=RegistrationForm().fields['role']
        self.assertTrue(role.required)
        self.assertEqual({value for value,label in role.choices},{'','DONOR','RECIPIENT'})

    def test_choice_form_required_and_allowlist(self):
        for value in ['', 'ADMIN','MEMBER','invalid']:
            self.assertFalse(RoleChoiceForm({'role':value}).is_valid())
        self.assertFalse(RoleChoiceForm({}).is_valid())
        for value in ['DONOR','RECIPIENT']:
            self.assertTrue(RoleChoiceForm({'role':value}).is_valid())

    def test_username_and_contact_validation(self):
        username_validator('lance.123');phone_validator('+63 917 123 4567')
        with self.assertRaises(ValidationError):username_validator('lance@example.com')
        for value in ['abc','123','']:
            with self.assertRaises(ValidationError):phone_validator(value)

    def test_password_hash(self):
        value=make_password('MySecret!78342')
        self.assertNotEqual(value,'MySecret!78342')
        self.assertTrue(check_password('MySecret!78342',value))
        self.assertFalse(check_password('wrong',value))

    def test_role_dispatch(self):
        for role,route in [('DONOR','donor_dashboard'),('RECIPIENT','recipient_dashboard'),('ADMIN','admin_dashboard'),(None,'choose_role')]:
            self.assertEqual(views.dashboard(self.request_for(role)).url,reverse(route))

    def test_cross_role_access_all_pairs(self):
        for role in ['DONOR','RECIPIENT','ADMIN']:
            for needed,view in [('DONOR',views.donor_dashboard),('RECIPIENT',views.recipient_dashboard),('ADMIN',views.admin_dashboard)]:
                if role != needed:
                    with self.assertRaises(PermissionDenied):view(self.request_for(role))

    def test_anonymous_routes_redirect(self):
        for name in ['dashboard','donor_dashboard','recipient_dashboard','admin_dashboard','choose_role','profile','profile_edit','manage_roles']:
            self.assertEqual(self.client.get(reverse(name)).status_code,302)

    def test_pending_gate_blocks_all_but_choice_and_logout(self):
        middleware=RequireRoleChoiceMiddleware(lambda r:None)
        for name in ['dashboard','donor_dashboard','recipient_dashboard','admin_dashboard','profile','profile_edit','manage_roles','promote_user','login','register','index']:
            request=self.request_for(None)
            request.resolver_match=SimpleNamespace(url_name=name)
            self.assertEqual(middleware.process_view(request,None,(),{}).url,reverse('choose_role'))
        for name in ['choose_role','logout']:
            request=self.request_for(None);request.resolver_match=SimpleNamespace(url_name=name)
            self.assertIsNone(middleware.process_view(request,None,(),{}))

    def test_gate_allows_selected_roles_and_anonymous(self):
        middleware=RequireRoleChoiceMiddleware(lambda r:None)
        for role in ['DONOR','RECIPIENT','ADMIN']:
            request=self.request_for(role)
            self.assertIsNone(middleware.process_view(request,None,(),{}))
        request=RequestFactory().get('/');request.user=AnonymousUser()
        self.assertIsNone(middleware.process_view(request,None,(),{}))

    def test_valid_choice_conditionally_updates_only_pending_user(self):
        for role in ['DONOR','RECIPIENT']:
            with patch.object(User.objects,'filter') as query,patch('accounts.views.messages.success'):
                query.return_value.update.return_value=1
                response=views.choose_role(self.request_for(None,'post',{'role':role}))
                query.assert_called_once_with(pk=1,role__isnull=True)
                query.return_value.update.assert_called_once_with(role=role)
                self.assertEqual(response.url,reverse('dashboard'))

    def test_cannot_change_existing_role_via_choice_page(self):
        with patch.object(User.objects,'filter') as query:
            for role in ['DONOR','RECIPIENT','ADMIN']:
                self.assertEqual(views.choose_role(self.request_for(role,'post',{'role':'DONOR'})).url,reverse('dashboard'))
            query.assert_not_called()

    def test_choice_get_and_invalid_post_do_not_update(self):
        with patch.object(User.objects,'filter') as query:
            self.assertEqual(views.choose_role(self.request_for(None)).status_code,200)
            self.assertEqual(views.choose_role(self.request_for(None,'post',{'role':'ADMIN'})).status_code,200)
            query.assert_not_called()

    def test_csrf_mutations(self):
        client=Client(enforce_csrf_checks=True)
        for name in ['register','login','logout','profile_edit','choose_role']:
            self.assertEqual(client.post(reverse(name),{}).status_code,403)
        self.assertEqual(client.post(reverse('promote_user',args=[2]),{}).status_code,403)

    def test_login_username_email_and_inactive(self):
        user=User(username='lance',email='lance@example.com',role='DONOR');user.set_password('Test!983472')
        backend=UsernameOrEmailBackend()
        for value,lookup in [('LANCE',{'username__iexact':'LANCE'}),('LANCE@EXAMPLE.COM',{'email__iexact':'LANCE@EXAMPLE.COM'})]:
            with patch.object(User.objects,'get',return_value=user) as get:
                self.assertIs(backend.authenticate(None,value,'Test!983472'),user)
                get.assert_called_once_with(**lookup)
                self.assertIsNone(backend.authenticate(None,value,'wrong'))
                user.is_active=False
                self.assertIsNone(backend.authenticate(None,value,'Test!983472'));user.is_active=True

    def test_missing_user_cannot_authenticate(self):
        with patch.object(User.objects,'get',side_effect=User.DoesNotExist):
            self.assertIsNone(UsernameOrEmailBackend().authenticate(None,'missing','wrong'))

    def test_public_roles_cannot_promote_or_list(self):
        for role in ['DONOR','RECIPIENT']:
            with self.assertRaises(PermissionDenied):views.manage_roles(self.request_for(role))
            with self.assertRaises(PermissionDenied):views.promote_user(self.request_for(role,'post'),2)

    def test_promotion_get_does_not_update(self):
        with patch('accounts.views.get_object_or_404',return_value=User(pk=2,username='donor',role='DONOR')),patch.object(User.objects,'filter') as query:
            response=views.promote_user(self.request_for('ADMIN'),2)
            self.assertIn(b'Confirm promotion',response.content);query.assert_not_called()

    def test_promotion_conditions_role_only_and_audit(self):
        with patch('accounts.views.get_object_or_404',return_value=User(pk=2,username='donor',role='DONOR')), \
             patch('accounts.views.transaction.atomic'),patch.object(User.objects,'filter') as query, \
             patch('accounts.views.ContentType.objects.get_for_model'),patch('accounts.views.LogEntry.objects.create') as log, \
             patch('accounts.views.messages.success'):
            query.return_value.update.return_value=1
            views.promote_user(self.request_for('ADMIN','post'),2)
            query.assert_called_once_with(pk=2,role__in=['DONOR','RECIPIENT'],is_active=True)
            query.return_value.update.assert_called_once_with(role='ADMIN')
            self.assertEqual(log.call_args.kwargs['user_id'],1)

    def test_repeat_promotion_no_duplicate_log(self):
        with patch('accounts.views.get_object_or_404',return_value=User(pk=2)),patch('accounts.views.transaction.atomic'), \
             patch.object(User.objects,'filter') as query,patch('accounts.views.LogEntry.objects.create') as log, \
             patch('accounts.views.messages.info'):
            query.return_value.update.return_value=0
            views.promote_user(self.request_for('ADMIN','post'),2);log.assert_not_called()

    def test_data_migration_targets_only_legacy_members(self):
        migration=importlib.import_module('accounts.migrations.0002_donor_recipient_roles')
        apps=MagicMock();editor=SimpleNamespace(connection=SimpleNamespace(alias='default'))
        migration.require_legacy_choice(apps,editor)
        manager=apps.get_model.return_value.objects.using.return_value
        apps.get_model.assert_called_once_with('accounts','User')
        manager.filter.assert_called_once_with(role='MEMBER')
        manager.filter.return_value.update.assert_called_once_with(role=None)
