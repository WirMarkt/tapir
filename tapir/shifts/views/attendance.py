from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.mail import EmailMessage
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone, translation
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    UpdateView,
    FormView,
)

from tapir import settings
from tapir.settings import FROM_EMAIL_MEMBER_OFFICE
from tapir.shifts.forms import (
    ShiftAttendanceTemplateForm,
    UpdateShiftAttendanceForm,
    RegisterUserToShiftSlotForm,
)
from tapir.shifts.models import (
    ShiftAttendance,
    ShiftAttendanceTemplate,
    ShiftSlot,
    ShiftSlotTemplate,
    CreateShiftAttendanceTemplateLogEntry,
    DeleteShiftAttendanceTemplateLogEntry,
    CreateShiftAttendanceLogEntry,
    UpdateShiftAttendanceStateLogEntry,
)
from tapir.shifts.views.views import SelectedUserViewMixin
from tapir.utils.shortcuts import safe_redirect


class RegisterUserToShiftSlotTemplateView(
    PermissionRequiredMixin, SelectedUserViewMixin, CreateView
):
    permission_required = "shifts.manage"
    model = ShiftAttendanceTemplate
    template_name = "shifts/register_user_to_shift_slot_template.html"
    form_class = ShiftAttendanceTemplateForm

    def get_initial(self):
        return {"user": self.get_selected_user()}

    def get_slot_template(self):
        return get_object_or_404(ShiftSlotTemplate, pk=self.kwargs["slot_template_pk"])

    def get_context_data(self, **kwargs):
        slot_template = self.get_slot_template()
        kwargs["slot_template"] = slot_template

        blocked_slots = []
        for slot in slot_template.generated_slots.filter(
            shift__start_time__gte=timezone.now()
        ):
            attendance = slot.get_valid_attendance()
            if attendance is not None:
                blocked_slots.append(slot)
        kwargs["blocked_slots"] = blocked_slots

        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        form.instance.slot_template = self.get_slot_template()
        with transaction.atomic():
            response = super().form_valid(form)

            shift_attendance_template: ShiftAttendanceTemplate = self.object

            for (
                shift
            ) in shift_attendance_template.slot_template.shift_template.generated_shifts.filter(
                start_time__gt=timezone.now()
            ):
                # Check for future cancelled shifts, the user should get a point.
                attendance = ShiftAttendance.objects.filter(
                    user=shift_attendance_template.user, slot__shift=shift
                ).first()
                if not shift.cancelled or not attendance:
                    continue
                attendance.state = ShiftAttendance.State.MISSED_EXCUSED
                attendance.save()
                attendance.update_shift_account_entry(shift.cancelled_reason)

            log_entry = CreateShiftAttendanceTemplateLogEntry().populate(
                actor=self.request.user,
                user=self.object.user,
                model=shift_attendance_template,
            )
            log_entry.slot_template_name = self.object.slot_template.name
            log_entry.shift_template = self.object.slot_template.shift_template
            log_entry.save()

        return response

    def get_success_url(self):
        if self.get_selected_user():
            return self.get_selected_user().get_absolute_url()
        return self.object.slot_template.shift_template.get_absolute_url()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"slot_template_pk": self.kwargs["slot_template_pk"]})
        return kwargs


