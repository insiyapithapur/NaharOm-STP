# serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from . import models

class IndividualDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.IndividualDetails
        fields = [
            'first_name', 'last_name', 'addressLine1', 'addressLine2',
            'city', 'state', 'pin_code', 'alternate_phone_no'
        ]

class CompanyDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CompanyDetails
        fields = [
            'company_name', 'addressLine1', 'addressLine2', 'city',
            'state', 'pin_no', 'alternate_phone_no', 'public_url_company'
        ]

class UserRoleSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    mobile = serializers.CharField(source='user.mobile', read_only=True)
    
    class Meta:
        model = models.UserRole
        fields = ['id', 'email', 'mobile', 'role']

class IndividualProfileSerializer(serializers.Serializer):
    user = serializers.IntegerField(required=True)
    alternate_phone_no = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    addressLine1 = serializers.CharField(required=True)
    addressLine2 = serializers.CharField(required=True)
    pan_card_no = serializers.CharField(required=False)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    state = serializers.CharField(required=True)
    city = serializers.CharField(required=True)
    pin_code = serializers.CharField(required=True)

class CompanyProfileSerializer(serializers.Serializer):
    user = serializers.IntegerField(required=True)
    company_name = serializers.CharField(required=True)
    addressLine1 = serializers.CharField(required=True)
    addressLine2 = serializers.CharField(required=True)
    city = serializers.CharField(required=True)
    state = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    pin_no = serializers.CharField(required=True)
    alternate_phone_no = serializers.CharField(required=True)
    company_pan_no = serializers.CharField(required=False)
    public_url_company = serializers.CharField(required=True)

class ProfileResponseSerializer(serializers.Serializer):
    user = UserRoleSerializer()
    profile = serializers.SerializerMethodField()

    def get_profile(self, obj):
        user_role = obj['user']
        if user_role.role == 'Individual':
            return IndividualDetailsSerializer(obj['profile']).data
        elif user_role.role == 'Company':
            return CompanyDetailsSerializer(obj['profile']).data
        return None