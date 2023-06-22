from django.contrib.auth.password_validation import validate_password

from rest_framework.views import APIView
from rest_framework.response import Response

from .models import *
from .serializers import *


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
                return Response(user.data)
            
            else:
                return Response({'Error': user_serializer.errors})
