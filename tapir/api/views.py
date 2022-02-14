from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from tapir.api.models import MemberContribution, MemberInfo
from tapir.api.serializers import (
    MemberInfoSerializer,
    MemberContributionSerializer,
)
from tapir.shifts.models import ShiftAttendance


class MemberInfoView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def get(request):
        member_info = MemberInfo(request.user)
        serializer = MemberInfoSerializer(member_info)
        return Response(serializer.data)


class MemberContributionView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def get(request):
        if hasattr(request.user, "share_owner"):
            share_owner = request.user.share_owner
            next_shift_attendance: ShiftAttendance = (
                request.user.shift_user_data.get_upcoming_shift_attendances().first()
            )
            serializer = MemberContributionSerializer(
                MemberContribution(share_owner, next_shift_attendance),
                context={"request": request},
            )
        else:
            serializer = MemberContributionSerializer(
                MemberContribution(None, None), context={"request": request}
            )
        return Response(serializer.data)
