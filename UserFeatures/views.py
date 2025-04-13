import uuid
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from . import models
from AdminFeatures import models as admin_models
from django.utils import timezone
from django.db import transaction
from django.utils.dateparse import parse_time
import requests
from django.db.models import Q
from collections import defaultdict
from django.db.models import Max
import jwt
from django.conf import settings
from datetime import datetime, timedelta
from ApiManagement.utils import is_api_enabled
from UserFeatures import serializer

# for rest framework
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from .serializer import *
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
import logging

logger = logging.getLogger(__name__)


class GenerateOtpAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = json.loads(request.body)
            country_code = data.get("countryCode")
            mobile_number = data.get("mobileNumber")

            if not country_code or not mobile_number:
                return Response(
                    {"message": "countryCode and mobileNumber are required"}, status=status.HTTP_400_BAD_REQUEST
                )
            
            # url = 'https://api-preproduction.signzy.app/api/v3/phone/generateOtp'

            # headers = {
            #     'Authorization': 'lWQdJDRWrlibgEbU3O53UXXQSYnQQGhF',
            #     'Content-Type': 'application/json'
            # }

            # payload = {
            #     "countryCode": country_code,
            #     "mobileNumber": mobile_number
            # }

            # response = requests.post(url, headers=headers, json=payload)

            status_code = 200
            # if response.status_code == 200:
            if status_code == 200:
                return Response(
                    {
                        "result": {
                            "result": {
                                "referenceId": "telecom_15JaOVZRiuXsoSPoqiwjSDjpDWoH5cg8"
                            }
                        }
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                # return JsonResponse({"message": response.json()}, status=response.status_code)
                return Response(
                    {"message": "Invalid Number"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        except json.JSONDecodeError:
            return Response({"message": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        return Response({"message": "Only POST method is allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
class VerifyOtpAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = json.loads(request.body)
            country_code = data.get("countryCode")
            mobile_number = data.get("mobileNumber")
            reference_id = data.get("referenceId")
            otp = data.get("otp")
            extra_fields = data.get("extraFields")
            user_role = data.get("user_role")

            if not all([country_code, mobile_number, user_role, reference_id, otp, str(extra_fields)]):
                return Response({"message": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)
            
            # url = 'https://api-preproduction.signzy.app/api/v3/phone/getNumberDetails'
            # headers = {
            #     'Authorization': 'lWQdJDRWrlibgEbU3O53UXXQSYnQQGhF',
            #     'Content-Type': 'application/json'
            # }

            # payload = {
            #     "countryCode": country_code,
            #     "mobileNumber": mobile_number,
            #     "referenceId": reference_id,
            #     "otp": otp,
            #     "extraFields": extra_fields
            # }

            # response = requests.post(url, headers=headers, json=payload)

            status_code = 200

            with transaction.atomic():
                # if response.status_code == 200:
                if status_code == 200:
                    try:
                        user = models.User.objects.get(mobile=mobile_number)
                        userRole = models.UserRole.objects.get(user=user)

                        if userRole.role != user_role:
                            return Response({"message": "User role does not match"}, status=status.HTTP_400_BAD_REQUEST)

                        return Response(
                            {
                                "message": "User already registered",
                                # "signzy_Response" : response.json(),
                                "user": userRole.id,
                                "user_role": userRole.role,
                                "is_admin": userRole.user.is_admin,
                                "is_superadmin": userRole.user.is_superadmin,
                            },
                            status=status.HTTP_200_OK,
                        )
                    except models.User.DoesNotExist:
                        with transaction.atomic():
                            user = models.User.objects.create(mobile=mobile_number, email="default@gmail.com")
                            userRole = models.UserRole.objects.create(user=user, role=user_role)

                            return Response(
                                {
                                    "message": "User registered successfully",
                                    # "signzy_Response" : response.json(),
                                    "user": userRole.id,
                                    "user_role": userRole.role,
                                    "is_admin": userRole.user.is_admin,
                                    "is_superadmin": userRole.user.is_superadmin,
                                },
                                status=status.HTTP_201_CREATED,
                            )
                    except models.UserRole.DoesNotExist:
                        userRole = models.UserRole.objects.create(user=user, role=user_role)
                        if userRole.role != user_role:
                            return Response({"message": "User role does not match"}, status=status.HTTP_400_BAD_REQUEST)

                        return Response(
                            {
                                "message": "User already registered",
                                # "signzy_Response" : response.json(),
                                "user": userRole.id,
                                "user_role": userRole.role,
                                "is_admin": userRole.user.is_admin,
                                "is_superadmin": userRole.user.is_superadmin,
                            },
                            status=status.HTTP_200_OK,
                        )
                    except Exception as e:
                        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    # return JsonResponse({"message": response.json()}, status=response.status_code)
                    return Response({"message": "Signzy Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except json.JSONDecodeError:
            return Response({"message": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        return Response({"message": "Only POST method is allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

class VerifyStatusAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user):
        try:
            if not user:
                return Response({"message": "userID should be present in the URL"}, status=status.HTTP_400_BAD_REQUEST)


            userRole = models.UserRole.objects.get(id=user)
            userDetails = models.User.objects.get(id=userRole.user.id)

            is_KYC = False
            is_BankDetailsExists = False
            OutstandingBalance = 0

            if userRole.role == "Individual":
                is_KYC = models.IndividualDetails.objects.filter(user_role=userRole).exists()
                is_BankDetailsExists = models.BankAccountDetails.objects.filter(user_role=userRole).exists()

                if is_BankDetailsExists:
                    try:
                        wallet = models.Wallet.objects.get(user_role=userRole)
                        OutstandingBalance = wallet.OutstandingBalance
                    except models.Wallet.DoesNotExist:
                        OutstandingBalance = 0

            elif userRole.role == "Company":
                is_KYC = models.CompanyDetails.objects.filter(user_role=userRole).exists()
                is_BankDetailsExists = models.BankAccountDetails.objects.filter(user_role=userRole).exists()

                if is_BankDetailsExists:
                    try:
                        wallet = models.Wallet.objects.get(user_role=userRole)
                        OutstandingBalance = wallet.OutstandingBalance
                    except models.Wallet.DoesNotExist:
                        OutstandingBalance = 0

            if userDetails.is_superadmin:
                role = "superadmin"
            elif userDetails.is_admin:
                role = "admin"
            else:
                role = "user"

            payload = {
                "user_id": userRole.id,
                "entity": userRole.role,
                "role": role,
                "is_BankDetailsExists": is_BankDetailsExists,
                "exp": int((datetime.utcnow() + timedelta(hours=24)).timestamp()),  # Token expiration
            }

            token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

            return Response({
                "token": token,
                "is_KYC": is_KYC,
                "is_BankDetailsExists": is_BankDetailsExists,
                "OutstandingBalance": OutstandingBalance
            }, status=status.HTTP_200_OK)

        except models.UserRole.DoesNotExist:
            return Response({"message": "User ID does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        return Response({"message": "Only GET methods are allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


class PhoneToPrefillAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user):
        try:
            if not user:
                return Response({"message": "user is required"}, status=status.HTTP_400_BAD_REQUEST)
        
            userRole = models.UserRole.objects.get(id=user)

            if userRole.role == "Individual":
                url = "https://api-preproduction.signzy.app/api/v3/phonekyc/phone-prefill-v2"
                headers = {
                    "Authorization": "lWQdJDRWrlibgEbU3O53UXXQSYnQQGhF",
                    "Content-Type": "application/json",
                }

                payload = {
                    "mobileNumber": userRole.user.mobile,
                    "consent": {
                        "consentFlag": True,
                        "consentTimestamp": 17000,
                        "consentIpAddress": "684D:1111:222:3333:4444:5555:6:77",
                        "consentMessageId": "CM_1",
                    },
                }

                response = requests.post(url, headers=headers, json=payload)
                response_data = response.json()

                if response.status_code == 200:
                    response_info = response_data["response"]

                    alternate_phone_numbers = [
                        phone["phoneNumber"]
                        for phone in response_info.get("alternatePhone", [])
                    ]
                    alternate_phone = next(
                        (phone for phone in alternate_phone_numbers if phone != userRole.user.mobile), None
                    )

                    email = response_info.get("email", [{}])[0].get("email") if response_info.get("email") else None

                    # Get the first two addresses if present
                    addresses = response_info.get("address", [])[:2]
                    address1 = addresses[0] if len(addresses) > 0 else None
                    address2 = addresses[1] if len(addresses) > 1 else None

                    pan_card_number = response_info.get("PAN", [{}])[0].get("IdNumber") if response_info.get("PAN") else None

                    first_name = response_info.get("name", {}).get("firstName")
                    last_name = response_info.get("name", {}).get("lastName")

                    state = addresses[0].get("State") if len(addresses) > 0 else None
                    postal_code = addresses[0].get("Postal") if len(addresses) > 0 else None

                    prefill_data = {
                        "alternatePhone": alternate_phone,
                        "email": email,
                        "address1": address1,
                        "address2": address2,
                        "panCardNumber": pan_card_number,
                        "firstName": first_name,
                        "lastName": last_name,
                        "state": state,
                        "postalCode": postal_code,
                    }

                    return Response(
                        {
                            "prefillData": prefill_data,
                            "user": userRole.id,
                            "phoneNumber": userRole.user.mobile,
                        },
                        status=status.HTTP_200_OK,
                    )
                else:
                    # return Response(
                    #     {
                    #         "message": "Failed to fetch data from the external API",
                    #         "response": response_data,
                    #         "user": userRole.id,
                    #         "phoneNumber": userRole.user.mobile,
                    #     },
                    #     status=response.status_code,
                    # )
                    return Response(
                        {
                            "prefillData": None,
                            "user": userRole.id,
                            "phoneNumber": userRole.user.mobile,
                         },
                         status=status.HTTP_200_OK
                    )

        except models.UserRole.DoesNotExist:
            return Response({"message": "User ID does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        return Response({"message": "Only GET methods are allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

class PANToGSTAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            data = json.loads(request.body)
            user = data.get("user")
            PAN = data.get("pan")
            email = data.get("email")
            state = data.get("state")

            userRole = models.UserRole.objects.get(id=user)

            with transaction.atomic():
                if userRole.role == "Company":
                    # url = 'https://api-preproduction.signzy.app/api/v3/gst/panToGstnDetail'
                    # headers = {
                    #     'Authorization': '1tKetIB80fpVfLwXXbKGSKxgtvMZ3DlF',
                    #     'Content-Type': 'application/json'
                    # }

                    # payload = {
                    #     "panNumber": PAN,
                    #     "state": state ,
                    #     "email": email
                    # }

                    # response = requests.post(url, headers=headers, json=payload)
                    # response_data = response.json()
                    response = 200
                    if response == 200:
                    # if response.status_code == 200:
                        # gstn_detail = response_data['result']['gstnDetailed'][0]
                        # gstn_record = response_data['result']['gstnRecords'][0]

                        # trade_name = gstn_detail.get('tradeNameOfBusiness', '')
                        # principal_address = gstn_detail.get('principalPlaceAddress', '')
                        # additional_address = gstn_detail.get('additionalPlaceAddress', '')
                        # state = gstn_detail.get('principalPlaceState', '')
                        # pincode = gstn_detail.get('principalPlacePincode', '')
                        # city = gstn_detail.get('principalPlaceCity', '')
                        # mobile_number = gstn_record.get('mobNum', '')

                        # # Constructing the response
                        # result = {
                        #     "company_name": trade_name,
                        #     "addressLine1": principal_address,
                        #     "addressLine2": additional_address,
                        #     "state": state,
                        #     "pin_no": pincode,
                        #     "city": city,
                        #     "alternate_phone_no": mobile_number,
                        #     "public_url_company" : None ,
                        #     "email" : email,
                        #     "PAN" : PAN
                        # }

                        # return JsonResponse(result, status=200)
                        return Response(
                            {
                                "result": None, 
                                "user": userRole.id,
                                "phoneNumber": userRole.user.mobile,
                            },
                            status=status.HTTP_200_OK,
                        )
                    else:
                        return Response(
                            {
                                "result": None,
                                "user": userRole.id,
                                "phoneNumber": userRole.user.mobile,
                            },
                            status=status.HTTP_200_OK,
                        )

        except models.UserRole.DoesNotExist:
            return Response({"error": "User role not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        return Response({"message": "Only POST methods are allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
class ProfileAPIView(APIView):
    permission_classes = [AllowAny]  # Uncomment if authentication is required

    def get(self, request, user=None):
        if not user:
            return Response({"message": "userID should be there"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_role = models.UserRole.objects.get(id=user)
            response_data = {
                "user": user_role
            }

            if user_role.role == "Individual":
                try:
                    individual_details = models.IndividualDetails.objects.get(user_role=user_role)
                    response_data["profile"] = individual_details
                except models.IndividualDetails.DoesNotExist:
                    return Response({"message": "Individual profile not found"}, status=status.HTTP_400_BAD_REQUEST)
            
            elif user_role.role == "Company":
                try:
                    company_details = models.CompanyDetails.objects.get(user_role=user_role)
                    response_data["profile"] = company_details
                except models.CompanyDetails.DoesNotExist:
                    return Response({"message": "Company profile not found"}, status=status.HTTP_400_BAD_REQUEST)
            
            serial = serializer.ProfileResponseSerializer(response_data)
            return Response(serial.data, status=status.HTTP_200_OK)
            
        except models.UserRole.DoesNotExist:
            return Response({"message": "user does not found"}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        if not request.data.get("user"):
            return Response({"message": "userID should be there"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user_role = models.UserRole.objects.get(id=request.data.get("user"))
            user = user_role.user

            with transaction.atomic():
                if user_role.role == "Individual":
                    individual_serial = serializer.IndividualProfileSerializer(data=request.data)
                    if not individual_serial.is_valid():
                        return Response(individual_serial.errors, status=status.HTTP_400_BAD_REQUEST)
                    
                    validated_data = individual_serial.validated_data
                    
                    # Update user email
                    user.email = validated_data.get("email")
                    user.save()
                    
                    try:
                        # Update existing individual profile
                        profile = models.IndividualDetails.objects.get(user_role=user_role)
                        profile.first_name = validated_data.get("firstName")
                        profile.last_name = validated_data.get("lastName")
                        profile.addressLine1 = validated_data.get("address1")
                        profile.addressLine2 = validated_data.get("address2")
                        profile.city = validated_data.get("city")
                        profile.state = validated_data.get("state")
                        profile.pin_code = validated_data.get("postalCode")
                        profile.alternate_phone_no = validated_data.get("alternatePhone")
                        profile.updated_at = timezone.now()
                        profile.save()
                        
                        try:
                            # Update PAN card
                            pancard = models.PanCardNos.objects.get(user_role=user_role)
                            pancard.pan_card_no = validated_data.get("panCardNumber", pancard.pan_card_no)
                            pancard.save()
                        except models.PanCardNos.DoesNotExist:
                            return Response(
                                {"message": "pan card entry is not there but Individual details is there"},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                            
                        return Response({
                            "message": "Successfully entered individual profile",
                            "indiviual_profileID": profile.id,
                            "user": user_role.id
                        }, status=status.HTTP_200_OK)
                        
                    except models.IndividualDetails.DoesNotExist:
                        # Create new individual profile
                        try:
                            # Check if PAN card exists
                            models.PanCardNos.objects.get(user_role=user_role)
                            return Response(
                                {"message": "PAN card already exists but individual profile does not"},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        except models.PanCardNos.DoesNotExist:
                            # Create new profile and PAN card
                            panCardNumber = validated_data.get("panCardNumber")
                            if not panCardNumber:
                                return Response(
                                    {"message": "panCardNumber is required as it is new user"},
                                    status=status.HTTP_400_BAD_REQUEST
                                )
                                
                            profile = models.IndividualDetails.objects.create(
                                user_role=user_role,
                                first_name=validated_data.get("firstName"),
                                last_name=validated_data.get("lastName"),
                                addressLine1=validated_data.get("address1"),
                                addressLine2=validated_data.get("address2"),
                                city=validated_data.get("city"),
                                state=validated_data.get("state"),
                                pin_code=validated_data.get("postalCode"),
                                alternate_phone_no=validated_data.get("alternatePhone"),
                                created_at=timezone.now(),
                                updated_at=timezone.now()
                            )
                            
                            pancard = models.PanCardNos.objects.create(
                                user_role=user_role,
                                pan_card_no=panCardNumber,
                                created_at=timezone.now()
                            )
                            
                            return Response({
                                "message": "Successfully entered individual profile",
                                "indiviual_profileID": profile.id,
                                "panCard_NumberID": pancard.id,
                                "user": user_role.id
                            }, status=status.HTTP_200_OK)
                
                elif user_role.role == "Company":
                    company_serial = serializer.CompanyProfileSerializer(data=request.data)
                    if not company_serial.is_valid():
                        return Response(company_serial.errors, status=status.HTTP_400_BAD_REQUEST)
                    
                    validated_data = company_serial.validated_data
                    
                    # Update user email
                    user.email = validated_data.get("email")
                    user.save()
                    
                    try:
                        # Update existing company profile
                        profile = models.CompanyDetails.objects.get(user_role=user_role)
                        profile.company_name = validated_data.get("company_name")
                        profile.addressLine1 = validated_data.get("addressLine1")
                        profile.addressLine2 = validated_data.get("addressLine2")
                        profile.city = validated_data.get("city")
                        profile.state = validated_data.get("state")
                        profile.pin_no = validated_data.get("pin_no")
                        profile.alternate_phone_no = validated_data.get("alternate_phone_no")
                        profile.public_url_company = validated_data.get("public_url_company")
                        profile.updated_at = timezone.now()
                        profile.save()
                        
                        try:
                            # Update PAN card
                            pancard = models.PanCardNos.objects.get(user_role=user_role)
                            pancard.pan_card_no = validated_data.get("company_pan_no", pancard.pan_card_no)
                            pancard.save()
                        except models.PanCardNos.DoesNotExist:
                            return Response(
                                {"message": "pan card entry is not there but company details is there"},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                            
                        return Response({
                            "message": "Successfully entered company profile",
                            "company_ProfileID": profile.id,
                            "user": user_role.id
                        }, status=status.HTTP_200_OK)
                        
                    except models.CompanyDetails.DoesNotExist:
                        # Create new company profile
                        try:
                            # Check if PAN card exists
                            models.PanCardNos.objects.get(user_role=user_role)
                            return Response(
                                {"message": "PAN card already exists but company profile does not"},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        except models.PanCardNos.DoesNotExist:
                            # Create new profile and PAN card
                            company_pan_no = validated_data.get("company_pan_no")
                            if not company_pan_no:
                                return Response(
                                    {"message": "panCardNumber is required as it is new user"},
                                    status=status.HTTP_400_BAD_REQUEST
                                )
                                
                            profile = models.CompanyDetails.objects.create(
                                user_role=user_role,
                                company_name=validated_data.get("company_name"),
                                addressLine1=validated_data.get("addressLine1"),
                                addressLine2=validated_data.get("addressLine2"),
                                city=validated_data.get("city"),
                                state=validated_data.get("state"),
                                pin_no=validated_data.get("pin_no"),
                                alternate_phone_no=validated_data.get("alternate_phone_no"),
                                public_url_company=validated_data.get("public_url_company"),
                                created_at=timezone.now(),
                                updated_at=timezone.now()
                            )
                            
                            pancard = models.PanCardNos.objects.create(
                                user_role=user_role,
                                pan_card_no=company_pan_no,
                                created_at=timezone.now()
                            )
                            
                            return Response({
                                "message": "Successfully entered company profile",
                                "company_ProfileID": profile.id,
                                "panCard_NumberID": pancard.id,
                                "user": user_role.id
                            }, status=status.HTTP_200_OK)
                
                else:
                    return Response({"message": "Role is not matched"}, status=status.HTTP_400_BAD_REQUEST)
        
        except models.UserRole.DoesNotExist:
            return Response({"message": "userID does not found"}, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
import json
from . import models

class BankAccountDetailsAPIView(APIView):
    """
    API view for handling bank account details.
    """
    
    def post(self, request):
        try:
            user_role_id = request.data.get("user")

            if not user_role_id:
                return Response({"message": "user is required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user_role = models.UserRole.objects.get(id=user_role_id)
            except models.UserRole.DoesNotExist:
                return Response({"message": "User role not found"}, status=status.HTTP_400_BAD_REQUEST)

            # Details that will come from 3rd party API
            account_number = request.data.get("account_number")
            ifc_code = request.data.get("ifc_code")
            account_type = request.data.get("account_type")

            if not account_number or not ifc_code or not account_type:
                return Response(
                    {
                        "message": "account_number, ifc_code, and account_type are required"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            is_exists = models.BankAccountDetails.objects.filter(
                user_role=user_role
            ).exists()

            # Create new bank account details
            bank_account_details = models.BankAccountDetails.objects.create(
                user_role=user_role,
                account_number=account_number,
                ifc_code=ifc_code,
                account_type=account_type,
            )
            
            # Get or create wallet
            try:
                wallet = models.Wallet.objects.get(user_role=user_role)
            except models.Wallet.DoesNotExist:
                wallet = models.Wallet.objects.create(
                    user_role=user_role,
                    primary_bankID=bank_account_details,
                    OutstandingBalance=0,
                    updated_at=timezone.now(),
                )
                
            response_data = {
                "message": "Bank account details saved successfully",
                "bank_account_id": bank_account_details.id,
                "user": user_role.id,
                "primary_bank": wallet.primary_bankID.id,
                "primary_bank_AccNo": wallet.primary_bankID.account_number,
            }
            
            # Return 201 if first account, 200 if additional account
            status_code = status.HTTP_201_CREATED if not is_exists else status.HTTP_200_OK
            return Response(response_data, status=status_code)
            
        except Exception as e:
            # Handle any unexpected errors
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreditFundsAPIView(APIView):
    """
    API view for crediting funds to a user's wallet.
    """
    
    def post(self, request):
        try:
            user_role_id = request.data.get("user")
            amount = request.data.get("amount")

            if not user_role_id or not amount:
                return Response(
                    {"message": "user and amount are required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                user_role = models.UserRole.objects.get(id=user_role_id)
            except models.UserRole.DoesNotExist:
                return Response(
                    {"message": "User role not found"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                wallet = models.Wallet.objects.get(user_role=user_role)
            except models.Wallet.DoesNotExist:
                return Response(
                    {"message": "Wallet not found for the given user"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                wallet.OutstandingBalance += amount
                wallet.updated_at = timezone.now().date()
                wallet.save()

                balance_transaction = models.WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_id=uuid.uuid4(),
                    type="fund",
                    creditedAmount=amount,
                    debitedAmount=None,
                    status="response",
                    source="bank_to_wallet",
                    purpose="Funds added to wallet",
                    from_bank_acc=wallet.primary_bankID,
                    to_bank_acc=None,
                    from_wallet=None,
                    to_wallet=wallet,
                    invoice=None,
                    time_date=timezone.now(),
                )

                return Response(
                    {
                        "message": "Funds added successfully",
                        "user": user_role.id,
                        "wallet_balance": wallet.OutstandingBalance,
                        "primary_BankAccID": wallet.primary_bankID.id,
                        "primary_BankAccNo": wallet.primary_bankID.account_number,
                        "transaction_id": balance_transaction.transaction_id,
                    },
                    status=status.HTTP_200_OK
                )

        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WithdrawFundsAPIView(APIView):
    """
    API view for withdrawing funds from a user's wallet.
    """
    
    def post(self, request):
        try:
            user_role_id = request.data.get("user")
            amount = request.data.get("amount")

            if not user_role_id or not amount:
                return Response(
                    {"message": "user and amount are required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                user_role = models.UserRole.objects.get(id=user_role_id)
            except models.UserRole.DoesNotExist:
                return Response(
                    {"message": "User not found"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                wallet = models.Wallet.objects.get(user_role=user_role)
            except models.Wallet.DoesNotExist:
                return Response(
                    {"message": "Wallet not found for the given user"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                if wallet.OutstandingBalance < amount:
                    return Response(
                        {"message": "Not sufficient amount to do withdrawal"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                
                wallet.OutstandingBalance -= amount
                wallet.updated_at = timezone.now().date()
                wallet.save()

                balance_transaction = models.WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_id=uuid.uuid4(),
                    type="Withdraw",
                    creditedAmount=None,
                    debitedAmount=amount,
                    status="response",
                    source="wallet_to_bank",
                    purpose="Funds debited from wallet",
                    to_bank_acc=wallet.primary_bankID,
                    from_bank_acc=None,
                    from_wallet=wallet,
                    to_wallet=None,
                    invoice=None,
                    time_date=timezone.now(),
                )

                return Response(
                    {
                        "message": "Funds debited successfully",
                        "user": user_role.id,
                        "wallet_balance": wallet.OutstandingBalance,
                        "primary_BankAccID": wallet.primary_bankID.id,
                        "primary_BankAccNo": wallet.primary_bankID.account_number,
                        "transaction_id": balance_transaction.transaction_id,
                    },
                    status=status.HTTP_200_OK
                )

        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LedgerAPIView(APIView):
    """
    API view for retrieving a user's transaction ledger.
    """
    
    def get(self, request, user):
        try:
            try:
                user_role = models.UserRole.objects.get(id=user)
            except models.UserRole.DoesNotExist:
                return Response(
                    {"message": "User role not found"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            wallet = models.Wallet.objects.filter(user_role=user_role)
            if not wallet.exists():
                return Response(
                    {"message": "No wallets found for this user role"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            transactions = models.WalletTransaction.objects.filter(
                wallet__in=wallet
            ).order_by("-time_date")

            transactions_data = []
            for transaction in transactions:
                transactions_data.append(
                    {
                        "transaction_id": str(transaction.transaction_id),
                        "type": transaction.type,
                        "creditedAmount": transaction.creditedAmount,
                        "debitedAmount": transaction.debitedAmount,
                        "status": transaction.status,
                        "source": transaction.source,
                        "purpose": transaction.purpose,
                        "from_bank_acc": (
                            transaction.from_bank_acc.account_number
                            if transaction.from_bank_acc
                            else None
                        ),
                        "to_bank_acc": (
                            transaction.to_bank_acc.account_number
                            if transaction.to_bank_acc
                            else None
                        ),
                        "from_wallet": (
                            transaction.from_wallet.id
                            if transaction.from_wallet
                            else None
                        ),
                        "to_wallet": (
                            transaction.to_wallet.id if transaction.to_wallet else None
                        ),
                        "invoice": (
                            transaction.invoice.product_name
                            if transaction.invoice
                            else None
                        ),
                        "time_date": transaction.time_date,
                    }
                )

            balance_wallet = wallet.first()
            return Response(
                {
                    "transactions": transactions_data,
                    "Balance": balance_wallet.OutstandingBalance,
                    "user": user_role.id,
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ShowFundsAPIView(APIView):
    """
    API view for showing a user's current wallet balance.
    """
    
    def get(self, request, user_role_id):
        try:
            try:
                wallet = models.Wallet.objects.get(user_role=user_role_id)
                balance = wallet.OutstandingBalance
                return Response({"Balance": balance}, status=status.HTTP_200_OK)
            except models.Wallet.DoesNotExist:
                return Response(
                    {"message": "Wallet not found for the given user"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetSellPurchaseDetailsAPIView(APIView):
    """
    API view for retrieving sell and purchase details for a user.
    """
    
    def get(self, request, user):
        try:
            try:
                user_role = models.UserRole.objects.get(id=user)
            except models.UserRole.DoesNotExist:
                return Response({"message": "user doesn't exist"}, status=status.HTTP_400_BAD_REQUEST)

            invoices = models.Invoices.objects.filter(expired=False)
            invoice_data_list = []

            for invoice in invoices:
                post_for_sales = models.Post_for_sale.objects.filter(
                    invoice_id=invoice,
                    sold=False,
                    remaining_units__gt=0,
                    withdrawn=False,
                ).exclude(user_id=user_role)
                
                for post_for_sale in post_for_sales:
                    invoice_data = {
                        "id": invoice.id,
                        "Invoice_id": invoice.invoice_id,
                        "Invoice_primary_id": invoice.primary_invoice_id,
                        "Invoice_no_of_units": post_for_sale.no_of_units,
                        "post_for_sellID": post_for_sale.id,
                        "Posted_withdrawn": post_for_sale.withdrawn,
                        "Invoice_remaining_units": post_for_sale.remaining_units,
                        "Invoice_per_unit_price": post_for_sale.per_unit_price,
                        "Invoice_total_price": post_for_sale.total_price,
                        "Invoice_name": invoice.product_name,
                        "Invoice_post_date": post_for_sale.post_date,
                        "Invoice_post_time": post_for_sale.post_time,
                        "Invoice_interest": invoice.interest,
                        "Invoice_xirr": invoice.xirr,
                        "Invoice_irr": invoice.irr,
                        "Invoice_from_date": post_for_sale.from_date,
                        "Invoice_to_date": post_for_sale.to_date,
                        "Invoice_tenure_in_days": invoice.tenure_in_days,
                        "Invoice_expiration_time": invoice.expiration_time,
                        "isAdmin": post_for_sale.user_id.user.is_admin,
                        "Invoice_type": post_for_sale.type,
                        "Invoice_no_of_bid": post_for_sale.no_of_bid,
                        "open_for_bid": post_for_sale.open_for_bid,
                        "type": "CanBuy",
                    }

                    if (
                        post_for_sale.type == "Bidding"
                        and post_for_sale.open_for_bid == True
                    ):
                        bids = models.User_Bid.objects.filter(
                            posted_for_sale_id=post_for_sale, withdraw=False
                        )
                        bid_details = []
                        for bid in bids:
                            bid_detail = {
                                "bid_id": bid.id,
                                "user_id": bid.user_id.id,
                                "bid_price": bid.per_unit_bid_price,
                                "no_of_units": bid.no_of_units,
                                "status": bid.status,
                                "withdrawn": bid.withdraw,
                                "created_at": bid.datetime,
                            }
                            bid_details.append(bid_detail)

                        highest_bid = (
                            bids.aggregate(Max("per_unit_bid_price"))[
                                "per_unit_bid_price__max"
                            ]
                            if bids
                            else None
                        )

                        invoice_data["bids"] = bid_details
                        invoice_data["highest_bid"] = highest_bid

                    invoice_data_list.append(invoice_data)

            # bidded
            bidded = models.User_Bid.objects.filter(
                user_id=user_role, status="awaiting_acceptance"
            )
            for bid in bidded:
                bidded_data = {
                    'id': bid.posted_for_sale_id.invoice_id.id,
                    'Invoice_id': bid.posted_for_sale_id.invoice_id.invoice_id,
                    'Invoice_primary_id': bid.posted_for_sale_id.invoice_id.primary_invoice_id,
                    'post_for_sellID' : bid.posted_for_sale_id.id,
                    "bidID" : bid.id,
                    'Invoice_no_of_units': bid.posted_for_sale_id.no_of_units,
                    'Invoice_remaining_units': bid.posted_for_sale_id.remaining_units,
                    'Invoice_per_unit_price': bid.posted_for_sale_id.per_unit_price,
                    'Invoice_total_price' : bid.posted_for_sale_id.total_price,
                    'Invoice_name': bid.posted_for_sale_id.invoice_id.product_name,
                    'Invoice_post_date': bid.posted_for_sale_id.post_date,
                    'Invoice_post_time': bid.posted_for_sale_id.post_time,
                    'Invoice_interest': bid.posted_for_sale_id.invoice_id.interest,
                    'Invoice_xirr': bid.posted_for_sale_id.invoice_id.xirr,
                    'Invoice_irr': bid.posted_for_sale_id.invoice_id.irr,
                    'Invoice_from_date' : bid.posted_for_sale_id.from_date,
                    'Invoice_to_date' : bid.posted_for_sale_id.to_date,
                    'Invoice_tenure_in_days': bid.posted_for_sale_id.invoice_id.tenure_in_days,
                    'Invoice_expiration_time': bid.posted_for_sale_id.invoice_id.expiration_time,
                    'isAdmin': bid.posted_for_sale_id.user_id.user.is_admin,
                    'Invoice_type' : bid.posted_for_sale_id.type,
                    'Invoice_no_of_bid' : bid.posted_for_sale_id.no_of_bid,
                    'open_for_bid' : bid.posted_for_sale_id.open_for_bid,
                    'bid_status' : bid.status,
                    'bid_withdrawn_by_bidder' : bid.withdraw,
                    'bid_price_by_bidder' : bid.per_unit_bid_price,
                    'no_of_units_by_bidder' : bid.no_of_units,
                    'updated_at_by_bidder' : bid.updated_at,
                    'type': 'bidded'
                }
                invoice_data_list.append(bidded_data)

            buyers = models.Buyers.objects.filter(user_id=user_role)
            for buyer in buyers:
                # not posted for sale
                buyer_units = models.Buyer_UnitsTracker.objects.filter(
                    buyer_id=buyer, post_for_saleID__isnull=True
                )
                buyer_units_count = buyer_units.count()
                if buyer_units_count > 0:
                    brought_invoice = buyer_units.first().unitID.invoice
                    invoice_data = {
                        "id": brought_invoice.id,
                        "Invoice_id": brought_invoice.invoice_id,
                        "Invoice_primary_id": brought_invoice.primary_invoice_id,
                        "Buyer_id": buyer.id,
                        "Purchased_no_of_units": buyer.no_of_units,
                        "Purchased_remaining_units": buyer_units_count,
                        "Purchased_per_unit_price": buyer.per_unit_price_invested,
                        "Invoice_name": brought_invoice.product_name,
                        "Purchased_date": buyer.purchase_date,
                        "Purchased_time": buyer.purchase_time,
                        "Invoice_interest": brought_invoice.interest,
                        "Invoice_xirr": brought_invoice.xirr,
                        "Invoice_irr": brought_invoice.irr,
                        "Invoice_tenure_in_days": brought_invoice.tenure_in_days,
                        "Invoice_expiration_time": brought_invoice.expiration_time,
                        "isAdmin": buyer.user_id.user.is_admin,
                        "Buyer_user_id": buyer.user_id.id,
                        "type": "Brought",
                    }
                    invoice_data_list.append(invoice_data)

                # posted for sale
                buyer_units_posted_for_sale = models.Buyer_UnitsTracker.objects.filter(
                    buyer_id=buyer, post_for_saleID__isnull=False
                )
                buyer_units_posted_for_sale_count = buyer_units_posted_for_sale.count()
                if buyer_units_posted_for_sale_count > 0:
                    # Group the units by post_for_saleID
                    units_by_post_for_sale = defaultdict(list)
                    for unit in buyer_units_posted_for_sale:
                        units_by_post_for_sale[unit.post_for_saleID].append(unit)
                    
                    first_unit = buyer_units_posted_for_sale.first()
                    if first_unit:
                        post_invoice = first_unit.unitID.invoice

                        # Iterate through each group
                        for post_for_saleID, units in units_by_post_for_sale.items():
                            if units:
                                # Fetch the post_for_sale object to access its fields
                                post_for_sale = models.Post_for_sale.objects.get(
                                    id=post_for_saleID.id
                                )
                                invoice_data = {
                                    "id": post_invoice.id,
                                    "Invoice_id": post_invoice.invoice_id,
                                    "Invoice_primary_id": post_invoice.primary_invoice_id,
                                    "Buyer_id": buyer.id,
                                    "Buyer_user_id": buyer.user_id.id,
                                    "post_for_saleID": post_for_saleID.id,
                                    "Posted_no_of_units": post_for_sale.no_of_units,
                                    "Posted_remaining_units": post_for_sale.remaining_units,
                                    "Posted_per_unit_price": post_for_sale.per_unit_price,
                                    "Posted_total_price": post_for_sale.total_price,
                                    "Posted_from_date": post_for_sale.from_date,
                                    "Posted_to_date": post_for_sale.to_date,
                                    "Posted_type": post_for_sale.type,
                                    "Posted_no_of_bid": post_for_sale.no_of_bid,
                                    "Posted_open_for_bid": post_for_sale.open_for_bid,
                                    "Posted_withdraw": post_for_sale.withdrawn,
                                    "Invoice_name": post_invoice.product_name,
                                    "Buyer_Purchased_date": buyer.purchase_date,
                                    "Buyer_Purchased_time": buyer.purchase_time,
                                    "Invoice_interest": post_invoice.interest,
                                    "Invoice_xirr": post_invoice.xirr,
                                    "Invoice_irr": post_invoice.irr,
                                    "Invoice_tenure_in_days": post_invoice.tenure_in_days,
                                    "Invoice_expiration_time": post_invoice.expiration_time,
                                    "isAdmin": buyer.user_id.user.is_admin,
                                    "type": "PostedForSale",
                                }
                                if (
                                    post_for_sale.type == "Bidding"
                                    and post_for_sale.withdrawn == False
                                ):
                                    bids = models.User_Bid.objects.filter(
                                        posted_for_sale_id=post_for_sale
                                    )
                                    if bids.count() != 0:
                                        bid_details = []
                                        for bid in bids:
                                            bid_detail = {
                                                "bid_id": bid.id,
                                                "user_id": bid.user_id.id,
                                                "bid_price": bid.per_unit_bid_price,
                                                "no_of_units": bid.no_of_units,
                                                "withdraw": bid.withdraw,
                                                "status": bid.status,
                                                "created_at": bid.datetime,
                                            }
                                            bid_details.append(bid_detail)

                                            highest_bid = (
                                                bids.aggregate(
                                                    Max("per_unit_bid_price")
                                                )["per_unit_bid_price__max"]
                                                if bids
                                                else None
                                            )

                                        invoice_data["bids"] = bid_details
                                        invoice_data["highest_bid"] = highest_bid

                                invoice_data_list.append(invoice_data)

            return Response(
                {"invoices": invoice_data_list, "user": user_role.id},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ToBuyAPIView(APIView):
    """
    API view for buying units from post for sale.
    """
    
    def post(self, request):
        try:
            userRoleID = request.data.get("user")
            postForSaleID = request.data.get("postForSaleID")
            no_of_units = int(request.data.get("no_of_units"))

            try:
                user_role = models.UserRole.objects.get(id=userRoleID)
            except models.UserRole.DoesNotExist:
                return Response({"message": "User not found"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                buyer_wallet = models.Wallet.objects.get(user_role=user_role)
            except models.Wallet.DoesNotExist:
                return Response({"message": "Buyer Wallet not found"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                postForSale = models.Post_for_sale.objects.get(id=postForSaleID)
            except models.Post_for_sale.DoesNotExist:
                return Response({"message": "postForSaleID not found"}, status=status.HTTP_400_BAD_REQUEST)

            if no_of_units <= 0:
                return Response(
                    {"message": "Number of units must be greater than zero"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            if postForSale.remaining_units < no_of_units:
                # Log the transaction as failed due to insufficient units
                admin_models.TransactionLog.objects.create(
                    user=user_role,
                    transaction_type="buy",
                    no_of_units=no_of_units,
                    per_unit_price=postForSale.per_unit_price,
                    total_price=postForSale.per_unit_price * no_of_units,
                    status="failed",  # Failed due to insufficient units
                    post_for_sale=postForSale,
                    remarks="Transaction failed due to not enough units available",
                )
                return Response(
                    {"message": "Not enough units available for sale"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            total_price = postForSale.per_unit_price * no_of_units

            if buyer_wallet.OutstandingBalance < total_price:
                # Log the transaction as failed due to insufficient balance
                admin_models.TransactionLog.objects.create(
                    user=user_role,
                    transaction_type="buy",
                    no_of_units=no_of_units,
                    per_unit_price=postForSale.per_unit_price,
                    total_price=total_price,
                    status="failed",  # Failed due to insufficient balance
                    post_for_sale=postForSale,
                    remarks="Transaction failed due to insufficient balance",
                )
                return Response(
                    {"message": "Insufficient balance in buyer's wallet"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Set initial transaction log as pending
            transaction_log = admin_models.TransactionLog.objects.create(
                user=user_role,
                transaction_type="buy",
                no_of_units=no_of_units,
                per_unit_price=postForSale.per_unit_price,
                total_price=total_price,
                status="pending",  # Pending before the transaction starts
                post_for_sale=postForSale,
                remarks="Transaction pending",
            )

            with transaction.atomic():
                buyer = models.Buyers.objects.create(
                    user_id=user_role,
                    no_of_units=no_of_units,
                    per_unit_price_invested=postForSale.per_unit_price,
                    wallet=buyer_wallet,
                    purchase_date=timezone.now().date(),
                    purchase_time=timezone.now().time(),
                    purchase_date_time=timezone.now(),
                )

                sales = models.Sales.objects.create(
                    UserID=postForSale.user_id,
                    Invoice=postForSale.invoice_id,
                    no_of_units=no_of_units,
                    sell_date=timezone.now().date(),
                    sell_time=timezone.now().time(),
                    sell_date_time=timezone.now(),
                )

                units_for_sale = models.Post_For_Sale_UnitTracker.objects.filter(
                    post_for_saleID=postForSale, sellersID__isnull=True
                ).order_by("id")[:no_of_units]

                if units_for_sale.count() < no_of_units:
                    # Log the transaction as failed due to not enough units
                    transaction_log.status = "failed"
                    transaction_log.remarks = "Transaction failed due to not enough units available"
                    transaction_log.save()

                    return Response(
                        {"message": "Not enough units available for sale"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                for unit in units_for_sale:
                    models.Post_For_Sale_UnitTracker.objects.filter(id=unit.id).update(sellersID=sales)

                    models.Buyer_UnitsTracker.objects.create(
                        buyer_id=buyer, unitID=unit.unitID
                    )

                    models.Sales_UnitTracker.objects.create(
                        unitID=unit.unitID, sellersID=sales
                    )
                    models.FractionalUnits.objects.filter(id=unit.unitID.id).update(current_owner=user_role)

                    models.SalePurchaseReport.objects.create(
                        invoiceID = postForSale.invoice_id,
                        unitID = unit.unitID,
                        seller_ID = postForSale.user_id,
                        buyerID_ID = user_role,
                        Sale_Buy_Date = timezone.now().date(),
                        Sale_Buy_per_unit_price = postForSale.per_unit_price,
                        ListingDate = timezone.now().date(),
                        transfer_date = timezone.now().date(),
                        no_of_days_units_held = (sales.sell_date - postForSale.post_date).days,
                        interest_due_to_seller = (postForSale.per_unit_price * 10) / 100,
                        TDS_deducted = (postForSale.per_unit_price * 10) / 100,
                        IRR = postForSale.invoice_id.irr
                    )

                buyer_wallet.OutstandingBalance -= total_price
                buyer_wallet.save()

                try:
                    seller_wallet = models.Wallet.objects.get(
                        user_role=postForSale.user_id
                    )
                except models.Wallet.DoesNotExist:
                    return Response(
                        {"message": "Seller wallet is not made"}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

                seller_wallet.OutstandingBalance += total_price
                seller_wallet.save()

                models.WalletTransaction.objects.create(
                    wallet=buyer_wallet,
                    type="buy",
                    debitedAmount=total_price,
                    status="response",
                    source="wallet_to_buy",
                    from_wallet=buyer_wallet,
                    to_wallet=seller_wallet,
                    invoice=postForSale.invoice_id,
                    time_date=timezone.now(),
                )

                models.WalletTransaction.objects.create(
                    wallet=seller_wallet,
                    type="sell",
                    creditedAmount=total_price,
                    status="response",
                    source="sell_to_wallet",
                    from_wallet=buyer_wallet,
                    to_wallet=seller_wallet,
                    invoice=postForSale.invoice_id,
                    time_date=timezone.now(),
                )

                postForSale.remaining_units -= no_of_units
                postForSale.save()

                if postForSale.remaining_units == 0:
                    models.Post_for_sale.objects.filter(id=postForSale.id).update(sold=True)

                # Update transaction status to completed after successful transaction
                transaction_log.status = "completed"
                transaction_log.remarks = "Buy transaction completed successfully"
                transaction_log.save()

            return Response(
                {
                    "message": "Units bought successfully",
                    "buyer_id": buyer.id,
                    "user": user_role.id,
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ToSellAPIView(APIView):
    """
    API view for selling units.
    """
    
    def post(self, request):
        try:
            userRoleID = request.data.get('user')
            buyerID = request.data.get('buyerID')
            no_of_units = request.data.get('no_of_units')
            per_unit_price = request.data.get('per_unit_price')
            total_price = no_of_units * per_unit_price
            from_date = request.data.get('from_date')
            to_date = request.data.get('to_date')
            type_of_sell = request.data.get('type_of_sell')

            if not all([userRoleID, buyerID, no_of_units, per_unit_price, from_date, to_date, type_of_sell]):
                return Response({"message": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user_role = models.UserRole.objects.get(id=userRoleID)
            except models.UserRole.DoesNotExist:
                return Response({"message": "User role not found"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                buyer = models.Buyers.objects.get(id=buyerID)
            except models.Buyers.DoesNotExist:
                return Response({"message": "Buyer not found"}, status=status.HTTP_400_BAD_REQUEST)

            transaction_log = admin_models.TransactionLog.objects.create(
                user=user_role,
                transaction_type="sell",
                no_of_units=no_of_units,
                per_unit_price=per_unit_price,
                total_price=total_price,
                status="pending",
                post_for_sale=None,
                buyer=buyer,
                remarks="Sell transaction pending",
            )

            with transaction.atomic():
                try:
                    buyer_Units = models.Buyer_UnitsTracker.objects.filter(buyer_id=buyer, post_for_saleID=None).order_by('id')[:no_of_units]
                except models.Buyer_UnitsTracker.DoesNotExist:
                    transaction_log.status = "failed"
                    transaction_log.remarks = "Buyer units do not exist or insufficient units for post for sale"
                    transaction_log.save()
                    return Response({"message": "Buyer units do not exist or not sufficient units for post for sale"}, status=status.HTTP_400_BAD_REQUEST)

                if buyer_Units.count() < no_of_units:
                    transaction_log.status = "failed"
                    transaction_log.remarks = "Not enough units available for selling"
                    transaction_log.save()
                    return Response({"message": "Not enough units available for selling"}, status=status.HTTP_400_BAD_REQUEST)

                for buyer_unit in buyer_Units:
                    invoice = buyer_unit.unitID.invoice
                    break

                if type_of_sell == "FIXED":
                    open_to_bid = False
                    bid_type = "Fixed"  # Added a reasonable default value
                elif type_of_sell == "BIDDABLE":
                    open_to_bid = True
                    bid_type = "Bidding"
                else:
                    return Response({"message": "type_of_sell should be FIXED or BIDDABLE"}, status=status.HTTP_400_BAD_REQUEST)

                post_for_sale = models.Post_for_sale.objects.create(
                    no_of_units=no_of_units,
                    per_unit_price=per_unit_price,
                    user_id=user_role,
                    invoice_id=invoice,
                    remaining_units=no_of_units,
                    total_price=(no_of_units * per_unit_price),
                    withdrawn=False,
                    post_time=timezone.now().time(),
                    post_date=timezone.now().date(),
                    from_date=from_date,
                    to_date=to_date,
                    sold=False,
                    type=bid_type,
                    no_of_bid=0,
                    open_for_bid=open_to_bid,
                    post_dateTime=timezone.now(),
                    is_admin=user_role.user.is_admin  # handle case : user_role.user.is_admin == admin then he can't do bidding
                )

                for buyer_unit in buyer_Units:
                    models.Buyer_UnitsTracker.objects.filter(id=buyer_unit.id).update(post_for_saleID=post_for_sale)

                    models.Post_For_Sale_UnitTracker.objects.create(
                        unitID=buyer_unit.unitID, post_for_saleID=post_for_sale
                    )

                transaction_log.status = "completed"
                transaction_log.post_for_sale = post_for_sale
                transaction_log.remarks = "Sell transaction recorded successfully"
                transaction_log.save()

            return Response(
                {
                    "message": "Sell transaction recorded successfully",
                    "user": user_role.id,
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CheckBalanceAgainstBidPriceAPIView(APIView):
    """
    API view for checking if a user has sufficient balance for bidding.
    """
    
    def post(self, request):
        try:
            userRoleID = request.data.get("user")
            bid_price = request.data.get("bid_price")

            if not all([userRoleID, bid_price]):
                return Response(
                    {"message": "All fields are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                user_role = models.UserRole.objects.get(id=userRoleID)
            except models.UserRole.DoesNotExist:
                return Response(
                    {"message": "User role not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            try:
                wallet = models.Wallet.objects.get(user_role=user_role)
            except models.Wallet.DoesNotExist:  # Fixed exception type
                return Response(
                    {"message": "Wallet not found for the given user", "user": user_role.id},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if wallet.OutstandingBalance < bid_price:
                return Response(
                    {"message": "Insufficient balance to bid", "user": user_role.id},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                {"message": "Can bid", "user": user_role.id},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {"message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProceedToBidAPIView(APIView):
    """
    API view for placing a bid on a post for sale.
    """
    
    def post(self, request):
        try:
            userRoleID = request.data.get("user")
            per_unit_bid_price = request.data.get("per_unit_bid_price")
            no_of_units = request.data.get("no_of_units")
            postForSaleID = request.data.get("postForSaleID")

            if not all([userRoleID, per_unit_bid_price, no_of_units, postForSaleID]):
                return Response(
                    {"message": "All fields are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                user_role = models.UserRole.objects.get(id=userRoleID)
            except models.UserRole.DoesNotExist:
                return Response(
                    {"message": "User role not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                postForSale = models.Post_for_sale.objects.get(id=postForSaleID)
            except models.Post_for_sale.DoesNotExist:
                return Response(
                    {"message": "postForSaleID not found"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if no_of_units > postForSale.remaining_units:
                return Response(
                    {
                        "message": f"Not enough units available. You can bid for up to {postForSale.remaining_units} units."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            total_bid_price = no_of_units * per_unit_bid_price

            try:
                user_wallet = models.Wallet.objects.get(user_role=user_role)
            except models.Wallet.DoesNotExist:
                return Response(
                    {"message": "Wallet not found for the given user"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if user_wallet.OutstandingBalance < total_bid_price:
                return Response(
                    {
                        "message": f"Insufficient balance. You need {total_bid_price} to place this bid, but your balance is {user_wallet.OutstandingBalance}."  # Fixed attribute name
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                user_bid = models.User_Bid.objects.create(
                    posted_for_sale_id=postForSale,
                    status="awaiting_acceptance",
                    user_id=user_role,
                    per_unit_bid_price=per_unit_bid_price,
                    no_of_units=no_of_units,
                    updated_at=timezone.now(),
                    datetime=timezone.now(),
                )
                
                models.Post_for_sale.objects.filter(id=postForSale.id).update(
                    no_of_bid=(postForSale.no_of_bid + 1)
                )

            return Response(
                {
                    "message": "Bid placed successfully",
                    "user_bid_id": user_bid.id,
                    "user": user_role.id,
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# updated_at post for sale table upadate
class ModifyBidAPIView(APIView):
    """
    API view for modifying bids by sellers or bidders.
    """
    
    def put(self, request):
        try:
            userRoleID = request.data.get("user")
            per_unit_price = request.data.get("per_unit_price")
            no_of_units = request.data.get("no_of_units")
            type = request.data.get("type")

            if not all([userRoleID, per_unit_price, no_of_units, type]):
                return Response(
                    {"message": "All fields are required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                user_role = models.UserRole.objects.get(id=userRoleID)
            except models.UserRole.DoesNotExist:
                return Response(
                    {"message": "User role not found"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            if type == "SELLER":
                buyerID = request.data.get("buyerID")
                postedForSaleID = request.data.get("postedForSaleID")

                if not all([buyerID, postedForSaleID]):
                    return Response(
                        {"message": "All fields are required"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                try:
                    postedForSale = models.Post_for_sale.objects.get(id=postedForSaleID)
                except models.Post_for_sale.DoesNotExist:
                    return Response(
                        {"message": "postedforsaleID not found"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                try:
                    buyer = models.Buyers.objects.get(id=buyerID)
                except models.Buyers.DoesNotExist:
                    return Response(
                        {"message": "Buyer not found"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                try:
                    buyer_Units = models.Buyer_UnitsTracker.objects.filter(
                        buyer_id=buyer, post_for_saleID=postedForSale
                    ).order_by("id")[:no_of_units]
                except models.Buyer_UnitsTracker.DoesNotExist:
                    return Response(
                        {
                            "message": "buyer unit does not exits or Not sufficient units for post for sale"
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if buyer_Units.count() < no_of_units:
                    return Response(
                        {
                            "message": f"Not enough units available for selling, You can bid up to {buyer_Units.count()} units only."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if postedForSale.type != "Bidding":
                    return Response(
                        {"message": "Only Biddable invoice can modify"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )

                if postedForSale.withdrawn == True:
                    return Response(
                        {"message": "Only non - withdraw invoice can modify"},
                        status=status.HTTP_403_FORBIDDEN
                    )

                active_bids = models.User_Bid.objects.filter(
                    posted_for_sale_id=postedForSale, status="awaiting_acceptance"
                ).exists()
                if active_bids:
                    return Response(
                        {"message": "Cannot modify post with active bids"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )

                expired_bids = models.User_Bid.objects.filter(
                    posted_for_sale_id=postedForSale, status="expired"
                ).exists()
                if expired_bids:
                    return Response(
                        {"message": "Cannot modify post with expired bids"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )

                with transaction.atomic():
                    if postedForSale.user_id != user_role:
                        return Response(
                            {"message": "check user id"}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    models.Post_for_sale.objects.filter(id=postedForSale.id).update(
                        per_unit_price=per_unit_price,
                        no_of_units=no_of_units,
                        remaining_units=no_of_units,
                        total_price=(per_unit_price*no_of_units)
                    )
                    
                    return Response(
                        {
                            "message": "Successfully updated the post for sale",
                            "user": user_role.id,
                            "postedForSaleID": postedForSale.id
                        }, 
                        status=status.HTTP_200_OK
                    )

            elif type == "BIDDER":
                userBidID = request.data.get("userBidID")

                if not userBidID:
                    return Response(
                        {"message": "userBidID is required"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                try:
                    userBid = models.User_Bid.objects.get(id=userBidID)
                except models.User_Bid.DoesNotExist:
                    return Response(
                        {"message": "User Bid ID not found"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                postedForSale = userBid.posted_for_sale_id

                if userBid.posted_for_sale_id.no_of_units < no_of_units:
                    return Response(
                        {
                            "message": f"You can bid up to {userBid.posted_for_sale_id.no_of_units}"
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if postedForSale.withdrawn == True:
                    return Response(
                        {"message": "Only non - withdraw invoice can modify"},
                        status=status.HTTP_403_FORBIDDEN
                    )

                funded_bids = models.User_Bid.objects.filter(
                    posted_for_sale_id=postedForSale, status="closed"
                ).exists()
                if funded_bids:
                    return Response(
                        {"message": "Cannot modify post with closed bids"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )

                expired_bids = models.User_Bid.objects.filter(
                    posted_for_sale_id=postedForSale, status="expired"
                ).exists()
                if expired_bids:
                    return Response(
                        {"message": "Cannot modify post with expired bids"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )

                with transaction.atomic():
                    models.User_Bid.objects.filter(id=userBid.id).update(
                        no_of_units=no_of_units,
                        per_unit_bid_price=per_unit_price,
                        updated_at=timezone.now()
                    )
                    
                    return Response(
                        {
                            "message": "Successfully updated the bid",
                            "user": user_role.id,
                            "userBidID": userBid.id
                        }, 
                        status=status.HTTP_200_OK
                    )
            else:
                return Response(
                    {
                        "message": "type should be SELLER or BIDDER",
                        "user": user_role.id
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            return Response(
                {"message": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WithdrawBidAPIView(APIView):
    """
    API view for withdrawing bids by sellers or bidders.
    """
    
    def put(self, request):
        try:
            userRoleID = request.data.get("user")
            type = request.data.get("type")

            if not all([userRoleID, type]):
                return Response(
                    {"message": "All fields are required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                user_role = models.UserRole.objects.get(id=userRoleID)
            except models.UserRole.DoesNotExist:
                return Response(
                    {"message": "User role not found"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            if type == "SELLER":
                postedForSaleID = request.data.get("postedForSaleID")
                if not postedForSaleID:
                    return Response(
                        {"message": "All fields are required"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                try:
                    postedForSale = models.Post_for_sale.objects.get(id=postedForSaleID)
                except models.Post_for_sale.DoesNotExist:
                    return Response(
                        {"message": "postedForSale not found"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if postedForSale.type != "Bidding":
                    return Response(
                        {"message": "Only Biddable invoice can withdraw"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )

                active_bids = models.User_Bid.objects.filter(
                    posted_for_sale_id=postedForSale, status="awaiting_acceptance"
                ).exists()
                if active_bids:
                    return Response(
                        {"message": "Cannot modify post with active bids"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )

                expired_bids = models.User_Bid.objects.filter(
                    posted_for_sale_id=postedForSale, status="expired"
                ).exists()
                if expired_bids:
                    return Response(
                        {"message": "Cannot modify post with expired bids"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )

                if postedForSale.user_id != user_role:
                    return Response(
                        {"message": "check user id"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                with transaction.atomic():
                    models.Post_for_sale.objects.filter(id=postedForSale.id).update(
                        withdrawn=True,
                        open_for_bid=False
                    )
                    
                    return Response(
                        {
                            "message": "Successfully withdrawn the post for sale",
                            "user": user_role.id,
                            "postedForSaleID": postedForSale.id
                        }, 
                        status=status.HTTP_200_OK
                    )

            elif type == "BIDDER":
                userbidID = request.data.get("userbidID")
                if not userbidID:
                    return Response(
                        {"message": "All fields are required"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                try:
                    userbid = models.User_Bid.objects.get(id=userbidID)
                except models.User_Bid.DoesNotExist:
                    return Response(
                        {"message": "user bid ID not found"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                postedForSale = userbid.posted_for_sale_id

                expired_bids = models.User_Bid.objects.filter(
                    posted_for_sale_id=postedForSale, status="expired"
                ).exists()
                if expired_bids:
                    return Response(
                        {"message": "Cannot modify post with expired bids"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )

                closed_bids = models.User_Bid.objects.filter(
                    posted_for_sale_id=postedForSale, status="closed"
                ).exists()
                if closed_bids:
                    return Response(
                        {"message": "Cannot modify post with closed bids"}, 
                        status=status.HTTP_403_FORBIDDEN
                    )

                with transaction.atomic():
                    models.User_Bid.objects.filter(id=userbid.id).update(withdraw=True)
                    
                    return Response(
                        {
                            "message": "Successfully withdrawn the bid",
                            "user": user_role.id
                        }, 
                        status=status.HTTP_200_OK
                    )

            else:
                return Response(
                    {
                        "message": "type should be SELLER or BIDDER",
                        "user": user_role.id,
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            return Response(
                {"message": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AcceptBidAPIView(APIView):
    """
    API view for accepting bids.
    """
    
    def post(self, request):
        try:
            userRoleID = request.data.get("user")
            userBidID = request.data.get("userBidID")

            if not all([userRoleID, userBidID]):
                return Response(
                    {"message": "All fields are required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                user_role = models.UserRole.objects.get(id=userRoleID)
            except models.UserRole.DoesNotExist:
                return Response(
                    {"message": "User role not found"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                user_bid = models.User_Bid.objects.get(id=userBidID)
            except models.User_Bid.DoesNotExist:
                return Response(
                    {"message": "User bid id not found"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            if user_bid.status != "awaiting_acceptance":
                return Response(
                    {"message": "Bid is already closed or accepted"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                post_for_sale = user_bid.posted_for_sale_id

                post_for_sale.remaining_units -= user_bid.no_of_units
                post_for_sale.save()
                
                if post_for_sale.remaining_units == 0:
                    models.Post_for_sale.objects.filter(id=post_for_sale.id).update(
                        sold=True,
                        open_for_bid=False
                    )

                units_to_transfer = models.Post_For_Sale_UnitTracker.objects.filter(
                    post_for_saleID=post_for_sale,
                    unitID__posted_for_sale=True,
                    sellersID__isnull=True,
                )[: user_bid.no_of_units]
                
                if units_to_transfer.count() < user_bid.no_of_units:
                    return Response(
                        {"message": "Not enough units"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                buyer_id = user_bid.user_id
                try:
                    buyer_wallet = models.Wallet.objects.get(user_role=buyer_id)
                except models.Wallet.DoesNotExist:
                    return Response(
                        {"message": "buyer wallet doesn't exist"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                seller_id = post_for_sale.user_id
                try:
                    seller_wallet = models.Wallet.objects.get(user_role=seller_id)
                except models.Wallet.DoesNotExist:
                    return Response(
                        {"message": "seller wallet doesn't exist"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                buyer_entry = models.Buyers.objects.create(
                    user_id=user_bid.user_id,
                    no_of_units=user_bid.no_of_units,
                    per_unit_price_invested=user_bid.per_unit_bid_price,
                    wallet=buyer_wallet,
                    purchase_date=timezone.now().date(),
                    purchase_time=timezone.now().time(),
                    purchase_date_time=timezone.now(),
                )

                sale_entry = models.Sales.objects.create(
                    UserID=post_for_sale.user_id,
                    Invoice=post_for_sale.invoice_id,
                    no_of_units=user_bid.no_of_units,
                    sell_date=timezone.now().date(),
                    sell_time=timezone.now().time(),
                    sell_date_time=timezone.now(),
                )

                for unit in units_to_transfer:
                    models.FractionalUnits.objects.filter(id=unit.unitID.id).update(
                        current_owner=user_bid.user_id
                    )

                    models.Buyer_UnitsTracker.objects.create(
                        buyer_id=buyer_entry, unitID=unit.unitID
                    )

                    models.Sales_UnitTracker.objects.create(
                        unitID=unit.unitID, sellersID=sale_entry
                    )

                    models.BidReport.objects.create(
                        unitID=unit.unitID,
                        user_BidID=user_bid,
                        post_for_saleID=unit.post_for_saleID,
                        ListingDate=timezone.now().date(),
                        created_at=timezone.now()
                    )

                models.User_Bid.objects.filter(id=user_bid.id).update(status='Accepted')
                models.User_Bid.objects.filter(
                    posted_for_sale_id=post_for_sale, 
                    status='awaiting_acceptance'
                ).update(status='closed')

                total_amount = user_bid.no_of_units * user_bid.per_unit_bid_price

                if buyer_wallet.OutstandingBalance < total_amount:
                    return Response(
                        {"message": "Insufficient wallet balance"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                buyer_wallet.OutstandingBalance -= total_amount
                seller_wallet.OutstandingBalance += total_amount
                buyer_wallet.save()
                seller_wallet.save()

                models.WalletTransaction.objects.create(
                    wallet=buyer_wallet,
                    type="buy",
                    debitedAmount=total_amount,
                    status="response",
                    source="wallet_to_buy",
                    purpose="Bid Acceptance",
                    time_date=timezone.now(),
                )

                models.WalletTransaction.objects.create(
                    wallet=seller_wallet,
                    type="sell",
                    creditedAmount=total_amount,
                    status="response",
                    source="sell_to_wallet",
                    purpose="Bid Acceptance",
                    time_date=timezone.now(),
                )

                return Response(
                    {
                        "user": user_role.id,
                        "message": "Bid accepted successfully and updated",
                    },
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            return Response(
                {"message": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CashFlowAPIView(APIView):
    """
    API view for retrieving cash flow information for an invoice.
    """
    
    def get(self, request, invoiceID):
        try:
            try:
                invoice = models.Invoices.objects.get(id=invoiceID)
            except models.Invoices.DoesNotExist:
                return Response(
                    {"message": "invoiceID not found"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            primary_invoice_id = invoice.primary_invoice_id
            
            url = "http://backend.ethyx.in/admin-api/payment-schedule-calculator/"
            headers = {
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzIyMzQyNzUwLCJpYXQiOjE3MjIyNTYzNTAsImp0aSI6ImZlMjAwMzM1OTYzNjRmNTRhYjA3ZTE4NWU4ZDI5NWJkIiwidWlkIjoiQVNOV1ROODI4NSJ9.8_yy4cwJGrJ8z2UsRcAYl7Hr3-1xGfIGoY4TFQ3JZng",
                "Content-Type": "application/json",
            }

            payload = {"invoice_product_id": 8}  # You might want to use primary_invoice_id here

            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                return Response(
                    {"CashFlow": response.json()}, 
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"message": response.json()}, 
                    status=response.status_code
                )

        except Exception as e:
            return Response(
                {"message": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@csrf_exempt
def create_entry(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            time_str = data.get("interest_cut_off_time")

            if not time_str:
                return JsonResponse({"message": "Time is required"}, status=400)

            interest_cut_off_time = parse_time(time_str)
            if not interest_cut_off_time:
                return JsonResponse({"message": "Invalid time format"}, status=400)

            new_entry = models.AdminSettings.objects.create(
                interest_cut_off_time=interest_cut_off_time
            )
            return JsonResponse(
                {
                    "message": "Entry created successfully",
                    "id": new_entry.id,
                    "interest_cut_of_time": new_entry.interest_cut_off_time,
                },
                status=201,
            )

        except json.JSONDecodeError:
            return JsonResponse({"message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=500)
    else:
        return JsonResponse({"message": "Only POST method is allowed"}, status=405)
