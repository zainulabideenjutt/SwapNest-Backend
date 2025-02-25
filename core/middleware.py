from django.utils.functional import SimpleLazyObject
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.response import Response
from django.http import JsonResponse
from datetime import datetime
import jwt
from django.conf import settings


class TokenRefreshMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        access_token = request.COOKIES.get('access_token')
        refresh_token = request.COOKIES.get('refresh_token')

        if access_token:
            try:
                # Decode the access token without verification to get payload
                payload = jwt.decode(access_token, options={
                                     "verify_signature": False})
                exp = datetime.fromtimestamp(payload['exp'])

                # Check if token is expired
                if exp <= datetime.now():
                    # Token is expired, try to refresh
                    from rest_framework_simplejwt.tokens import RefreshToken
                    try:
                        refresh = RefreshToken(refresh_token)
                        new_access_token = str(refresh.access_token)
                        new_refresh_token = str(refresh)

                        # Update the cookie in the request for the current request
                        request.COOKIES['access_token'] = new_access_token
                        request.COOKIES['refresh_token'] = new_refresh_token

                        # Get the response
                        response = self.get_response(request)

                        # Set new cookies in response
                        response.set_cookie(
                            key='access_token',
                            value=new_access_token,
                            httponly=True,
                            secure=True,
                            samesite='None',
                            path='/'
                        )
                        response.set_cookie(
                            key='refresh_token',
                            value=new_refresh_token,
                            httponly=True,
                            secure=True,
                            samesite='None',
                            path='/'
                        )
                        return response

                    except Exception as e:
                        # If refresh token is invalid, let the authentication backend handle it
                        pass

            except (jwt.InvalidTokenError, jwt.ExpiredSignatureError):
                pass

        return self.get_response(request)
