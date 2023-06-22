from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password

from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token



from .models import *
from .serializers import *
from .signals import *


__all__ = [
    'RegisterAccount',
    'ConfirmAccount',
    'LoginAccount',
    'AccountDetails',
]

MSG_NO_REQUIRED_FIELDS = 'No required fields'

class RegisterAccount(APIView):
    def post(self, request):
        if not {'email', 'password', 'username'}.issubset(request.data):
            return Response({'Error': MSG_NO_REQUIRED_FIELDS})
        
        try:
            validate_password(request.data['password'])
        except Exception as error:
            return Response({'Error': list(error)})
        else:
            request.data.update({})
            user_serializer = UserSerializer(data=request.data)
            if user_serializer.is_valid():
                user = user_serializer.save()
                user.set_password(request.data['password'])
                user.save()
                new_user_registered_signal(user.id)
                return Response(user_serializer.data)
            
            else:
                return Response({'Error': user_serializer.errors})


class ConfirmAccount(APIView):
    def post(self, request):
        if not {'email', 'token'}.issubset(request.data):
            return Response({'Error': MSG_NO_REQUIRED_FIELDS})
        
        token = ConfirmEmailToken.objects.filter(user__email=request.data['email'],
                                                 key=request.data['token']).first()
        if token:
            token.user.is_active = True
            token.user.save()
            token.delete()
            return Response({'OK': True})
        else:
            return Response({'Error': 'Invalid email or token'})


class LoginAccount(APIView):
    def post(self, request):
        if not {'email', 'password'}.issubset(request.data):
            return Response({'Error': MSG_NO_REQUIRED_FIELDS})

        user = authenticate(request, username=request.data['email'],
                            password=request.data['password'])
        if user is not None:
            if user.is_active:
                token, _ = Token.objects.get_or_create(user=user)
                return Response({'OK': token.key})
        return Response({'Error': 'Invalid request'})
    

class AccountDetails(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    def post(self, request):
        if 'password' in request.data:
            try:
                validate_password(request.data['password'])
            except Exception as error:
                return Response({'Error': error})
            else:
                request.user.set_password(request.data['password'])
        
        user_serializer = UserSerializer(request.user, data=request.data,
                                         partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return Response(user_serializer.data)
        return Response({'Error': user_serializer.errors})


