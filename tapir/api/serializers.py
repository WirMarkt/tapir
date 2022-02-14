from rest_framework import serializers


class MemberContributionSerializer(serializers.Serializer):
    status = serializers.CharField()
    attended_welcome_session = serializers.BooleanField()
    next_shift_name = serializers.CharField()
    next_shift_attendance_state = serializers.IntegerField()
    next_shift_id = serializers.CharField()
    next_shift_url = serializers.CharField()
    next_shift_start_time_epoch_ms = serializers.IntegerField()
    next_shift_end_time_epoch_ms = serializers.IntegerField()
    sepa_account_holder = serializers.CharField()
    sepa_iban = serializers.CharField()
    signed_sepa_mandate = serializers.BooleanField()
    is_investing = serializers.BooleanField()
    share_count = serializers.IntegerField()


class MemberInfoSerializer(serializers.Serializer):
    email = serializers.CharField()
    preferred_language = serializers.CharField()
    can_shop = serializers.BooleanField()
