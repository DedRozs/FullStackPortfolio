from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .models import CustomUser
from django.middleware.csrf import get_token

@api_view(['POST'])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)

    if user:
        token, created = Token.objects.get_or_create(user=user)
        update_last_login(None, user)
        response = Response({'token': token.key, 'role': user.role})
        response.set_cookie('auth_token', token.key, httponly=True, secure=True, samesite='Strict')
        return response

    return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def register_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    role = request.data.get('role', 'user')

    if CustomUser.objects.filter(username=username).exists():
        return Response({'error': 'User already exists'}, status=status.HTTP_400_BAD_REQUEST)

    user = CustomUser.objects.create_user(username=username, password=password, role=role)
    return Response({'message': 'User created successfully'})

@api_view(['POST'])
def logout_view(request):
    response = Response({'message': 'Logged out successfully'})
    response.delete_cookie('auth_token')
    return response
