from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.datetime_safe import date
from django.views import generic
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST, require_GET

from tapir.coop import pdfs
from tapir.coop.config import COOP_SHARE_PRICE
from tapir.coop.emails.membership_confirmation_email_for_active_member import (
    MembershipConfirmationForActiveMemberEmail,
)
from tapir.coop.emails.membership_confirmation_email_for_investing_member import (
    MembershipConfirmationForInvestingMemberEmail,
)
from tapir.coop.forms import (
    DraftUserForm,
    DraftUserRegisterForm,
)
from tapir.coop.models import (
    DraftUser,
    ShareOwner,
    ShareOwnership,
    NewMembershipsForAccountingRecap,
)
from tapir.utils.models import copy_user_info


class DraftUserViewMixin:
    model = DraftUser
    form_class = DraftUserForm
    ordering = ["created_at"]


class DraftUserListView(PermissionRequiredMixin, DraftUserViewMixin, generic.ListView):
    permission_required = "coop.manage"


class DraftUserCreateView(
    PermissionRequiredMixin, DraftUserViewMixin, generic.CreateView
):
    permission_required = "coop.manage"


class DraftUserRegisterView(DraftUserViewMixin, generic.CreateView):
    form_class = DraftUserRegisterForm
    success_url = reverse_lazy("coop:draftuser_confirm_registration")

    def get_template_names(self):
        return [
            "coop/draftuser_register_form.html",
            "coop/draftuser_register_form.default.html",
        ]


class DraftUserConfirmRegistrationView(DraftUserViewMixin, generic.TemplateView):
    template_name = "coop/draftuser_confirm_registration.html"


class DraftUserUpdateView(
    PermissionRequiredMixin, DraftUserViewMixin, generic.UpdateView
):
    permission_required = "coop.manage"


class DraftUserDetailView(
    PermissionRequiredMixin, DraftUserViewMixin, generic.DetailView
):
    permission_required = "coop.manage"


class DraftUserDeleteView(
    PermissionRequiredMixin, DraftUserViewMixin, generic.DeleteView
):
    permission_required = "coop.manage"
    success_url = reverse_lazy("coop:draftuser_list")


@require_GET
@permission_required("coop.manage")
def draftuser_membership_agreement(request, pk):
    draft_user = get_object_or_404(DraftUser, pk=pk)
    filename = "Beteiligungserklärung %s %s.pdf" % (
        draft_user.first_name,
        draft_user.last_name,
    )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'filename="{}"'.format(filename)
    response.write(pdfs.get_membership_agreement_pdf(draft_user).write_pdf())
    return response


@require_POST
@csrf_protect
@permission_required("coop.manage")
def mark_signed_membership_agreement(request, pk):
    u = DraftUser.objects.get(pk=pk)
    u.signed_membership_agreement = True
    u.save()

    return redirect(u)


@require_POST
@csrf_protect
@permission_required("coop.manage")
def mark_attended_welcome_session(request, pk):
    u = DraftUser.objects.get(pk=pk)
    u.attended_welcome_session = True
    u.save()

    return redirect(u)


@require_POST
@csrf_protect
@permission_required("coop.manage")
def register_draftuser_payment(request, pk):
    draft = get_object_or_404(DraftUser, pk=pk)
    draft.paid_membership_fee = True
    draft.save()
    return redirect(draft.get_absolute_url())


@require_POST
@csrf_protect
@permission_required("coop.manage")
def create_share_owner_from_draft_user_view(request, pk):
    draft_user = DraftUser.objects.get(pk=pk)

    if not draft_user.can_create_user():
        raise ValidationError(
            "DraftUser is not ready (could be missing information or invalid amount of shares)"
        )

    with transaction.atomic():
        share_owner = create_share_owner_and_shares_from_draft_user(draft_user)
        draft_user.delete()

        NewMembershipsForAccountingRecap.objects.create(
            member=share_owner,
            number_of_shares=share_owner.get_active_share_ownerships().count(),
            date=timezone.now().date(),
        )

        email = (
            MembershipConfirmationForInvestingMemberEmail
            if share_owner.is_investing
            else MembershipConfirmationForActiveMemberEmail
        )(share_owner=share_owner)
        email.send_to_share_owner(actor=request.user, recipient=share_owner)

    return redirect(share_owner.get_absolute_url())


def create_share_owner_and_shares_from_draft_user(draft_user: DraftUser) -> ShareOwner:
    share_owner = ShareOwner.objects.create(
        is_company=False,
        is_investing=draft_user.is_investing,
        ratenzahlung=draft_user.ratenzahlung,
        attended_welcome_session=draft_user.attended_welcome_session,
        paid_membership_fee=draft_user.paid_membership_fee,
    )

    copy_user_info(draft_user, share_owner)
    share_owner.save()

    for _ in range(0, draft_user.num_shares):
        ShareOwnership.objects.create(
            owner=share_owner,
            start_date=date.today(),
            amount_paid=(COOP_SHARE_PRICE if draft_user.paid_shares else 0),
        )

    return share_owner
