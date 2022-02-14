from django.conf import settings
from django.db import models

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner
from tapir.shifts.models import Shift


class MemberContribution(models.Model):
    status: str
    attended_welcome_session: bool
    next_shift_name: str
    next_shift_attendance_state: int
    next_shift_url: str
    next_shift_id: str
    next_shift_start_time_epoch_ms: int
    next_shift_end_time_epoch_ms: int
    sepa_account_holder: str
    sepa_iban: str
    signed_sepa_mandate: bool
    is_investing: bool
    share_count: int

    # noinspection PyTypeChecker
    def __init__(self, share_owner, next_shift_attendance, *args, **kwargs):
        super().__init__(*args, **kwargs)

        next_shift: Shift = None

        if next_shift_attendance:
            next_shift: Shift = next_shift_attendance.slot.shift

        self.status = share_owner.get_member_status() if share_owner else None
        self.attended_welcome_session = (
            share_owner.attended_welcome_session if share_owner else None
        )
        self.next_shift_name = next_shift.name if next_shift else None
        self.next_shift_attendance_state = (
            next_shift_attendance.state if next_shift_attendance else None
        )
        self.next_shift_url = (
            settings.SITE_URL + next_shift.get_absolute_url() if next_shift else None
        )
        self.next_shift_id = next_shift.pk if next_shift else None
        self.next_shift_start_time_epoch_ms = (
            int(next_shift.start_time.timestamp() * 1000) if next_shift else None
        )

        self.next_shift_end_time_epoch_ms = (
            int(next_shift.end_time.timestamp() * 1000) if next_shift else None
        )
        self.sepa_account_holder = (
            share_owner.sepa_account_holder if next_shift else None
        )
        self.sepa_iban = share_owner.sepa_iban if next_shift else None
        self.signed_sepa_mandate = (
            share_owner.signed_sepa_mandate if next_shift else None
        )
        self.is_investing = share_owner.is_investing
        self.share_count = share_owner.num_shares()


class MemberInfo(models.Model):
    email: str
    preferred_language: str
    can_shop: bool

    def __init__(self, user: TapirUser, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.email = user.email
        self.preferred_language = user.preferred_language

        if hasattr(user, "share_owner"):
            share_owner: ShareOwner = user.share_owner
            self.can_shop = share_owner.can_shop()
        else:
            self.can_shop = False
