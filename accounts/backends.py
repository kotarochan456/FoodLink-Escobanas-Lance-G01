from django.contrib.auth.backends import ModelBackend
from .models import User

class UsernameOrEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        identifier = username.strip()
        lookup = {'email__iexact': identifier} if '@' in identifier else {'username__iexact': identifier}
        try:
            user = User.objects.get(**lookup)
        except User.DoesNotExist:
            User().set_password(password)  # Keep missing-user work comparable to password checking.
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
