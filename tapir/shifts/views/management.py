from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import transaction
from django.views.generic import CreateView, UpdateView

from tapir.shifts.forms import ShiftCreateForm, ShiftSlotForm, ShiftCancelForm
from tapir.shifts.models import Shift, ShiftSlot, ShiftAttendance


class ShiftCreateView(PermissionRequiredMixin, CreateView):
    model = Shift
    form_class = ShiftCreateForm
    permission_required = "shifts.manage"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["card_title"] = f"Creating a shift"
        return context


class ShiftSlotCreateView(PermissionRequiredMixin, CreateView):
    model = ShiftSlot
    form_class = ShiftSlotForm
    permission_required = "shifts.manage"

    def get_shift(self):
        return Shift.objects.get(pk=self.kwargs.get("shift_pk"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[
            "shift_name"
        ] = f"Adding a slot to {self.get_shift().get_display_name()}"
        return context

    def form_valid(self, form):
        form.instance.shift = self.get_shift()
        return super().form_valid(form)

    def get_success_url(self):
        return self.get_shift().get_absolute_url()


class ShiftSlotEditView(PermissionRequiredMixin, UpdateView):
    model = ShiftSlot
    form_class = ShiftSlotForm
    permission_required = "shifts.manage"

    def get_success_url(self):
        return self.object.shift.get_absolute_url()


class CancelShiftView(PermissionRequiredMixin, UpdateView):
    permission_required = "shifts.manage"
    model = Shift
    form_class = ShiftCancelForm
    template_name = "shifts/cancel_shift.html"

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)

            shift: Shift = form.instance
            shift.cancelled = True
            shift.save()

            for slot in shift.slots.all():
                attendance = slot.get_valid_attendance()
                if not attendance:
                    continue
                if (
                    hasattr(slot.slot_template, "attendance_template")
                    and slot.slot_template.attendance_template.user == attendance.user
                ):
                    attendance.state = ShiftAttendance.State.MISSED_EXCUSED
                    attendance.excused_reason = "Shift cancelled"
                    attendance.save()
                    attendance.update_shift_account_entry()
                else:
                    attendance.state = ShiftAttendance.State.CANCELLED
                    attendance.save()

            return response


class EditShiftView(PermissionRequiredMixin, UpdateView):
    permission_required = "shifts.manage"
    model = Shift
    form_class = ShiftCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["card_title"] = f"Editing shift: {self.object.get_display_name()}"
        return context
