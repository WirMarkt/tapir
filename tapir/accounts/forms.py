from django import forms
from django.forms import TextInput

from tapir.accounts.models import TapirUser
from tapir.utils.forms import DateInputTapir, TapirPhoneNumberField


class TapirUserForm(forms.ModelForm):
    phone_number = TapirPhoneNumberField(required=False)

    class Meta:
        model = TapirUser
        fields = [
            "first_name",
            "last_name",
            "username",
            "phone_number",
            "email",
            "birthdate",
            "street",
            "street_2",
            "postcode",
            "city",
            "preferred_language",
            "co_purchaser",
        ]
        widgets = {
            "birthdate": DateInputTapir(),
            "username": TextInput(attrs={"readonly": True}),
        }