class UpdateShiftAttendanceStateBase(PermissionRequiredMixin, UpdateView):
    model = ShiftAttendance
    get_state_from_kwargs = True

    def get_attendance(self):
        return ShiftAttendance.objects.get(pk=self.kwargs["pk"])

    def get_permission_required(self):
        state = self.kwargs["state"]
        self_unregister = (
            state == ShiftAttendance.State.CANCELLED
            and self.get_attendance().slot.user_can_self_unregister(self.request.user)
        )
        look_for_standing = (
            state == ShiftAttendance.State.LOOKING_FOR_STAND_IN
            and self.get_attendance().slot.user_can_look_for_standin(self.request.user)
        )
        cancel_look_for_standing = (
            state == ShiftAttendance.State.PENDING
            and self.get_attendance().state
            == ShiftAttendance.State.LOOKING_FOR_STAND_IN
        )
        if self_unregister or look_for_standing or cancel_look_for_standing:
            return []
        return ["shifts.manage"]

    def get_success_url(self):
        return self.get_object().slot.shift.get_absolute_url()

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)

            attendance = self.get_attendance()
            if self.get_state_from_kwargs:
                attendance.state = self.kwargs["state"]
                attendance.save()

            log_entry = UpdateShiftAttendanceStateLogEntry().populate(
                actor=self.request.user,
                user=attendance.user,
                model=attendance,
            )
            log_entry.slot_name = attendance.slot.name
            log_entry.shift = attendance.slot.shift
            log_entry.state = attendance.state
            log_entry.save()

            if attendance.state == ShiftAttendance.State.MISSED:
                self.send_shift_missed_email()

            description = None
            if "description" in form.data:
                description = form.data["description"]
            attendance.update_shift_account_entry(description)

            return response

    def send_shift_missed_email(self):
        attendance = self.get_attendance()

        with translation.override(attendance.user.preferred_language):
            mail = EmailMessage(
                subject=_("You missed your shift!"),
                body=render_to_string(
                    [
                        "shifts/email/shift_missed.html",
                        "shifts/email/shift_missed.default.html",
                    ],
                    {
                        "tapir_user": attendance.user,
                        "shift": attendance.slot.shift,
                        "contact_email_address": settings.EMAIL_ADDRESS_MEMBER_OFFICE,
                        "coop_name": settings.COOP_NAME,
                    },
                ),
                from_email=FROM_EMAIL_MEMBER_OFFICE,
                to=[attendance.user.email],
            )
            mail.content_subtype = "html"
            mail.send()


class UpdateShiftAttendanceStateView(UpdateShiftAttendanceStateBase):
    fields = []


class UpdateShiftAttendanceStateWithFormView(UpdateShiftAttendanceStateBase):
    form_class = UpdateShiftAttendanceForm
    get_state_from_kwargs = False

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"state": self.kwargs["state"]})
        return kwargs


@require_POST
@csrf_protect
@permission_required("shifts.manage")
def shift_attendance_template_delete(request, pk):
    shift_attendance_template = get_object_or_404(ShiftAttendanceTemplate, pk=pk)
    slot_template = shift_attendance_template.slot_template

    with transaction.atomic():
        log_entry = DeleteShiftAttendanceTemplateLogEntry().populate(
            actor=request.user,
            user=shift_attendance_template.user,
            model=shift_attendance_template,
        )
        log_entry.slot_template_name = slot_template.name
        log_entry.shift_template = slot_template.shift_template
        log_entry.save()

        shift_attendance_template.cancel_attendances(timezone.now())
        shift_attendance_template.delete()

    return safe_redirect(request.GET.get("next"), slot_template.shift_template, request)


class RegisterUserToShiftSlotView(PermissionRequiredMixin, FormView):
    template_name = "shifts/register_user_to_shift_slot.html"
    form_class = RegisterUserToShiftSlotForm

    def get_permission_required(self):
        if self.get_slot().user_can_attend(self.request.user):
            return []
        return ["shifts.manage"]

    def get_slot(self) -> ShiftSlot:
        return get_object_or_404(ShiftSlot, pk=self.kwargs["slot_pk"])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(
            {
                "slot": self.get_slot(),
                "request_user": self.request.user,
            }
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["slot"] = self.get_slot()
        return context

    def get_initial(self):
        if self.request.user.has_perm("shifts.manage"):
            return {}
        return {"user": self.request.user}

    def get_success_url(self):
        return self.get_slot().shift.get_absolute_url()

    def form_valid(self, form):
        response = super().form_valid(form)
        slot = self.get_slot()
        user_to_register = form.cleaned_data["user"]

        with transaction.atomic():
            attendance = ShiftAttendance.objects.create(
                user=user_to_register, slot=slot
            )
            slot.mark_stand_in_found_if_relevant(self.request.user)
            log_entry = CreateShiftAttendanceLogEntry().populate(
                actor=self.request.user,
                user=user_to_register,
                model=attendance,
            )
            log_entry.slot_name = attendance.slot.name
            log_entry.shift = attendance.slot.shift
            log_entry.save()

        return response
