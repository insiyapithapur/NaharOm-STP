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

# for rest framework
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
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
    
@csrf_exempt
def ProfileAPI(request, user=None):
    if request.method == "POST":
        data = json.loads(request.body)
        userID = data.get("user")

        if not userID:
            return JsonResponse({"message": "userID should be there"}, status=400)

        with transaction.atomic():
            try:
                user_role = models.UserRole.objects.get(id=userID)
                user = user_role.user
                # print(user_role.id)
                if user_role.role == "Individual":
                    alternatePhone = data.get("alternatePhone")
                    email = data.get("email")
                    address1 = data.get("address1")
                    address2 = data.get("address2")
                    panCardNumber = data.get("panCardNumber")
                    firstName = data.get("firstName")
                    lastName = data.get("lastName")
                    state = data.get("state")
                    city = data.get("city")
                    postalCode = data.get("postalCode")

                    if not all(
                        [
                            alternatePhone,
                            email,
                            address1,
                            address2,
                            firstName,
                            lastName,
                            state,
                            city,
                            postalCode,
                        ]
                    ):
                        return JsonResponse(
                            {"message": "All fields are required"}, status=400
                        )

                    print("email", email)
                    user.email = email
                    user.save()
                    print("userRole.user.email", user_role.user.email)

                    try:
                        # update
                        # print("jbdcfh ")
                        individualProfileExistence = (
                            models.IndividualDetails.objects.get(user_role=user_role)
                        )
                        # print(individualProfileExistence)
                        individualProfileExistence.first_name = firstName
                        individualProfileExistence.last_name = lastName
                        individualProfileExistence.addressLine1 = address1
                        individualProfileExistence.addressLine2 = address2
                        individualProfileExistence.city = city
                        individualProfileExistence.state = state
                        individualProfileExistence.pin_code = postalCode
                        individualProfileExistence.alternate_phone_no = alternatePhone
                        individualProfileExistence.updated_at = timezone.now()
                        individualProfileExistence.save()

                        try:
                            pancards = models.PanCardNos.objects.get(
                                user_role=user_role
                            )
                            pancards.pan_card_no = panCardNumber
                            pancards.save()
                        except:
                            return JsonResponse(
                                {
                                    "message": "pan card entery is not there but Individual details is there"
                                },
                                status=400,
                            )

                        return JsonResponse(
                            {
                                "message": "Successfully entered individual profile",
                                "indiviual_profileID": individualProfileExistence.id,
                                "user": user_role.id,
                            },
                            status=200,
                        )

                        #   models.IndividualDetails.DoesNotExist and models.PanCardNos.DoesNotExist == True then only create thase
                    except models.IndividualDetails.DoesNotExist:
                        try:
                            models.PanCardNos.objects.get(user_role=user_role)
                            return JsonResponse(
                                {
                                    "message": "PAN card already exists but individual profile does not"
                                },
                                status=400,
                            )
                        except models.PanCardNos.DoesNotExist:
                            if not panCardNumber:
                                return JsonResponse(
                                    {
                                        "message": "panCardNumber is required as it is new user"
                                    },
                                    status=400,
                                )

                            # create
                            individualProfile = models.IndividualDetails.objects.create(
                                user_role=user_role,
                                first_name=firstName,
                                last_name=lastName,
                                addressLine1=address1,
                                addressLine2=address2,
                                city=city,
                                state=state,
                                pin_code=postalCode,
                                alternate_phone_no=alternatePhone,
                                created_at=timezone.now(),
                                updated_at=timezone.now(),
                            )

                            try:
                                pancards = models.PanCardNos.objects.get(
                                    user_role=user_role
                                )
                                return JsonResponse(
                                    {"message": "pan card entery is there"}, status=400
                                )
                            except:
                                panCard = models.PanCardNos.objects.create(
                                    user_role=user_role,
                                    pan_card_no=panCardNumber,
                                    created_at=timezone.now(),
                                )
                            return JsonResponse(
                                {
                                    "message": "Successfully entered individual profile",
                                    "indiviual_profileID": individualProfile.id,
                                    "panCard_NumberID": panCard.id,
                                    "user": user_role.id,
                                },
                                status=200,
                            )

                elif user_role.role == "Company":
                    company_name = data.get("company_name")
                    addressLine1 = data.get("addressLine1")
                    addressLine2 = data.get("addressLine2")
                    city = data.get("city")
                    state = data.get("state")
                    email = data.get("email")
                    pin_no = data.get("pin_no")
                    alternate_phone_no = data.get("alternate_phone_no")
                    company_pan_no = data.get("company_pan_no")
                    public_url_company = data.get("public_url_company")

                    if not all(
                        [
                            company_name,
                            addressLine1,
                            addressLine2,
                            city,
                            state,
                            email,
                            pin_no,
                            alternate_phone_no,
                            public_url_company,
                        ]
                    ):
                        return JsonResponse(
                            {"message": "All fields are required"}, status=400
                        )

                    user.email = email
                    user.save()

                    try:
                        companyProfileExistence = models.CompanyDetails.objects.get(
                            user_role=user_role
                        )
                        # update
                        companyProfileExistence.company_name = company_name
                        companyProfileExistence.addressLine1 = addressLine1
                        companyProfileExistence.addressLine2 = addressLine2
                        companyProfileExistence.city = city
                        companyProfileExistence.state = state
                        companyProfileExistence.pin_no = pin_no
                        companyProfileExistence.alternate_phone_no = alternate_phone_no
                        companyProfileExistence.public_url_company = public_url_company
                        companyProfileExistence.updated_at = timezone.now()
                        companyProfileExistence.save()

                        try:
                            pancards = models.PanCardNos.objects.get(
                                user_role=user_role
                            )
                            pancards.pan_card_no = company_pan_no
                            pancards.save()
                        except:
                            return JsonResponse(
                                {
                                    "message": "pan card entery is not there but company details is there"
                                },
                                status=400,
                            )

                        return JsonResponse(
                            {
                                "message": "Successfully entered company profile",
                                "company_ProfileID": companyProfileExistence.id,
                                "user": user_role.id,
                            },
                            status=200,
                        )
                    except models.CompanyDetails.DoesNotExist:
                        try:
                            models.PanCardNos.objects.get(user_role=user_role)
                            return JsonResponse(
                                {
                                    "message": "PAN card already exists but company profile does not"
                                },
                                status=400,
                            )
                        except models.PanCardNos.DoesNotExist:
                            if not company_pan_no:
                                return JsonResponse(
                                    {
                                        "message": "panCardNumber is required as it is new user"
                                    },
                                    status=400,
                                )
                            # create
                            companyProfile = models.CompanyDetails.objects.create(
                                user_role=user_role,
                                company_name=company_name,
                                addressLine1=addressLine1,
                                addressLine2=addressLine2,
                                city=city,
                                state=state,
                                pin_no=pin_no,
                                alternate_phone_no=alternate_phone_no,
                                public_url_company=public_url_company,
                                created_at=timezone.now(),
                                updated_at=timezone.now(),
                            )
                            panCard = models.PanCardNos.objects.create(
                                user_role=user_role,
                                pan_card_no=company_pan_no,
                                created_at=timezone.now(),
                            )

                            return JsonResponse(
                                {
                                    "message": "Successfully entered company profile",
                                    "company_ProfileID": companyProfile.id,
                                    "panCard_NumberID": panCard.id,
                                    "user": user_role.id,
                                },
                                status=200,
                            )
                else:
                    return JsonResponse({"message": "Role is not matched"}, status=400)
            except models.UserRole.DoesNotExist:
                return JsonResponse({"message": "userID does not found"}, status=400)

    elif request.method == "GET":
        # userID = request.GET.get('user')

        if not user:
            return JsonResponse({"message": "userID should be there"}, status=400)

        try:
            user_role = models.UserRole.objects.get(id=user)
            response_data = {
                "user": {
                    "id": user_role.id,
                    "email": user_role.user.email,
                    "mobile": user_role.user.mobile,
                    "role": user_role.role,
                }
            }

            if user_role.role == "Individual":
                try:
                    individual_details = models.IndividualDetails.objects.get(
                        user_role=user_role
                    )
                    response_data["profile"] = {
                        "first_name": individual_details.first_name,
                        "last_name": individual_details.last_name,
                        "addressLine1": individual_details.addressLine1,
                        "addressLine2": individual_details.addressLine2,
                        "city": individual_details.city,
                        "state": individual_details.state,
                        "pin_code": individual_details.pin_code,
                        "alternate_phone_no": individual_details.alternate_phone_no,
                    }
                except models.IndividualDetails.DoesNotExist:
                    return JsonResponse(
                        {"message": "Individual profile not found"}, status=400
                    )

            elif user_role.role == "Company":
                try:
                    company_details = models.CompanyDetails.objects.get(
                        user_role=user_role
                    )
                    response_data["profile"] = {
                        "company_name": company_details.company_name,
                        "addressLine1": company_details.addressLine1,
                        "addressLine2": company_details.addressLine2,
                        "city": company_details.city,
                        "state": company_details.state,
                        "pin_no": company_details.pin_no,
                        "alternate_phone_no": company_details.alternate_phone_no,
                        "public_url_company": company_details.public_url_company,
                    }
                except models.CompanyDetails.DoesNotExist:
                    return JsonResponse(
                        {"message": "Company profile not found"}, status=400
                    )

            return JsonResponse(response_data, status=200)
        except models.UserRole.DoesNotExist:
            return JsonResponse({"message": "user does not found"}, status=400)
    else:
        return JsonResponse({"message": "Only POST methods are allowed"}, status=405)


