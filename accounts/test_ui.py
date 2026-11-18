"""Server-rendered UI checks; these do not replace browser visual inspection."""
from django.test import SimpleTestCase, RequestFactory
from django.template.loader import render_to_string
from django.contrib.auth.models import AnonymousUser
from django.core.paginator import Paginator
from django.forms.utils import ErrorDict, ErrorList
from .models import User
from .forms import RegistrationForm, ProfileForm, RoleChoiceForm

class UiTests(SimpleTestCase):
    def render(self, template, context=None, user=None):
        request=RequestFactory().get('/')
        request.user=user or AnonymousUser()
        return render_to_string(template, context or {}, request=request)

    def test_login_bootstrap_cdn_and_theme_assets(self):
        response=self.client.get('/accounts/login/')
        self.assertContains(response,'bootstrap@5.3.9/dist/css/bootstrap.min.css')
        self.assertContains(response,'bootstrap@5.3.9/dist/js/bootstrap.bundle.min.js')
        self.assertContains(response,'theme.js')
        self.assertContains(response,'data-theme-toggle')
        self.assertContains(response,'name="csrfmiddlewaretoken"')
        self.assertNotContains(response,'react-dom')

    def test_registration_has_required_role_radios_with_no_default(self):
        html=self.render('accounts/form.html',{'form':RegistrationForm(),'title':'Register','button':'Register'})
        self.assertIn('name="role" value="DONOR"',html)
        self.assertIn('name="role" value="RECIPIENT"',html)
        self.assertNotIn('value="ADMIN"',html)
        self.assertNotIn('checked',html)
        self.assertIn('class="form-control"',html)

    def test_choice_preserves_selection_on_validation_error(self):
        form=RoleChoiceForm({'role':'RECIPIENT'})
        form.is_valid()
        html=self.render('accounts/choose_role.html',{'form':form},User(pk=1,first_name='Lance',role=None))
        self.assertIn('id="role-recipient" required checked',html)
        self.assertNotIn('id="role-donor" required checked',html)
        self.assertIn('name="csrfmiddlewaretoken"',html)

    def test_profile_field_errors_accessible(self):
        form=ProfileForm()
        form._errors=ErrorDict({'email':ErrorList(['Enter a valid email address.'])})
        html=self.render('accounts/form.html',{'form':form,'title':'Edit profile','button':'Save'},User(pk=1,role='DONOR'))
        self.assertIn('is-invalid',html)
        self.assertIn('id="id_email_errors"',html)
        self.assertIn('aria-describedby="id_email_errors"',html)
        self.assertNotIn('name="role"',html)

    def test_role_table_has_only_authorized_action_targets(self):
        accounts=[User(pk=1,username='donor',role='DONOR'),User(pk=2,username='pending',role=None),User(pk=3,username='admin',role='ADMIN')]
        html=self.render('accounts/manage_roles.html',{'page_obj':Paginator(accounts,20).page(1)},accounts[2])
        self.assertIn('/dashboard/admin/users/1/promote/',html)
        self.assertNotIn('/dashboard/admin/users/2/promote/',html)
        self.assertNotIn('/dashboard/admin/users/3/promote/',html)
        self.assertIn('table-responsive',html)
        self.assertIn('Awaiting choice',html)

    def test_all_role_dashboards_and_profile_render(self):
        for role in ['DONOR','RECIPIENT','ADMIN']:
            user=User(pk=1,username='demo',first_name='Demo',last_name='User',role=role)
            html=self.render('accounts/'+role.lower()+'_dashboard.html',dict(donor_count=2,recipient_count=3,pending_count=1,active_count=6),user)
            self.assertIn(role.title()+' dashboard',html)
            self.assertIn('data-theme-toggle',html)
            self.assertIn('My profile',self.render('accounts/profile.html',{},user))

    def test_error_pages_render(self):
        for code in ['403','404','500']:
            self.assertIn('error-code',self.render(code+'.html'))

    def test_native_admin_login_inherits_theme(self):
        response=self.client.get('/admin/login/')
        self.assertContains(response,'admin-theme.css')
        self.assertContains(response,'data-theme-toggle')
        self.assertContains(response,'bootstrap@5.3.9')
