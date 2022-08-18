import logging

from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager, User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.db import connections, router, models
from django.template import loader
from django.urls import reverse
from django.utils import translation
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from tapir import utils
from tapir.accounts import validators
from tapir.log.models import UpdateModelLogEntry
from tapir.settings import PERMISSIONS, COOP_NAME
from tapir.utils.models import CountryField
from tapir.utils.user_utils import UserUtils

log = logging.getLogger(__name__)


class TapirUserQuerySet(models.QuerySet):
    def with_shift_attendance_mode(self, attendance_mode: str):
        return self.filter(shift_user_data__attendance_mode=attendance_mode)

    def registered_to_shift_slot_name(self, slot_name: str):
        return self.filter(
            shift_attendance_templates__slot_template__name=slot_name
        ).distinct()

    def registered_to_shift_slot_with_capability(self, capability: str):
        return self.filter(
            shift_attendance_templates__slot_template__required_capabilities__contains=[
                capability
            ]
        ).distinct()

    def has_capability(self, capability: str):
        return self.filter(
            shift_user_data__capabilities__contains=[capability]
        ).distinct()


class TapirUserManager(UserManager.from_queryset(TapirUserQuerySet)):
    use_in_migrations = True


class TapirUser(AbstractUser):
    username_validator = validators.UsernameValidator()

    # Copy-pasted from django/contrib/auth/models.py to override validators
    username = models.CharField(
        _("Username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and ./-/_ only."
        ),
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )

    phone_number = PhoneNumberField(_("Phone number"), blank=True)
    birthdate = models.DateField(_("Birthdate"), blank=True, null=True)
    street = models.CharField(_("Street and house number"), max_length=150, blank=True)
    street_2 = models.CharField(_("Extra address line"), max_length=150, blank=True)
    postcode = models.CharField(_("Postcode"), max_length=32, blank=True)
    city = models.CharField(_("City"), max_length=50, blank=True)
    country = CountryField(_("Country"), blank=True, default="DE")
    co_purchaser = models.CharField(_("Co-Purchaser"), max_length=150, blank=True)

    preferred_language = models.CharField(
        _("Preferred Language"),
        choices=utils.models.PREFERRED_LANGUAGES,
        default="de",
        max_length=16,
    )

    objects = TapirUserManager()

    def get_display_name(self):
        return UserUtils.build_display_name(self.first_name, self.last_name)

    def get_display_address(self):
        return UserUtils.build_display_address(
            self.street, self.street_2, self.postcode, self.city
        )

    def get_absolute_url(self):
        return reverse("accounts:user_detail", args=[self.pk])

    def get_email_from_template(
        self, subject_template_names: list, email_template_names: list
    ):
        # TODO(Leon Handreke): Should this be in views? Check in the django source how they do it.
        context = {
            "site_url": settings.SITE_URL,
            "uid": urlsafe_base64_encode(force_bytes(self.pk)),
            "tapir_user": self,
            "token": default_token_generator.make_token(self),
            "coop_name": COOP_NAME,
        }
        with translation.override(self.preferred_language):
            subject = loader.render_to_string(subject_template_names, context)
            # Email subject *must not* contain newlines
            subject = "".join(subject.splitlines())
            body = loader.render_to_string(email_template_names, context)
        email = EmailMultiAlternatives(subject, body, to=[self.email])
        email.content_subtype = "html"
        return email

    def has_perm(self, perm, obj=None):
        # This is a hack to allow permissions based on client certificates. ClientPermsMiddleware checks the
        # certificate in the request and adds the extra permissions the user object, which is accessible here.
        if hasattr(self, "client_perms") and perm in self.client_perms:
            return True

        return super().has_perm(perm=perm, obj=obj)

    def get_permissions_display(self):
        user_perms = [perm for perm in PERMISSIONS if self.has_perm(perm)]
        if len(user_perms) == 0:
            return _("None")
        return ", ".join(user_perms)


class UpdateTapirUserLogEntry(UpdateModelLogEntry):
    template_name = "accounts/log/update_tapir_user_log_entry.html"
    excluded_fields = ["password"]


def language_middleware(get_response):
    def middleware(request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            translation.activate(user.preferred_language)
        response = get_response(request)
        translation.deactivate()
        return response

    return middleware
