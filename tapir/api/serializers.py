from rest_framework import serializers

from tapir.accounts.models import TapirUser
from tapir.coop.models import ShareOwner
from tapir.shifts.models import Shift, ShiftUserData, ShiftAttendance


class ShiftSerializer(serializers.ModelSerializer):
    absolute_url = serializers.CharField(source="get_absolute_url", read_only=True)

    class Meta:
        model = Shift
        fields = "__all__"


class ShiftAttendanceSerializer(serializers.ModelSerializer):
    shift = ShiftSerializer(source="get_shift", read_only=True)

    class Meta:
        model = ShiftAttendance
        fields = "__all__"


class ShareOwnerSerializer(serializers.ModelSerializer):
    external_id = serializers.CharField(source="get_external_id", read_only=True)
    can_shop = serializers.BooleanField(read_only=True)
    num_shares = serializers.IntegerField(read_only=True)
    status = serializers.CharField(source="get_member_status", read_only=True)
    absolute_url = serializers.CharField(source="get_absolute_url", read_only=True)

    class Meta:
        model = ShareOwner
        fields = "__all__"


class ShiftUserDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftUserData
        fields = "__all__"


class TapirUserSerializer(serializers.ModelSerializer):
    share_owner = ShareOwnerSerializer(many=False, read_only=True)
    shift_user_data = ShiftUserDataSerializer(many=False, read_only=True)

    class Meta:
        model = TapirUser
        exclude = ["password"]
        depth = 1
