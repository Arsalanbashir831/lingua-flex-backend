# bookings/views_enhanced.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models, transaction
from datetime import datetime, timedelta
from .models import TeacherAvailability, SessionBooking
from .serializers import (
    TeacherAvailabilitySerializer,
    SessionBookingSerializer,
)
from .zoom_service import ZoomService
from core.models import User
import logging

logger = logging.getLogger(__name__)


class TeacherAvailabilityViewSet(viewsets.ModelViewSet):
    serializer_class = TeacherAvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.action == "list":
            teacher_id = self.request.query_params.get("teacher_id")
            if teacher_id:
                return TeacherAvailability.objects.filter(teacher_id=teacher_id)
        return TeacherAvailability.objects.filter(teacher=self.request.user)

    def perform_create(self, serializer):
        """Only teachers can create availability slots"""
        if self.request.user.role != User.Role.TEACHER:
            raise permissions.PermissionDenied(
                "Only teachers can create availability slots"
            )
        serializer.save(teacher=self.request.user)

    def perform_update(self, serializer):
        """Only teachers can update their own availability slots"""
        if self.request.user.role != User.Role.TEACHER:
            raise permissions.PermissionDenied(
                "Only teachers can update availability slots"
            )

        # Ensure teacher can only update their own availability
        availability = self.get_object()
        if availability.teacher != self.request.user:
            raise permissions.PermissionDenied(
                "You can only update your own availability slots"
            )

        serializer.save()

    def perform_destroy(self, instance):
        """Only teachers can delete their own availability slots"""
        if self.request.user.role != User.Role.TEACHER:
            raise permissions.PermissionDenied(
                "Only teachers can delete availability slots"
            )

        # Ensure teacher can only delete their own availability
        if instance.teacher != self.request.user:
            raise permissions.PermissionDenied(
                "You can only delete your own availability slots"
            )

        instance.delete()

    @action(detail=False, methods=["get"])
    def weekly_availability(self, request):
        """Get teacher's weekly availability schedule"""
        teacher_id = request.query_params.get("teacher_id")

        if not teacher_id:
            return Response(
                {"error": "teacher_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Verify teacher exists
        try:
            teacher = User.objects.get(id=teacher_id, role=User.Role.TEACHER)
        except User.DoesNotExist:
            return Response(
                {"error": "Teacher not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Get all recurring availability slots for the teacher
        availabilities = TeacherAvailability.objects.filter(
            teacher_id=teacher_id, is_recurring=True
        ).order_by("day_of_week", "start_time")

        # Group availabilities by day of week
        day_names = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        weekly_schedule = {}

        # Initialize empty schedule for all days
        for day_num, day_name in enumerate(day_names):
            weekly_schedule[day_name] = {
                "day_of_week": day_num,
                "day_name": day_name,
                "available": False,
                "slots": [],
            }

        # Fill in availability slots
        for availability in availabilities:
            day_name = day_names[availability.day_of_week]
            weekly_schedule[day_name]["available"] = True
            weekly_schedule[day_name]["slots"].append(
                {
                    "id": availability.id,
                    "start_time": availability.start_time.strftime("%H:%M:%S"),
                    "end_time": availability.end_time.strftime("%H:%M:%S"),
                    "duration_hours": (
                        datetime.combine(datetime.today(), availability.end_time)
                        - datetime.combine(datetime.today(), availability.start_time)
                    ).total_seconds()
                    / 3600,
                }
            )

        # Get teacher profile info for response
        teacher_info = {
            "id": teacher.id,
            "name": f"{teacher.first_name} {teacher.last_name}",
            "email": teacher.email,
        }

        # Add teacher profile details if available
        try:
            from accounts.models import TeacherProfile

            teacher_profile = TeacherProfile.objects.select_related("user").get(
                user_id=teacher_id
            )
            teacher_info.update(
                {
                    "profile_picture": teacher_profile.profile_picture,
                    "bio": teacher_profile.bio,
                    "languages": teacher_profile.languages,
                    "hourly_rate": teacher_profile.hourly_rate,
                    "experience_years": teacher_profile.experience_years,
                    "specializations": teacher_profile.specializations,
                }
            )
        except Exception as e:
            logger.error(f"Error fetching teacher profile for {teacher_id}: {str(e)}")
            pass  # Teacher profile might not exist or other non-critical error

        # Calculate summary statistics
        total_slots = sum(len(day["slots"]) for day in weekly_schedule.values())
        available_days = sum(1 for day in weekly_schedule.values() if day["available"])
        total_hours = sum(
            sum(slot["duration_hours"] for slot in day["slots"])
            for day in weekly_schedule.values()
        )

        return Response(
            {
                "teacher": teacher_info,
                "weekly_schedule": weekly_schedule,
                "summary": {
                    "total_availability_slots": total_slots,
                    "available_days_count": available_days,
                    "total_weekly_hours": round(total_hours, 2),
                    "days_with_availability": [
                        day_name
                        for day_name, day_data in weekly_schedule.items()
                        if day_data["available"]
                    ],
                },
            }
        )

    @action(detail=False, methods=["post"])
    def bulk_create(self, request):
        """Create multiple availability slots at once for the week"""
        if request.user.role != User.Role.TEACHER:
            return Response(
                {"error": "Only teachers can create availability slots"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Handle both array of objects and wrapped format
        if isinstance(request.data, list):
            # Direct array format [{"day_of_week": 0, ...}, {"day_of_week": 1, ...}]
            availabilities_data = request.data
        elif isinstance(request.data, dict) and "availabilities" in request.data:
            # Wrapped format {"availabilities": [{"day_of_week": 0, ...}, ...]}
            availabilities_data = request.data["availabilities"]
        else:
            return Response(
                {
                    "error": "Invalid data format. Expected array of availability objects or {'availabilities': [...]}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate that we have data
        if not availabilities_data:
            return Response(
                {"error": "At least one availability slot is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Use transaction to ensure all or nothing creation
        try:
            with transaction.atomic():
                created_availabilities = []
                errors = []

                for i, availability_data in enumerate(availabilities_data):
                    # Add teacher to each availability
                    availability_data["teacher"] = request.user.id

                    # Validate individual availability
                    serializer = TeacherAvailabilitySerializer(
                        data=availability_data, context={"request": request}
                    )

                    if serializer.is_valid():
                        # Check if this exact availability already exists
                        existing = TeacherAvailability.objects.filter(
                            teacher=request.user,
                            day_of_week=availability_data["day_of_week"],
                            start_time=availability_data["start_time"],
                            end_time=availability_data["end_time"],
                            is_recurring=availability_data.get("is_recurring", True),
                        ).first()

                        if existing:
                            # Update existing availability
                            for key, value in availability_data.items():
                                if key not in ["teacher"]:
                                    setattr(existing, key, value)
                            existing.save()
                            created_availabilities.append(existing)
                        else:
                            # Create new availability
                            availability = serializer.save(teacher=request.user)
                            created_availabilities.append(availability)
                    else:
                        errors.append(
                            {
                                "index": i,
                                "data": availability_data,
                                "errors": serializer.errors,
                            }
                        )

                # If there are validation errors, return them
                if errors:
                    return Response(
                        {
                            "error": "Validation failed for some availability slots",
                            "details": errors,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Serialize the created/updated availabilities for response
                response_serializer = TeacherAvailabilitySerializer(
                    created_availabilities, many=True
                )

                return Response(
                    {
                        "message": f"Successfully created/updated {len(created_availabilities)} availability slots",
                        "availabilities": response_serializer.data,
                    },
                    status=status.HTTP_201_CREATED,
                )

        except Exception as e:
            return Response(
                {"error": f"Failed to create availability slots: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["put"])
    def replace_weekly_schedule(self, request):
        """Replace entire weekly schedule for teacher"""
        if request.user.role != User.Role.TEACHER:
            return Response(
                {"error": "Only teachers can replace availability schedule"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Handle both array of objects and wrapped format
        if isinstance(request.data, list):
            new_availabilities_data = request.data
        elif isinstance(request.data, dict) and "availabilities" in request.data:
            new_availabilities_data = request.data["availabilities"]
        else:
            return Response(
                {
                    "error": "Invalid data format. Expected array of availability objects or {'availabilities': [...]}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                # Delete all existing recurring availabilities for the teacher
                TeacherAvailability.objects.filter(
                    teacher=request.user, is_recurring=True
                ).delete()

                # Create new availabilities
                created_availabilities = []
                errors = []

                for i, availability_data in enumerate(new_availabilities_data):
                    availability_data["teacher"] = request.user.id
                    availability_data["is_recurring"] = (
                        True  # Force recurring for weekly schedule
                    )

                    serializer = TeacherAvailabilitySerializer(
                        data=availability_data, context={"request": request}
                    )

                    if serializer.is_valid():
                        availability = serializer.save(teacher=request.user)
                        created_availabilities.append(availability)
                    else:
                        errors.append(
                            {
                                "index": i,
                                "data": availability_data,
                                "errors": serializer.errors,
                            }
                        )

                if errors:
                    return Response(
                        {
                            "error": "Validation failed for some availability slots",
                            "details": errors,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Serialize the created availabilities for response
                response_serializer = TeacherAvailabilitySerializer(
                    created_availabilities, many=True
                )

                return Response(
                    {
                        "message": f"Successfully replaced weekly schedule with {len(created_availabilities)} availability slots",
                        "availabilities": response_serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )

        except Exception as e:
            return Response(
                {"error": f"Failed to replace weekly schedule: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SessionBookingViewSet(viewsets.ModelViewSet):
    serializer_class = SessionBookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return (
            SessionBooking.objects.filter(
                models.Q(student=user) | models.Q(teacher=user)
            )
            .select_related("student", "teacher", "gig", "payment")
            .order_by("-start_time")
        )

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create a booking request"""
        teacher_id = request.data.get("teacher")
        if teacher_id and str(teacher_id) == str(request.user.id):
            return Response(
                {"error": "You cannot schedule a booking with yourself"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create the booking
        booking = serializer.save(student=request.user, status="CONFIRMED")

        # Check if this is a video call session - if so, create Zoom meeting
        session_type = request.data.get("session_type", "video_call")
        if session_type == "video_call":
            zoom_service = ZoomService()
            try:
                zoom_result = zoom_service.create_meeting(booking)

                if zoom_result["success"]:
                    booking.zoom_meeting_id = str(zoom_result["meeting_id"])
                    booking.zoom_join_url = zoom_result["join_url"]
                    booking.zoom_start_url = zoom_result.get("start_url", "")
                    booking.zoom_password = zoom_result.get("password", "")
                    booking.save()

                    # Include Zoom info in response
                    response_data = SessionBookingSerializer(
                        booking, context={"request": request}
                    ).data
                    response_data.update(
                        {
                            "zoom_meeting_id": zoom_result["meeting_id"],
                            "zoom_join_url": zoom_result["join_url"],
                            "zoom_start_url": zoom_result.get("start_url", ""),
                            "zoom_password": zoom_result.get("password", ""),
                        }
                    )

                    return Response(response_data, status=status.HTTP_201_CREATED)
                else:
                    # If Zoom creation fails, still create the booking but without Zoom
                    return Response(
                        {
                            **SessionBookingSerializer(
                                booking, context={"request": request}
                            ).data,
                            "warning": f"Booking created but Zoom meeting failed: {zoom_result.get('error', 'Unknown error')}",
                        },
                        status=status.HTTP_201_CREATED,
                    )

            except Exception as e:
                # If Zoom creation fails, still create the booking but without Zoom
                return Response(
                    {
                        **SessionBookingSerializer(
                            booking, context={"request": request}
                        ).data,
                        "warning": f"Booking created but Zoom meeting failed: {str(e)}",
                    },
                    status=status.HTTP_201_CREATED,
                )

        # For non-video sessions, just return the booking
        return Response(
            SessionBookingSerializer(booking, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """Confirm a booking and create Zoom meeting (teachers only)"""
        booking = self.get_object()

        if request.user != booking.teacher:
            return Response(
                {"error": "Only the assigned teacher can confirm this booking"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if booking.status != "PENDING":
            return Response(
                {"error": "Only pending bookings can be confirmed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if Zoom meeting already exists
        if booking.zoom_meeting_id and booking.zoom_join_url:
            # Meeting already exists, just confirm the booking
            booking.status = "CONFIRMED"
            booking.save()

            return Response(
                {
                    "message": "Booking confirmed (Zoom meeting already exists)",
                    "booking": SessionBookingSerializer(booking).data,
                    "zoom_info": {
                        "join_url": booking.zoom_join_url,
                        "meeting_id": booking.zoom_meeting_id,
                        "password": booking.zoom_password or "",
                    },
                }
            )

        # Create new Zoom meeting only if one doesn't exist
        zoom_service = ZoomService()
        try:
            zoom_result = zoom_service.create_meeting(booking)

            if zoom_result["success"]:
                booking.zoom_meeting_id = str(zoom_result["meeting_id"])
                booking.zoom_join_url = zoom_result["join_url"]
                booking.zoom_start_url = zoom_result.get("start_url", "")
                booking.zoom_password = zoom_result.get("password", "")
                booking.status = "CONFIRMED"
                booking.save()

                return Response(
                    {
                        "message": "Booking confirmed and Zoom meeting created",
                        "booking": SessionBookingSerializer(booking).data,
                        "zoom_info": {
                            "join_url": zoom_result["join_url"],
                            "meeting_id": zoom_result["meeting_id"],
                            "password": zoom_result.get("password", ""),
                        },
                    }
                )
            else:
                return Response(
                    {"error": f"Failed to create Zoom meeting: {zoom_result['error']}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception as e:
            return Response(
                {"error": f"Error creating Zoom meeting: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a booking"""
        booking = self.get_object()
        reason = request.data.get("reason", "")

        # Only student or teacher can cancel their own bookings
        if request.user not in [booking.student, booking.teacher]:
            return Response(
                {"error": "You can only cancel your own bookings"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if booking.status not in ["PENDING", "CONFIRMED"]:
            return Response(
                {"error": "Cannot cancel completed or already cancelled sessions"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Cancel Zoom meeting if it exists
        if booking.zoom_meeting_id:
            zoom_service = ZoomService()
            try:
                zoom_service.delete_meeting(booking.zoom_meeting_id)
            except Exception as e:
                # Log the error but don't fail the cancellation
                print(
                    f"Warning: Failed to delete Zoom meeting {booking.zoom_meeting_id}: {e}"
                )

        booking.cancel(reason)

        return Response(
            {
                "message": "Booking cancelled successfully",
                "booking": SessionBookingSerializer(booking).data,
            }
        )

    @action(detail=True, methods=["post"])
    def reschedule(self, request, pk=None):
        """Reschedule a booking"""
        booking = self.get_object()

        # Support both parameter formats for flexibility
        new_start_time_str = request.data.get("new_start_time") or request.data.get(
            "start_time"
        )
        new_end_time_str = request.data.get("new_end_time") or request.data.get(
            "end_time"
        )
        duration = request.data.get("duration", 60)
        reason = request.data.get("reason", "")

        if not new_start_time_str:
            return Response(
                {"error": "new_start_time or start_time is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Only student or teacher can reschedule
        if request.user not in [booking.student, booking.teacher]:
            return Response(
                {"error": "You can only reschedule your own bookings"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if booking.status not in ["PENDING", "CONFIRMED"]:
            return Response(
                {"error": "Cannot reschedule completed or cancelled sessions"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            new_start_time = datetime.fromisoformat(
                new_start_time_str.replace("Z", "+00:00")
            )

            # Calculate end time based on provided end_time or duration
            if new_end_time_str:
                new_end_time = datetime.fromisoformat(
                    new_end_time_str.replace("Z", "+00:00")
                )
            else:
                new_end_time = new_start_time + timedelta(minutes=int(duration))
        except ValueError:
            return Response(
                {
                    "error": "Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SSZ)"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_start_time >= new_end_time:
            return Response(
                {"error": "Start time must be before end time"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if new time slot is available
        conflicting_booking = (
            SessionBooking.objects.filter(
                teacher=booking.teacher,
                start_time__lt=new_end_time,
                end_time__gt=new_start_time,
                status__in=["PENDING", "CONFIRMED"],
            )
            .exclude(id=booking.id)
            .exists()
        )

        if conflicting_booking:
            return Response(
                {"error": "New time slot is not available"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Store old times for response
        old_start = booking.start_time
        old_end = booking.end_time

        # Update booking
        booking.start_time = new_start_time
        booking.end_time = new_end_time

        # Update Zoom meeting if it exists
        if booking.zoom_meeting_id:
            zoom_service = ZoomService()
            try:
                zoom_service.update_meeting(booking.zoom_meeting_id, booking)
            except Exception as e:
                return Response(
                    {"error": f"Failed to update Zoom meeting: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        booking.save()

        return Response(
            {
                "message": "Booking rescheduled successfully",
                "changes": {
                    "old_start_time": old_start,
                    "old_end_time": old_end,
                    "new_start_time": new_start_time,
                    "new_end_time": new_end_time,
                    "reason": reason,
                },
                "booking": SessionBookingSerializer(
                    booking, context={"request": request}
                ).data,
            }
        )

    @action(detail=True, methods=["post"])
    def request_reschedule(self, request, pk=None):
        """Request a reschedule that requires confirmation from the other party"""
        booking = self.get_object()

        # Get required data
        new_start_time_str = request.data.get("new_start_time") or request.data.get(
            "start_time"
        )
        new_end_time_str = request.data.get("new_end_time") or request.data.get(
            "end_time"
        )
        duration = request.data.get("duration", 60)
        reason = request.data.get("reason", "")

        if not new_start_time_str:
            return Response(
                {"error": "new_start_time or start_time is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Only student or teacher can request reschedule
        if request.user not in [booking.student, booking.teacher]:
            return Response(
                {"error": "You can only request reschedule for your own bookings"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Can't request reschedule for completed or cancelled sessions
        if booking.status not in ["PENDING", "CONFIRMED"]:
            return Response(
                {
                    "error": "Cannot request reschedule for completed or cancelled sessions"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if there's already a pending reschedule request
        if booking.reschedule_request_status == "PENDING":
            return Response(
                {
                    "error": "There is already a pending reschedule request for this booking"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            new_start_time = datetime.fromisoformat(
                new_start_time_str.replace("Z", "+00:00")
            )

            # Calculate end time based on provided end_time or duration
            if new_end_time_str:
                new_end_time = datetime.fromisoformat(
                    new_end_time_str.replace("Z", "+00:00")
                )
            else:
                new_end_time = new_start_time + timedelta(minutes=int(duration))
        except ValueError:
            return Response(
                {
                    "error": "Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SSZ)"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_start_time >= new_end_time:
            return Response(
                {"error": "Start time must be before end time"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if new time slot is available
        conflicting_booking = (
            SessionBooking.objects.filter(
                teacher=booking.teacher,
                start_time__lt=new_end_time,
                end_time__gt=new_start_time,
                status__in=["PENDING", "CONFIRMED"],
            )
            .exclude(id=booking.id)
            .exists()
        )

        if conflicting_booking:
            return Response(
                {"error": "Requested time slot is not available"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Determine who is requesting the reschedule
        if request.user == booking.student:
            requested_by = "STUDENT"
        else:
            requested_by = "TEACHER"

        # Update booking with reschedule request data
        booking.reschedule_request_status = "PENDING"
        booking.reschedule_requested_by = requested_by
        booking.reschedule_request_start_time = new_start_time
        booking.reschedule_request_end_time = new_end_time
        booking.reschedule_request_reason = reason
        booking.save()

        # Get the other party's information
        other_party = (
            booking.teacher if request.user == booking.student else booking.student
        )

        return Response(
            {
                "message": "Reschedule request sent successfully",
                "reschedule_request": {
                    "requested_by": requested_by,
                    "status": "PENDING",
                    "requested_start_time": new_start_time,
                    "requested_end_time": new_end_time,
                    "reason": reason,
                    "awaiting_response_from": other_party.email,
                },
                "booking": SessionBookingSerializer(
                    booking, context={"request": request}
                ).data,
            }
        )

    @action(detail=True, methods=["post"])
    def respond_reschedule(self, request, pk=None):
        """Respond to a reschedule request (confirm or decline)"""
        booking = self.get_object()

        action = request.data.get("action")  # 'CONFIRMED' or 'DECLINED'
        response_message = request.data.get("response_message", "")

        if not action:
            return Response(
                {"error": "action is required ('CONFIRMED' or 'DECLINED')"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if action not in ["CONFIRMED", "DECLINED"]:
            return Response(
                {"error": "action must be either 'CONFIRMED' or 'DECLINED'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Only the OTHER party can respond to the reschedule request
        if (
            booking.reschedule_requested_by == "STUDENT"
            and request.user != booking.teacher
        ):
            return Response(
                {"error": "Only the teacher can respond to this reschedule request"},
                status=status.HTTP_403_FORBIDDEN,
            )
        elif (
            booking.reschedule_requested_by == "TEACHER"
            and request.user != booking.student
        ):
            return Response(
                {"error": "Only the student can respond to this reschedule request"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if there's a pending reschedule request
        if booking.reschedule_request_status != "PENDING":
            return Response(
                {"error": "No pending reschedule request found for this booking"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update reschedule status
        booking.reschedule_request_status = action

        if action == "CONFIRMED":
            # Get the reschedule request details from the dedicated fields
            if (
                not booking.reschedule_request_start_time
                or not booking.reschedule_request_end_time
            ):
                return Response(
                    {"error": "Reschedule request details not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Apply the reschedule
            old_start = booking.start_time
            old_end = booking.end_time

            booking.start_time = booking.reschedule_request_start_time
            booking.end_time = booking.reschedule_request_end_time

            # Update Zoom meeting if it exists
            if booking.zoom_meeting_id:
                zoom_service = ZoomService()
                try:
                    zoom_service.update_meeting(booking.zoom_meeting_id, booking)
                except Exception as e:
                    # Log the error but don't fail the reschedule
                    print(
                        f"Failed to update Zoom meeting {booking.zoom_meeting_id}: {str(e)}"
                    )

            # Clear reschedule tracking after successful reschedule and save previous status
            booking.previous_reschedule_request_status = "CONFIRMED"
            booking.reschedule_request_status = "NONE"
            booking.reschedule_requested_by = None
            booking.reschedule_request_start_time = None
            booking.reschedule_request_end_time = None
            booking.reschedule_request_reason = ""

            booking.save()

            return Response(
                {
                    "message": "Reschedule request confirmed and booking updated successfully",
                    "changes": {
                        "old_start_time": old_start,
                        "old_end_time": old_end,
                        "new_start_time": booking.start_time,
                        "new_end_time": booking.end_time,
                        "response_message": response_message,
                    },
                    "booking": SessionBookingSerializer(
                        booking, context={"request": request}
                    ).data,
                }
            )

        else:  # action == 'DECLINED'
            # Clear reschedule tracking and save previous status
            booking.previous_reschedule_request_status = "DECLINED"
            booking.reschedule_request_status = "NONE"
            booking.reschedule_requested_by = None
            booking.reschedule_request_start_time = None
            booking.reschedule_request_end_time = None
            booking.reschedule_request_reason = ""
            booking.save()

            return Response(
                {
                    "message": "Reschedule request declined",
                    "response_message": response_message,
                    "booking": SessionBookingSerializer(
                        booking, context={"request": request}
                    ).data,
                }
            )

    @action(detail=False, methods=["get"])
    def my_bookings(self, request):
        """Get current user's bookings with filtering options"""
        try:
            status_filter = request.query_params.get("status")
            role_filter = request.query_params.get("role")  # 'student' or 'teacher'

            # Get base queryset (user's bookings)
            queryset = self.get_queryset()

            # Apply status filter if provided
            if status_filter:
                queryset = queryset.filter(status=status_filter.upper())

            # Apply role-specific filter if provided
            if role_filter == "student":
                queryset = queryset.filter(student=request.user)
            elif role_filter == "teacher":
                queryset = queryset.filter(teacher=request.user)

            # Serialize and return data
            serializer = self.get_serializer(queryset, many=True)
            return Response({"count": queryset.count(), "results": serializer.data})

        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve bookings: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
