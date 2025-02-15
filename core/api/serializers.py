# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
# from rest_framework import serializers
# from ..models import CustomUser , Note
# from django.forms.models import model_to_dict

# class NoteSerializer(serializers.ModelSerializer):
#     class Meta :
#         model = Note
#         fields = ['id','name','owner']

# class CustomObtainPairSerializer(TokenObtainPairSerializer):
#     @classmethod
#     def get_token(cls, user):
#         token = super(CustomObtainPairSerializer, cls).get_token(user)

#         # Add custom claims
#         token['username'] = user.username
#         token['email'] = user.email
#         return token
    

# class CustomUserSerializer(serializers.ModelSerializer):
#     confirm_password = serializers.CharField(write_only=True, required=True)
    
#     class Meta:
#         model = CustomUser
#         fields = ['id', 'username', 'email', 'password', 'confirm_password', 'profile_image', 'address', 'phone_number', 'date_of_birth']
#         extra_kwargs = {
#             'email': {'required': True},
#             'username': {'required': True},
#             'password': {
#                 'write_only': True,
#                 'required': True,
#                 'min_length': 8,
#                 'error_messages': {
#                     'min_length': 'Password must be at least 8 characters long.'
#                 }
#             },
#         }

#     def validate(self, data):
#         password = data.get('password')
#         confirm_password = data.get('confirm_password')
        
#         if not password:
#             raise serializers.ValidationError({
#                 'password': 'Password is required.'
#             })
        
#         if not confirm_password:
#             raise serializers.ValidationError({
#                 'confirm_password': 'Please confirm your password.'
#             })
            
#         if password != confirm_password:
#             raise serializers.ValidationError({
#                 'confirm_password': 'Passwords do not match.',
#                 'password': 'Passwords do not match.'
#             })
            
#         return data

#     def validate_email(self, value):
#         if not value:
#             raise serializers.ValidationError("Email is required")
#         if CustomUser.objects.filter(email=value).exists():
#             raise serializers.ValidationError("Email already exists")
#         return value

#     def validate_username(self, value):
#         if not value:
#             raise serializers.ValidationError("Username is required")
#         if CustomUser.objects.filter(username=value).exists():
#             raise serializers.ValidationError("Username already exists")
#         return value

#     def validate_phone_number(self,value):
#         if value is not "" or None:
#             if not (value.startswith('+92') or value.startswith('03') ):
#                 raise serializers.ValidationError("Please insert a Valid Pakistani Number")
#         return value

#     def create(self, validated_data):
#         validated_data.pop('confirm_password', None)  # Remove confirm_password before creating user
#         password = validated_data.pop('password', None)
#         user = CustomUser.objects.create(**validated_data)
#         if password:

#             user.set_password(password)
#             user.save()
#         return user