@csrf_exempt
def BankAccDetailsAPI(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_role_id = data.get("user")

            if not user_role_id:
                return JsonResponse({"message": "user is required"}, status=400)

            try:
                user_role = models.UserRole.objects.get(id=user_role_id)
            except models.UserRole.DoesNotExist:
                return JsonResponse({"message": "User role not found"}, status=400)

            try:
                # following details will come from 3rd party api
                account_number = data.get("account_number")
                ifc_code = data.get("ifc_code")
                account_type = data.get("account_type")

                if not account_number or not ifc_code or not account_type:
                    return JsonResponse(
                        {
                            "message": "account_number, ifc_code, and account_type are required"
                        },
                        status=400,
                    )

                is_exists = models.BankAccountDetails.objects.filter(
                    user_role=user_role
                ).exists()

                if is_exists:
                    bank_account_details = models.BankAccountDetails.objects.create(
                        user_role=user_role,
                        account_number=account_number,
                        ifc_code=ifc_code,
                        account_type=account_type,
                    )
                    try:
                        wallet = models.Wallet.objects.get(user_role=user_role)
                    except models.Wallet.DoesNotExist:
                        wallet = models.Wallet.objects.create(
                            user_role=user_role,
                            primary_bankID=bank_account_details,
                            OutstandingBalance=0,
                            updated_at=timezone.now(),
                        )
                    return JsonResponse(
                        {
                            "message": "Bank account details saved successfully",
                            "bank_account_id": bank_account_details.id,
                            "user": user_role.id,
                            "primary_bank": wallet.primary_bankID.id,
                            "primary_bank_AccNo": wallet.primary_bankID.account_number,
                        },
                        status=200,
                    )
                else:
                    # ek bhi nai hoi
                    bank_account_details = models.BankAccountDetails.objects.create(
                        user_role=user_role,
                        account_number=account_number,
                        ifc_code=ifc_code,
                        account_type=account_type,
                    )
                    try:
                        wallet = models.Wallet.objects.get(user_role=user_role)
                    except models.Wallet.DoesNotExist:
                        wallet = models.Wallet.objects.create(
                            user_role=user_role,
                            primary_bankID=bank_account_details,
                            OutstandingBalance=0,
                            updated_at=timezone.now(),
                        )
                    return JsonResponse(
                        {
                            "message": "Bank account details saved successfully",
                            "bank_account_id": bank_account_details.id,
                            "user": user_role.id,
                            "primary_bank": wallet.primary_bankID.id,
                            "primary_bank_AccNo": wallet.primary_bankID.account_number,
                        },
                        status=201,
                    )
            except json.JSONDecodeError:
                return JsonResponse({"message": "Invalid JSON"}, status=400)
            except Exception as e:
                return JsonResponse({"message": str(e)}, status=500)
            except KeyError:
                return JsonResponse({"message": "Missing required fields"}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=500)
    else:
        return JsonResponse({"message": "Only POST methods are allowed"}, status=405)


@csrf_exempt
def Credit_FundsAPI(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_role_id = data.get("user")
            amount = data.get("amount")

            if not user_role_id or not amount:
                return JsonResponse(
                    {"message": "user and amount are required"}, status=400
                )

            try:
                user_role = models.UserRole.objects.get(id=user_role_id)
            except models.UserRole.DoesNotExist:
                return JsonResponse({"message": "User role not found"}, status=400)

            try:
                wallet = models.Wallet.objects.get(user_role=user_role)
            except models.BankAccountDetails.DoesNotExist:
                return JsonResponse(
                    {"message": " Wallet not found for the given user"}, status=400
                )

            with transaction.atomic():
                try:
                    wallet.OutstandingBalance += amount
                    wallet.updated_at = timezone.now().date()
                    wallet.save()
                except models.Wallet.DoesNotExist:
                    return JsonResponse(
                        {"message": " Wallet not found for the given user"}, status=400
                    )

                Balancetransaction = models.WalletTransaction.objects.create(
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

                return JsonResponse(
                    {
                        "message": "Funds added successfully",
                        "user": user_role.id,
                        "wallet_balance": wallet.OutstandingBalance,
                        "primary_BankAccID": wallet.primary_bankID.id,
                        "primary_BankAccNo": wallet.primary_bankID.account_number,
                        "transaction_id": Balancetransaction.transaction_id,
                    },
                    status=200,
                )

        except json.JSONDecodeError:
            return JsonResponse({"message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=500)
    else:
        return JsonResponse({"message": "Only POST method is allowed"}, status=405)


@csrf_exempt
def Withdraw_FundsAPI(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_role_id = data.get("user")
            amount = data.get("amount")

            if not user_role_id or not amount:
                return JsonResponse(
                    {"message": "user and amount are required"}, status=400
                )

            try:
                user_role = models.UserRole.objects.get(id=user_role_id)
            except models.UserRole.DoesNotExist:
                return JsonResponse({"message": "User not found"}, status=400)

            try:
                wallet = models.Wallet.objects.get(user_role=user_role)
            except models.BankAccountDetails.DoesNotExist:
                return JsonResponse(
                    {"message": " Wallet not found for the given user"}, status=400
                )

            with transaction.atomic():
                try:
                    if wallet.OutstandingBalance < amount:
                        return JsonResponse(
                            {"message": "Not sufficient amount to do withdrawal"},
                            status=400,
                        )
                    wallet.OutstandingBalance -= amount
                    wallet.updated_at = timezone.now().date()
                    wallet.save()
                except models.Wallet.DoesNotExist:
                    return JsonResponse(
                        {"message": " Wallet not found for the given user"}, status=400
                    )

                Balancetransaction = models.WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_id=uuid.uuid4(),
                    type="Withdraw",
                    creditedAmount=None,
                    debitedAmount=amount,
                    status="response",
                    source="wallet_to_bank",
                    purpose="Funds debited from wallet",
                    to_bank_acc=wallet.primary_bankID,
                    from_wallet=wallet,
                    invoice=None,
                    time_date=timezone.now(),
                )

                return JsonResponse(
                    {
                        "message": "Funds debited successfully",
                        "user": user_role.id,
                        "wallet_balance": wallet.OutstandingBalance,
                        "primary_BankAccID": wallet.primary_bankID.id,
                        "primary_BankAccNo": wallet.primary_bankID.account_number,
                        "transaction_id": Balancetransaction.transaction_id,
                    },
                    status=200,
                )

        except json.JSONDecodeError:
            return JsonResponse({"message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=500)
    else:
        return JsonResponse({"message": "Only POST method is allowed"}, status=405)


@csrf_exempt
def LedgerAPI(request, user):
    if request.method == "GET":
        try:
            try:
                user_role = models.UserRole.objects.get(id=user)
            except models.UserRole.DoesNotExist:
                return JsonResponse({"message": "User role not found"}, status=400)

            wallet = models.Wallet.objects.filter(user_role=user_role)
            if not wallet.exists():
                return JsonResponse(
                    {"message": "No wallets found for this user role"}, status=400
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

                Balancewallet = wallet.first()
            return JsonResponse(
                {
                    "transactions": transactions_data,
                    "Balance": Balancewallet.OutstandingBalance,
                    "user": user_role.id,
                },
                status=200,
            )

        except Exception as e:
            return JsonResponse({"message": str(e)}, status=500)
    else:
        return JsonResponse({"message": "Only GET method is allowed"}, status=405)


@csrf_exempt
def ShowFundsAPI(request, user_role_id):
    if request.method == "GET":
        try:
            balance = models.Wallet.objects.get(
                user_role=user_role_id
            ).OutstandingBalance
            return JsonResponse({"Balance": balance}, status=200)
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=500)
    else:
        return JsonResponse({"message": "Only GET method is allowed"}, status=405)


@csrf_exempt
def GetSellPurchaseDetailsAPI(request, user):
    if request.method == "GET":
        try:
            try:
                userRole = models.UserRole.objects.get(id=user)
            except models.UserRole.DoesNotExist:
                return JsonResponse({"message": "user doesn't exist"}, status=400)

            invoices = models.Invoices.objects.filter(expired=False)

            invoice_data_list = []

            for invoice in invoices:
                post_for_sales = models.Post_for_sale.objects.filter(
                    invoice_id=invoice,
                    sold=False,
                    remaining_units__gt=0,
                    withdrawn=False,
                ).exclude(user_id=userRole)
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
                        print("bids.count()sxass", bids.count())
                        bid_details = []
                        for bid in bids:
                            print("bid.id saasx ", bid.id)
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
                user_id=userRole, status="awaiting_acceptance"
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
                    'Invoice_total_price' : bid.posted_for_sale_id.total_price ,
                    'Invoice_name': bid.posted_for_sale_id.invoice_id.product_name,
                    'Invoice_post_date': bid.posted_for_sale_id.post_date,
                    'Invoice_post_time': bid.posted_for_sale_id.post_time,
                    'Invoice_interest': bid.posted_for_sale_id.invoice_id.interest,
                    'Invoice_xirr': bid.posted_for_sale_id.invoice_id.xirr,
                    'Invoice_irr': bid.posted_for_sale_id.invoice_id.irr,
                    'Invoice_from_date' : bid.posted_for_sale_id.from_date,
                    'Invoice_to_date' : bid.posted_for_sale_id.to_date ,
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

            buyers = models.Buyers.objects.filter(user_id=userRole)
            for buyer in buyers:
                # not posted for sale
                buyer_units = models.Buyer_UnitsTracker.objects.filter(
                    buyer_id=buyer, post_for_saleID__isnull=True
                )
                buyer_units_count = buyer_units.count()
                # print("buyer_units_count : ",buyer_units_count)
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

                # print("invoice_data_list : ",invoice_data_list)

                # posted for sale
                buyer_units_posted_for_sale = models.Buyer_UnitsTracker.objects.filter(
                    buyer_id=buyer, post_for_saleID__isnull=False
                )
                # print("buyer_units_posted_for_sale.count() :",buyer_units_posted_for_sale.count())
                buyer_units_posted_for_sale_count = buyer_units_posted_for_sale.count()
                if buyer_units_posted_for_sale_count > 0:
                    # print("bjcvdsuj")
                    # Group the units by post_for_saleID
                    units_by_post_for_sale = defaultdict(list)
                    for unit in buyer_units_posted_for_sale:
                        units_by_post_for_sale[unit.post_for_saleID].append(unit)
                    # print("post_invoice")
                    first_unit = buyer_units_posted_for_sale.first()
                    if first_unit:
                        post_invoice = first_unit.unitID.invoice
                        # print("post_invoice:", post_invoice)

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
                                    print("post_for_sale ", post_for_sale.id)
                                    print(
                                        "post_for_sale.withdraw",
                                        post_for_sale.withdrawn,
                                    )
                                    bids = models.User_Bid.objects.filter(
                                        posted_for_sale_id=post_for_sale
                                    )
                                    print("bids.count()", bids.count())
                                    if bids.count() != 0:
                                        bid_details = []
                                        for bid in bids:
                                            print("bid.id ", bid.id)
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
                else:
                    print("dnkesbnzfvk")
                    pass
            return JsonResponse(
                {"invoices": invoice_data_list, "user": userRole.id}, status=200
            )
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=500)
    else:
        return JsonResponse({"message": "Only GET method is allowed"}, status=405)


@csrf_exempt
def TobuyAPI(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            userRoleID = data.get("user")
            postForSaleID = data.get("postForSaleID")
            no_of_units = int(data.get("no_of_units"))

            try:
                user_role = models.UserRole.objects.get(id=userRoleID)
            except models.UserRole.DoesNotExist:
                return JsonResponse({"message": "User not found"}, status=400)

            try:
                buyer_wallet = models.Wallet.objects.get(user_role=user_role)
                print("buyer_wallet:", buyer_wallet.primary_bankID)
            except models.Wallet.DoesNotExist:
                return JsonResponse({"message": "Buyer Wallet not found"}, status=400)

            try:
                postForSale = models.Post_for_sale.objects.get(id=postForSaleID)
            except models.Post_for_sale.DoesNotExist:
                return JsonResponse({"message": "postForSaleID not found"}, status=400)

            print("postForSale.remaining_units:", postForSale.remaining_units)
            print("no_of_units:", no_of_units)

            if no_of_units <= 0:
                return JsonResponse(
                    {"message": "Number of units must be greater than zero"}, status=400
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
                return JsonResponse(
                    {"message": "Not enough units available for sale"}, status=400
                )

            total_price = postForSale.per_unit_price * no_of_units
            print("Total price:", total_price)

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
                return JsonResponse(
                    {"message": "Insufficient balance in buyer's wallet"}, status=400
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

                print("units_for_sale.count():", units_for_sale.count())

                if units_for_sale.count() < no_of_units:
                    # Log the transaction as failed due to not enough units
                    transaction_log.status = "failed"
                    transaction_log.remarks = (
                        "Transaction failed due to not enough units available"
                    )
                    transaction_log.save()

                    return JsonResponse(
                        {"message": "Not enough units available for sale"}, status=400
                    )

                for unit in units_for_sale:
                    models.Post_For_Sale_UnitTracker.objects.filter(id=unit.id).update(sellersID=sales)
                    # unit.sellersID = sales
                    # unit.save()

                    models.Buyer_UnitsTracker.objects.create(
                        buyer_id=buyer, unitID=unit.unitID
                    )

                    models.Sales_UnitTracker.objects.create(
                        unitID=unit.unitID, sellersID=sales
                    )
                    models.FractionalUnits.objects.filter(id=unit.unitID.id).update(current_owner=user_role)
                    # unit.unitID.current_owner = user_role
                    # unit.unitID.save()

                    salespurchaseReport = models.SalePurchaseReport.objects.create(
                        invoiceID = postForSale.invoice_id ,
                        unitID = unit.unitID ,
                        seller_ID = postForSale.user_id,
                        buyerID_ID = user_role ,
                        Sale_Buy_Date = timezone.now().date(),
                        Sale_Buy_per_unit_price = postForSale.per_unit_price,
                        ListingDate = timezone.now().date(),
                        transfer_date = timezone.now().date(),
                        no_of_days_units_held = (sales.sell_date - postForSale.post_date).days,
                        interest_due_to_seller = ( postForSale.per_unit_price * 10 ) / 100,
                        TDS_deducted = ( postForSale.per_unit_price * 10 ) / 100,
                        IRR = postForSale.invoice_id.irr
                    )

                buyer_wallet.OutstandingBalance -= total_price
                buyer_wallet.save()

                try:
                    seller_wallet = models.Wallet.objects.get(
                        user_role=postForSale.user_id
                    )
                    print("seller_wallet:", seller_wallet.primary_bankID)
                except models.Wallet.DoesNotExist:
                    return JsonResponse(
                        {"message": "Seller wallet is not made"}, status=500
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

            return JsonResponse(
                {
                    "message": "Units bought successfully",
                    "buyer_id": buyer.id,
                    "user": user_role.id,
                },
                status=201,
            )
        except json.JSONDecodeError:
            return JsonResponse({"message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=500)
    else:
        return JsonResponse({"message": "Only POST method is allowed"}, status=405)


@csrf_exempt
def checkBalanceAgainstBidPrice(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            userRoleID = data.get("user")
            bid_price = data.get("bid_price")

            if not all([userRoleID, bid_price]):
                return JsonResponse(
                    {"message": "All fields are required", "user": user_role.id},
                    status=400,
                )

            try:
                user_role = models.UserRole.objects.get(id=userRoleID)
            except models.UserRole.DoesNotExist:
                return JsonResponse(
                    {"message": "User role not found", "user": user_role.id}, status=400
                )
            try:
                wallet = models.Wallet.objects.get(user_role=user_role)
            except models.BankAccountDetails.DoesNotExist:
                return JsonResponse(
                    {
                        "message": " Wallet not found for the given user",
                        "user": user_role.id,
                    },
                    status=400,
                )

            if wallet.OutstandingBalance < bid_price:
                return JsonResponse(
                    {"message": "Insufficient balance to bid", "user": user_role.id},
                    status=400,
                )

            return JsonResponse(
                {"message": "Can bid", "user": user_role.id}, status=200
            )
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=500)
    else:
        return JsonResponse({"message": "Only POST method is allowed"}, status=405)


@csrf_exempt
def proceedToBid(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            userRoleID = data.get("user")
            per_unit_bid_price = data.get("per_unit_bid_price")
            no_of_units = data.get("no_of_units")
            postForSaleID = data.get("postForSaleID")

            if not all([userRoleID, per_unit_bid_price, no_of_units, postForSaleID]):
                return JsonResponse({"message": "All fields are required"}, status=400)

            try:
                user_role = models.UserRole.objects.get(id=userRoleID)
            except models.UserRole.DoesNotExist:
                return JsonResponse(
                    {"message": "User role not found", "user": user_role.id}, status=400
                )

            try:
                postForSale = models.Post_for_sale.objects.get(id=postForSaleID)
            except models.Post_for_sale.DoesNotExist:
                return JsonResponse(
                    {"message": "postForSaleID not found", "user": user_role.id},
                    status=400,
                )

            if no_of_units > postForSale.remaining_units:
                return JsonResponse(
                    {
                        "message": f"Not enough units available. You can bid for up to {postForSale.remaining_units} units."
                    },
                    status=400,
                )

            total_bid_price = no_of_units * per_unit_bid_price

            user_wallet = models.Wallet.objects.get(user_role=user_role)

            if user_wallet.OutstandingBalance < total_bid_price:
                return JsonResponse(
                    {
                        "message": f"Insufficient balance. You need {total_bid_price} to place this bid, but your balance is {user_wallet.balance}.",
                        "user": user_role.id,
                    },
                    status=400,
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
                models.Post_for_sale.objects.filter(id=postForSale.id).update(no_of_bid=(postForSale.no_of_bid+1))
                # postForSale.no_of_bid += 1
                # postForSale.save()

            return JsonResponse(
                {
                    "message": "Bid placed successfully",
                    "user_bid_id": user_bid.id,
                    "user": user_role.id,
                },
                status=200,
            )

        except Exception as e:
            return JsonResponse({"message": str(e)}, status=500)
    else:
        return JsonResponse({"message": "Only POST method is allowed"}, status=405)


@csrf_exempt
def ToSellAPI(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            userRoleID = data.get('user')
            buyerID = data.get('buyerID')
            no_of_units = data.get('no_of_units')
            per_unit_price = data.get('per_unit_price')
            total_price = no_of_units*per_unit_price
            from_date = data.get('from_date')
            to_date = data.get('to_date')
            type_of_sell = data.get('type_of_sell')

            if not all([userRoleID, buyerID , no_of_units, per_unit_price,from_date,to_date,type_of_sell]):
                return JsonResponse({"message": "All fields are required"}, status=400)

            try:
                user_role = models.UserRole.objects.get(id=userRoleID)
            except models.UserRole.DoesNotExist:
                return JsonResponse({"message": "User role not found"}, status=400)

            try:
                buyer = models.Buyers.objects.get(id=buyerID)
            except models.Buyers.DoesNotExist:
                return JsonResponse({"message": "Buyer not found"}, status=400)

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
                try :
                    buyer_Units = models.Buyer_UnitsTracker.objects.filter(buyer_id=buyer , post_for_saleID = None).order_by('id')[:no_of_units]
                except models.Buyer_UnitsTracker.DoesNotExist:
                    transaction_log.status = "failed"
                    transaction_log.remarks = "Buyer units do not exist or insufficient units for post for sale"
                    transaction_log.save()
                    return JsonResponse({"message": "Buyer units do not exist or not sufficient units for post for sale"}, status=400)

                if buyer_Units.count() < no_of_units:
                    transaction_log.status = "failed"
                    transaction_log.remarks = "Not enough units available for selling"
                    transaction_log.save()
                    return JsonResponse({"message": "Not enough units available for selling"}, status=400)

                for buyer_unit in buyer_Units:
                    invoice = buyer_unit.unitID.invoice
                    break

                if type_of_sell == "FIXED":
                    open_to_bid = False
                elif type_of_sell == "BIDDABLE":
                    open_to_bid = True
                    bid_type = "Bidding"
                else :
                    return JsonResponse({"message": "type_of_sell should be FIXED or BIDDABLE"}, status=400)

                print("bid_type ",bid_type)
                post_for_sale = models.Post_for_sale.objects.create(
                    no_of_units = no_of_units ,
                    per_unit_price = per_unit_price ,
                    user_id = user_role ,
                    invoice_id = invoice ,
                    remaining_units = no_of_units ,
                    total_price =  ( no_of_units * per_unit_price ),
                    withdrawn = False ,
                    post_time = timezone.now().time() ,
                    post_date = timezone.now().date() ,
                    from_date = from_date ,
                    to_date = to_date ,
                    sold = False ,
                    type = bid_type,
                    no_of_bid = 0 ,
                    open_for_bid = open_to_bid ,
                    post_dateTime = timezone.now() ,
                    is_admin =  user_role.user.is_admin # handle case : user_role.user.is_admin == admin then he can't do bidding
                )

                for buyer_unit in buyer_Units:
                    models.Buyer_UnitsTracker.objects.filter(id=buyer_unit.id).update(post_for_saleID=post_for_sale)
                    # buyer_unit.post_for_saleID = post_for_sale
                    # buyer_unit.save()

                    models.Post_For_Sale_UnitTracker.objects.create(
                        unitID=buyer_unit.unitID, post_for_saleID=post_for_sale
                    )

                transaction_log.status = "completed"
                transaction_log.post_for_sale = post_for_sale
                transaction_log.remarks = "Sell transaction recorded successfully"
                transaction_log.save()

            return JsonResponse(
                {
                    "message": "Sell transaction recorded successfully",
                    "user": user_role.id,
                },
                status=201,
            )

        except json.JSONDecodeError:
            return JsonResponse({"message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=500)

    else:
        return JsonResponse({"message": "Only POST method is allowed"}, status=405)


@csrf_exempt
def AcceptBidAPI(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            userRoleID = data.get("user")
            userBidID = data.get("userBidID")

            if not all([userRoleID, userBidID]):
                return JsonResponse({"message": "All fields are required"}, status=400)

            try:
                user_role = models.UserRole.objects.get(id=userRoleID)
            except models.UserRole.DoesNotExist:
                return JsonResponse(
                    {"message": "User role not found", "user": user_role.id}, status=400
                )

            try:
                user_bid = models.User_Bid.objects.get(id=userBidID)
            except models.User_Bid.DoesNotExist:
                return JsonResponse(
                    {"message": "User bid id not found", "user": user_role.id},
                    status=400,
                )

            if user_bid.status != "awaiting_acceptance":
                return JsonResponse(
                    {"message": "Bid is already closed or accepted"}, status=400
                )
            print("xyz")
            with transaction.atomic():
                post_for_sale = user_bid.posted_for_sale_id

                post_for_sale.remaining_units -= user_bid.no_of_units
                if post_for_sale.remaining_units == 0:
                    models.Post_for_sale.objects.filter(id=post_for_sale.id).update(sold=True,open_for_bid=False)
                #     post_for_sale.sold = True
                #     post_for_sale.open_for_bid = False
                # post_for_sale.save()

                units_to_transfer = models.Post_For_Sale_UnitTracker.objects.filter(
                    post_for_saleID=post_for_sale,
                    unitID__posted_for_sale=True,
                    sellersID__isnull=True,
                )[: user_bid.no_of_units]
                print("units_to_transfer.count()", units_to_transfer.count())
                if units_to_transfer.count() < user_bid.no_of_units:
                    return JsonResponse({"message": "No enough units"}, status=400)

                buyer_id = user_bid.user_id
                try:
                    buyer_wallet = models.Wallet.objects.get(user_role=buyer_id)
                except models.Wallet.DoesNotExist:
                    return JsonResponse(
                        {"message": "buyer wallet doesn't exist"}, status=400
                    )

                seller_id = post_for_sale.user_id
                try:
                    seller_wallet = models.Wallet.objects.get(user_role=seller_id)
                except models.Wallet.DoesNotExist:
                    return JsonResponse(
                        {"message": "seller wallet doesn't exist"}, status=400
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
                )

                for unit in units_to_transfer:
                    models.FractionalUnits.objects.filter(id=unit.unitID.id).update(current_owner=user_bid.user_id)
                    # unit.unitID.current_owner = user_bid.user_id
                    # unit.unitID.save()

                    models.Buyer_UnitsTracker.objects.create(
                        buyer_id=buyer_entry, unitID=unit.unitID
                    )

                    models.Sales_UnitTracker.objects.create(
                        unitID=unit.unitID, sellersID=sale_entry
                    )

                    models.BidReport.objects.create(
                        unitID = unit.unitID,
                        user_BidID = user_bid,
                        post_for_saleID = unit.post_for_saleID,
                        ListingDate = timezone.now().date(),
                        created_at = timezone.now()
                    )

                # user_bid.status = 'closed'
                # user_bid.save()
                models.User_Bid.objects.filter(id=user_bid.id).update(status = 'Accepted')
                models.User_Bid.objects.filter(posted_for_sale_id=post_for_sale, status='awaiting_acceptance').update(status='closed')

                total_amount = user_bid.no_of_units * user_bid.per_unit_bid_price

                if buyer_wallet.OutstandingBalance < total_amount:
                    return JsonResponse(
                        {"message": "Insufficient wallet balance"}, status=400
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

                return JsonResponse(
                    {
                        "user": user_role.id,
                        "message": "Bid accepted successfully and updated",
                    },
                    status=200,
                )
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=500)
    else:
        return JsonResponse({"message": "Only POST method is allowed"}, status=405)


@csrf_exempt
def withdrawBid(request):
    if request.method == "PUT":
        try:
            data = json.loads(request.body)
            userRoleID = data.get("user")
            type = data.get("type")

            if not all([userRoleID, type]):
                return JsonResponse({"message": "All fields are required"}, status=400)

            try:
                user_role = models.UserRole.objects.get(id=userRoleID)
            except models.UserRole.DoesNotExist:
                return JsonResponse({"message": "User role not found"}, status=400)

            if type == "SELLER":
                postedForSaleID = data.get("postedForSaleID")
                if not all([postedForSaleID]):
                    return JsonResponse(
                        {"message": "All fields are required"}, status=400
                    )

                try:
                    postedForSale = models.Post_for_sale.objects.get(id=postedForSaleID)
                except models.Post_for_sale.DoesNotExist:
                    return JsonResponse(
                        {"message": "postedForSale not found"}, status=400
                    )

                if postedForSale.type != "Bidding":
                    return JsonResponse(
                        {"message": "Only Biddable invoice can withdraw"}, status=403
                    )

                active_bids = models.User_Bid.objects.filter(
                    posted_for_sale_id=postedForSale, status="awaiting_acceptance"
                ).exists()
                if active_bids:
                    return JsonResponse(
                        {"message": "Cannot modify post with active bids"}, status=403
                    )

                expired_bids = models.User_Bid.objects.filter(
                    posted_for_sale_id=postedForSale, status="expired"
                ).exists()
                if expired_bids:
                    return JsonResponse(
                        {"message": "Cannot modify post with expired bids"}, status=403
                    )

                if postedForSale.user_id != user_role:
                    return JsonResponse({"message": "chech user id "}, status=400)

                with transaction.atomic():
                    # postedForSale.withdrawn = True
                    # postedForSale.open_for_bid = False
                    # postedForSale.save()
                    models.Post_for_sale.objects.filter(id=postedForSale.id).update(withdrawn=True,open_for_bid=False)
                    return JsonResponse({"message": "Successfully withdrawn the post for sale","user":user_role.id,"postedForSaleID":postedForSale.id}, status=200)

            elif type == "BIDDER":
                userbidID = data.get("userbidID")
                if not all([userbidID]):
                    return JsonResponse(
                        {"message": "All fields are required"}, status=400
                    )

                try:
                    userbid = models.User_Bid.objects.get(id=userbidID)
                except models.User_Bid.DoesNotExist:
                    return JsonResponse(
                        {"message": "user bid ID not found"}, status=400
                    )

                postedForSale = userbid.posted_for_sale_id

                expired_bids = models.User_Bid.objects.filter(
                    posted_for_sale_id=postedForSale, status="expired"
                ).exists()
                if expired_bids:
                    return JsonResponse(
                        {"message": "Cannot modify post with expired bids"}, status=403
                    )

                closed_bids = models.User_Bid.objects.filter(
                    posted_for_sale_id=postedForSale, status="closed"
                ).exists()
                if closed_bids:
                    return JsonResponse(
                        {"message": "Cannot modify post with closed bids"}, status=403
                    )

                with transaction.atomic():
                    # userbid.withdraw = True
                    # userbid.save()
                    models.User_Bid.objects.filter(id=userbid.id).update(withdraw=True)
                    return JsonResponse({"message": "Successfully withdrawn the bid","user":user_role.id}, status=200)

            else:
                return JsonResponse(
                    {
                        "message": "type should be SELLER or BIDDER",
                        "user": user_role.id,
                    },
                    status=400,
                )

        except Exception as e:
            return JsonResponse({"message": str(e)}, status=500)
    else:
        return JsonResponse({"message": "Only PUT method is allowed"}, status=405)


# updated_at post for sale table upadate
@csrf_exempt
def ModifyBidAPI(request):
    if request.method == "PUT":
        try:
            data = json.loads(request.body)
            userRoleID = data.get("user")
            per_unit_price = data.get("per_unit_price")
            no_of_units = data.get("no_of_units")
            type = data.get("type")

            if not all([userRoleID, per_unit_price, no_of_units, type]):
                return JsonResponse({"message": "All fields are required"}, status=400)

            try:
                user_role = models.UserRole.objects.get(id=userRoleID)
            except models.UserRole.DoesNotExist:
                return JsonResponse({"message": "User role not found"}, status=400)

            if type == "SELLER":
                buyerID = data.get("buyerID")
                postedForSaleID = data.get("postedForSaleID")

                if not all([buyerID, postedForSaleID]):
                    return JsonResponse(
                        {"message": "All fields are required"}, status=400
                    )

                try:
                    postedForSale = models.Post_for_sale.objects.get(id=postedForSaleID)
                except models.Post_for_sale.DoesNotExist:
                    return JsonResponse(
                        {"message": "postedforsaleID not found"}, status=400
                    )

                try:
                    buyer = models.Buyers.objects.get(id=buyerID)
                except models.Buyers.DoesNotExist:
                    return JsonResponse({"message": "Buyer not found"}, status=400)

                try:
                    buyer_Units = models.Buyer_UnitsTracker.objects.filter(
                        buyer_id=buyer, post_for_saleID=postedForSale
                    ).order_by("id")[:no_of_units]
                except models.Buyer_UnitsTracker.DoesNotExist:
                    return JsonResponse(
                        {
                            "message": "buyer unit does not exits or Not sufficient units for post for sale"
                        },
                        status=400,
                    )

                if buyer_Units.count() < no_of_units:
                    return JsonResponse(
                        {
                            "message": f"Not enough units available for selling , You can bid up to {buyer_Units.count()} units only."
                        },
                        status=400,
                    )

                if postedForSale.type != "Bidding":
                    return JsonResponse(
                        {"message": "Only Biddable invoice can modify"}, status=403
                    )

                if postedForSale.withdrawn == True:
                    return JsonResponse(
                        {"message": "Only non - withdraw invoice can modify"},
                        status=403,
                    )

                active_bids = models.User_Bid.objects.filter(
                    posted_for_sale_id=postedForSale, status="awaiting_acceptance"
                ).exists()
                if active_bids:
                    return JsonResponse(
                        {"message": "Cannot modify post with active bids"}, status=403
                    )

                expired_bids = models.User_Bid.objects.filter(
                    posted_for_sale_id=postedForSale, status="expired"
                ).exists()
                if expired_bids:
                    return JsonResponse(
                        {"message": "Cannot modify post with expired bids"}, status=403
                    )

                with transaction.atomic():
                    if postedForSale.user_id != user_role:
                        return JsonResponse({"message": "chech user id "}, status=400)

                    # postedForSale.per_unit_price = per_unit_price
                    # postedForSale.no_of_units = no_of_units
                    # postedForSale.remaining_units = no_of_units
                    # postedForSale.total_price = per_unit_price * no_of_units
                    # postedForSale.save()
                    models.Post_for_sale.objects.filter(id=postedForSale.id).update(per_unit_price=per_unit_price,no_of_units=no_of_units,remaining_units=no_of_units,total_price=(per_unit_price*no_of_units))
                    return JsonResponse({"message": "Successfully updated the post for sale","user":user_role.id,"postedForSaleID":postedForSale.id}, status=200)

            elif type == "BIDDER":
                userBidID = data.get("userBidID")

                if not all([userBidID]):
                    return JsonResponse(
                        {"message": "userBidID are required"}, status=400
                    )

                try:
                    userBid = models.User_Bid.objects.get(id=userBidID)
                except models.User_Bid.DoesNotExist:
                    return JsonResponse(
                        {"message": "User Bid ID not found"}, status=400
                    )

                postedForSale = userBid.posted_for_sale_id

                if userBid.posted_for_sale_id.no_of_units < no_of_units:
                    return JsonResponse(
                        {
                            "message ",
                            f"You can bid upto {userBid.posted_for_sale_id.no_of_bid}",
                        },
                        status=400,
                    )

                if postedForSale.withdrawn == True:
                    return JsonResponse(
                        {"message": "Only non - withdraw invoice can modify"},
                        status=403,
                    )

                funded_bids = models.User_Bid.objects.filter(
                    posted_for_sale_id=postedForSale, status="closed"
                ).exists()
                if funded_bids:
                    return JsonResponse(
                        {"message": "Cannot modify post with closed bids"}, status=403
                    )

                expired_bids = models.User_Bid.objects.filter(
                    posted_for_sale_id=postedForSale, status="expired"
                ).exists()
                if expired_bids:
                    return JsonResponse(
                        {"message": "Cannot modify post with expired bids"}, status=403
                    )

                with transaction.atomic():
                    # userBid.no_of_units = no_of_units
                    # userBid.per_unit_bid_price = per_unit_price
                    # userBid.updated_at = timezone.now()
                    # userBid.save()
                    models.User_Bid.objects.filter(id=userBid.id).update(no_of_units=no_of_units,per_unit_bid_price=per_unit_price,updated_at=timezone.now())
                    return JsonResponse({"message": "Successfully updated the bid","user":user_role.id,"userBidID":userBid.id}, status=200)
            else :
                return JsonResponse({"message":"type should be SELLER or BIDDER","user":user_role.id},status=400)

        except Exception as e:
            return JsonResponse({"message": str(e)}, status=500)
    else:
        return JsonResponse({"message": "Only PUT method is allowed"}, status=405)


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


@csrf_exempt
def cashFlowAPI(request, invoiceID):
    if request.method == "GET":
        try:
            try:
                invoice = models.Invoices.objects.get(id=invoiceID)
            except models.Invoices.DoesNotExist:
                return JsonResponse({"message": "invoiceID not found"})

            primary_invoice_id = invoice.primary_invoice_id
            print(primary_invoice_id)
            url = "http://backend.ethyx.in/admin-api/payment-schedule-calculator/"
            headers = {
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzIyMzQyNzUwLCJpYXQiOjE3MjIyNTYzNTAsImp0aSI6ImZlMjAwMzM1OTYzNjRmNTRhYjA3ZTE4NWU4ZDI5NWJkIiwidWlkIjoiQVNOV1ROODI4NSJ9.8_yy4cwJGrJ8z2UsRcAYl7Hr3-1xGfIGoY4TFQ3JZng",
                "Content-Type": "application/json",
            }

            payload = {"invoice_product_id": 8}

            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                return JsonResponse({"CashFlow": response.json()}, status=200)
            else:
                return JsonResponse(
                    {"message": response.json()}, status=response.status_code
                )

        except Exception as e:
            return JsonResponse({"message": str(e)}, status=500)
    else:
        return JsonResponse({"message": "Only GET method is allowed"}, status=405)
