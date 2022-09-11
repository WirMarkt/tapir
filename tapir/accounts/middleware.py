import datetime
from urllib.parse import urlencode
from urllib.request import Request

from django.conf import settings
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from tapir.accounts.models import TapirUser
from tapir.settings import LOGOUT_REDIRECT_URL, OIDC_PROVIDER_LOGOUT_URL
from tapir.shifts.models import Shift, ShiftAttendance


class ClientPermsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_anonymous:
            return

        request_comes_from_welcome_desk = (
            request.META.get("HTTP_X_SSL_CLIENT_VERIFY") == "SUCCESS"
            and request.META["HTTP_X_SSL_CLIENT_S_DN"]
            in settings.CLIENT_PERMISSIONS.keys()
        )
        if request_comes_from_welcome_desk:
            request.user.client_perms = settings.CLIENT_PERMISSIONS[
                request.META["HTTP_X_SSL_CLIENT_S_DN"]
            ]
            return

        current_shifts = Shift.objects.filter(
            start_time__lt=timezone.now() + datetime.timedelta(minutes=20),
            end_time__gt=timezone.now() - datetime.timedelta(minutes=20),
        )
        user_is_currently_doing_a_shift = (
            ShiftAttendance.objects.filter(
                user=request.user, slot__shift__in=current_shifts
            )
            .with_valid_state()
            .exists()
        )
        if user_is_currently_doing_a_shift:
            request.user.client_perms = ["welcomedesk.view"]


class TapirOIDCAB(OIDCAuthenticationBackend):
    def verify_claims(self, claims):
        verified = super(TapirOIDCAB, self).verify_claims(claims)
        has_groups = "roles" in claims
        email_verified = claims.get("email_verified", False)
        # optionally restrict usage to certain users
        return verified and has_groups and email_verified

    def get_user_permissions(self, user_obj: TapirUser, obj=None):
        super_perms = super().get_user_permissions(user_obj, obj)
        return super_perms.union(set(user_obj.oidc_perms))

    def create_user(self, claims):
        user: TapirUser = super(TapirOIDCAB, self).create_user(claims)

        user.oidc_perms = claims["roles"]
        user.save()

        return user

    def update_user(self, user: TapirUser, claims):
        user.oidc_perms = claims["roles"]
        user.save()

        return user


def provider_logout(request):
    # See your provider's documentation for details on if and how this is
    # supported

    id_token = request.session.get("oidc_id_token")

    redirect_url = (
        OIDC_PROVIDER_LOGOUT_URL
        + "?"
        + urlencode(
            {"post_logout_redirect_uri": LOGOUT_REDIRECT_URL, "id_token_hint": id_token}
        )
    )
    return redirect_url
