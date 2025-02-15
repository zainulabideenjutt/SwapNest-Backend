# from rest_framework.request import Request
# from rest_framework.response import Response
# from rest_framework.decorators import api_view
# from rest_framework import status
# from rest_framework import mixins ,views
# # Create your views here.
# from rest_framework_simplejwt.views import TokenObtainPairView , TokenRefreshView
# from rest_framework.permissions import AllowAny
# from rest_framework import generics
# from ..models import CustomUser , Note
# from .serializers import CustomUserSerializer ,NoteSerializer, CustomObtainPairSerializer
# from rest_framework.views import APIView
# from rest_framework.permissions import IsAuthenticated
# from django.contrib.auth import authenticate
# from rest_framework_simplejwt.authentication import JWTAuthentication
# from ..authentication import CookiesJWTAuthentication
# from django.core.exceptions import ValidationError
# from django.db import IntegrityError





# class GETNotesAPIView(mixins.ListModelMixin,
#                   generics.GenericAPIView):
#     queryset=Note.objects.all()
#     serializer_class=NoteSerializer
#     authentication_classes=[CookiesJWTAuthentication]
#     permission_classes = [IsAuthenticated]
#     def get(self,request,*args,**kwargs):
#         try:
#             return self.list(request,*args,**kwargs)
#         except Exception as e:
#             return Response({"success": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# class HomeView(APIView):
#     authentication_classes = [CookiesJWTAuthentication]
#     permission_classes = [IsAuthenticated]
#     def get(self, request):
#         content = {'message': 'Welcome to the JWT Authentication page using React Js and Django!'}
#         return Response(content)
    
# @api_view(['GET'])
# def getRoutes(request):
#     routes = [
#         '/api/token',
#         '/api/token/refresh',
#     ]

#     return Response(routes)

# class RegisterCustomUserView(mixins.CreateModelMixin,generics.GenericAPIView):
#     queryset = CustomUser.objects.all()
#     serializer_class = CustomUserSerializer
#     permission_classes = [AllowAny]
#     authentication_classes = []
#     def post(self, request, *args, **kwargs):
#         try:
#             response = self.create(request, *args, **kwargs)
#             user = CustomUser.objects.get(username=response.data['username'])
            
#             # Generate tokens
#             serializer = CustomObtainPairSerializer.get_token(user)
#             access_token = str(serializer.access_token)
#             refresh_token = str(serializer)

#             res = Response(status=status.HTTP_201_CREATED)
#             res.data = {
#                 'success': True,
#                 'message': 'User registered successfully',
#                 'user': {
#                     'id': user.id,
#                     'username': user.username,
#                     'email': user.email
#                 }
#             }
            
#             # Set cookies
#             res.set_cookie(
#                 key='access_token',
#                 value=access_token,
#                 httponly=True,
#                 secure=True,
#                 samesite='None',
#                 path='/'
#             )
#             res.set_cookie(
#                 key='refresh_token',
#                 value=refresh_token,
#                 httponly=True,
#                 secure=True,
#                 samesite='None',
#                 path='/'
#             )
            
#             res.data.update({
#                 'access_token': access_token,
#                 'refresh_token': refresh_token
#             })
#             return res
#         except Exception as e:
#             return Response(
#                 {"success": False, "error": str(e)}, 
#                 status=status.HTTP_400_BAD_REQUEST
#             )



# class CustomObtainTokenPairView(TokenObtainPairView):
#     serializer_class=CustomObtainPairSerializer
#     def post(self,request,*args,**kwargs):
#         response=super().post(request,*args,**kwargs)
#         try:
#             tokens = response.data
#             access_token = tokens['access']
#             refresh_token = tokens['refresh']

#             res = Response()

#             res.data = {'success':True}
#             res.set_cookie(
#                 key='access_token',
#                 value=access_token,
#                 httponly=True,
#                 secure=True,
#                 samesite='None',
#                 path='/'
#             )

#             res.set_cookie(
#                 key='refresh_token',
#                 value=refresh_token,
#                 httponly=True,
#                 secure=True,
#                 samesite='None',
#                 path='/'
#             )
#             res.data.update({'access_token':access_token,'refresh_token':refresh_token})
#             return res
#         except Exception as e:
#             return Response({"success": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

# class CustomTokenRefreshView(TokenRefreshView):
#     def post(self, request: Request, *args, **kwargs) -> Response:
#         try:
#             refresh_token = request.COOKIES.get('refresh_token')
#             request.data['refresh'] = refresh_token
#             response=super().post(request, *args, **kwargs)
#             tokens=response.data
#             access_token = tokens['access']
#             refresh_token = tokens['refresh']

#             res = Response()

#             res.data = {'refeshed':True}
#             res.set_cookie(
#                     key='access_token',
#                     value=access_token,
#                     httponly=True,
#                     secure=True,
#                     samesite='None',
#                     path='/'
#                 )
#             res.set_cookie(
#                     key='refresh_token',
#                     value=refresh_token,
#                     httponly=True,
#                     secure=True,
#                     samesite='None',
#                     path='/'
#                 )
#             res.data.update({'access_token':access_token,'refresh_token':refresh_token})
#             return res
#         except Exception as e:
#             return Response({'refreshed':False, "error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        
# class LogoutAPIView(APIView):
#     def post(self, request, *args, **kwargs):
#         # Check if cookies are available
#         if request.COOKIES.get('access_token') or request.COOKIES.get('refresh_token'):
#             response = Response()
#             # Delete access_token and refresh_token cookies
#             response.delete_cookie('access_token', path='/', samesite='None')
#             response.delete_cookie('refresh_token', path='/', samesite='None')
#             # Send a success response
#             response.data = {'success': True}
#             return response

# class IsAuthenticatedAPIView(APIView):
#     authentication_classes = [CookiesJWTAuthentication]
#     permission_classes = [IsAuthenticated]
#     def post(self,request,*args,**kwargs):
#         return Response({'is_authenticated':True})