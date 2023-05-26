from django_auth_ldap.backend import LDAPBackend

from main.models import UserProfile


class CELDAPBackend(LDAPBackend):
    def authenticate_ldap_user(self, *args, **kwargs):
        try:
            user = super(CELDAPBackend, self).authenticate_ldap_user(*args, **kwargs)
        except:
            return None
        if not user:
            return None
        try:
            user.profile
        except UserProfile.DoesNotExist:
            return user
        else:
            return None

    def get_or_build_user(self, username, ldap_user):
        model = self.get_user_model()
        query_value = username.lower()
        try:
            user = model.objects.get(username__iexact=query_value)
        except model.DoesNotExist:
            raise
        return user, False

    def ldap_to_django_username(self, username):
        return username

    def django_to_ldap_username(self, username):
        if "@" in username:
            username = username[:username.find("@")]
        return username