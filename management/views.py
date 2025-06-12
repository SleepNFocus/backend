# 작성자: 한율
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from management.serializers import UserDetailSerializer, UserUpdateSerializer
from users.models import User


class SleepRecordView(APIView):
    def get(self, request):
        return Response({"message": "GET sleep records"}, status=status.HTTP_200_OK)


class UpdateUserView(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response(
                {"message": "user_id query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user = User.objects.get(user_id=user_id)
            serializer = UserDetailSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(
                {"message": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request):
        user_id = request.data.get("user_id")
        if not user_id:
            return Response(
                {"message": "user_id in request body is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user = User.objects.get(user_id=user_id)
            serializer = UserUpdateSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response(
                {"message": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )


class UserManageView(APIView):
    def delete(self, request):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response(
                {"message": "user_id query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user = User.objects.get(user_id=user_id)
            user.delete()
            return Response(
                {"message": "User deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except User.DoesNotExist:
            return Response(
                {"message": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )


class SleepAnalyzeView(APIView):
    def get(self, request):
        return Response({"message": "GET sleep analysis"}, status=status.HTTP_200_OK)


class AdminRootView(APIView):
    def get(self, request):
        return Response({"message": "Admin API Root"}, status=status.HTTP_200_OK)


class AdminUserListView(APIView):
    def get(self, request):
        users = User.objects.all()
        serializer = UserDetailSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminUserDetailView(APIView):
    def get(self, request, pk):
        user = get_object_or_404(User, user_id=pk)
        serializer = UserDetailSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        user = get_object_or_404(User, user_id=pk)
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = get_object_or_404(User, user_id=pk)
        user.delete()
        return Response(
            {"message": "User deleted successfully"}, status=status.HTTP_204_NO_CONTENT
        )


class AdminLogsView(APIView):
    def get(self, request):
        return Response(
            {"message": "GET logs data (logs model not available in management app)"},
            status=status.HTTP_200_OK,
        )
