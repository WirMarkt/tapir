from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from tapir.api.serializers import (
    ShiftSerializer,
    ShareOwnerSerializer,
    TapirUserSerializer,
    ShiftAttendanceSerializer,
)
from tapir.coop.models import ShareOwner
from tapir.shifts.models import ShiftAttendance, Shift


class UpcomingShiftAttendanceView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def get(request):
        upcoming_shift_attendance: ShiftAttendance = (
            request.user.shift_user_data.get_upcoming_shift_attendances().first()
        )

        serializer = ShiftAttendanceSerializer(
            upcoming_shift_attendance,
            context={"request": request},
        )
        return Response(serializer.data)


class ShareOwnerView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def get(request):
        share_owner: ShareOwner = None
        if hasattr(request.user, "share_owner"):
            share_owner = request.user.share_owner

        serializer = ShareOwnerSerializer(share_owner, context={"request": request})
        return Response(serializer.data)


class TapirUserView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def get(request):
        serializer = TapirUserSerializer(request.user, context={"request": request})
        return Response(serializer.data)
