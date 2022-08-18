import datetime

from django.conf import settings
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from tapir.accounts.models import TapirUser
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
    # def create_user(self, claims):
    #     user: TapirUser = super(TapirOIDCAB, self).create_user(claims)
    #
    #     user.first_name = claims.get('given_name', '')
    #     user.last_name = claims.get('family_name', '')
    #     user.save()
    #
    #     return user

    def update_user(self, user: TapirUser, claims):
        # user.first_name = claims.get('given_name', '')
        # user.last_name = claims.get('family_name', '')
        # user.save()

        return user
