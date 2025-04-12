# views.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from .models import ApiStatus
from .serializers import ApiStatusSerializer, ApiStatusUpdateSerializer
import logging

logger = logging.getLogger(__name__)


class ApiStatusView(APIView):
    """
    This view provides GET and POST APIs for listing all APIs and updating their status.
    GET: get status of all the available external apis
    POST: Update status of external api, make it on or off.
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            api_statuses = ApiStatus.objects.all()
            serializer = ApiStatusSerializer(api_statuses, many=True)
            logger.info("Successfully fetched API statuses")
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error while fetching API statuses: {str(e)}")
            return Response(
                {"message": "Server error while fetching API statuses."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        try:
            api_id = request.data.get("id")

            if not api_id:
                logger.warning("API ID is missing in the request")
                return Response(
                    {"message": "API ID is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            api_status = ApiStatus.objects.filter(id=api_id).first()

            if not api_status:
                logger.warning(f"API with ID {api_id} not found")
                return Response(
                    {"message": "API not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            is_enabled = request.data.get("is_enabled", api_status.is_enabled)

            # Update the status of the selected API
            api_status.is_enabled = is_enabled
            api_status.save()

            logger.info(f"API {api_id} status updated to {is_enabled}")

            if is_enabled:
                if api_status.alternate_api:
                    ApiStatus.objects.filter(
                        alternate_api=api_status.alternate_api
                    ).update(is_enabled=True)
                    api_status.alternate_api.is_enabled = False
                    api_status.alternate_api.save()
                else:
                    ApiStatus.objects.filter(alternate_api=api_status).update(
                        is_enabled=False
                    )
            else:
                if api_status.alternate_api:
                    ApiStatus.objects.filter(
                        alternate_api=api_status.alternate_api
                    ).update(is_enabled=False)
                    api_status.alternate_api.is_enabled = True
                    api_status.alternate_api.save()
                else:
                    ApiStatus.objects.filter(alternate_api=api_status).update(
                        is_enabled=True
                    )

            serializer = ApiStatusSerializer(api_status)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Server error while updating the API status: {str(e)}")
            return Response(
                {"message": "Server error while updating the API status."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
