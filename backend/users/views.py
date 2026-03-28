from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone

from .serializers import RegisterSerializer, UserSerializer
from config.response import success_response, error_response


class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response(success_response({
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }), status=status.HTTP_201_CREATED)
        return Response(error_response(str(serializer.errors)), status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                error_response("Email and password are required."),
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=email, password=password)
        if not user:
            return Response(
                error_response("Invalid credentials."),
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        return Response(success_response({
            "user": UserSerializer(user).data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "server_time": timezone.now().isoformat(),
        }))


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(success_response({
            "user": UserSerializer(request.user).data,
            "server_time": timezone.now().isoformat(),
        }))
