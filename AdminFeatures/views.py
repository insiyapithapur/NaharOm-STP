from datetime import datetime
import os
from django.utils import timezone
import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from UserFeatures import models
from AdminFeatures import models as admin_models
from django.utils import timezone
from django.db import transaction
import base64
import time
from django.conf import settings
import hashlib
from django.db.models import Q
import jwt
from datetime import datetime, timedelta
from django.utils.decorators import method_decorator
from django.views import View
from ApiManagement.utils import is_api_enabled

# for rest framework
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
import logging

logger = logging.getLogger(__name__)


# Load invoices data from JSON file
with open(os.path.join(os.path.dirname(__file__), "invoices.json")) as f:
    invoices_data = json.load(f)


def filter_invoice_data(invoice):
    product = invoice.get("product", {})
    return {
        "primary_invoice_id": invoice["id"],
        "buyer_poc_name": invoice["buyer_poc_name"],
        "product_name": product.get("name"),
        "irr": product.get("interest_rate_fixed"),
        "tenure_in_days": product.get("tenure_in_days"),
        "interest_rate": product.get("interest"),
        "xirr": product.get("xirr_in_percentage"),
        "principle_amt": product.get("principle_amt"),
        "expiration_time": timezone.now() + timezone.timedelta(days=product.get("tenure_in_days")),
    }


class TransactionLogAPIView(APIView):
    """
    API endpoint for managing transaction logs.
    """
    
    def get(self, request):
        user_id = request.query_params.get("userId")

        if user_id:
            # Filter transactions for the specific user
            logs = admin_models.TransactionLog.objects.filter(user__id=user_id).values()
        else:
            # Fetch all transactions if no userId is provided
            logs = admin_models.TransactionLog.objects.all().values()

        return Response(list(logs), status=status.HTTP_200_OK)

    def post(self, request):
        try:
            userRoleID = request.data.get("user")
            transaction_type = request.data.get("transaction_type")
            no_of_units = request.data.get("no_of_units")
            per_unit_price = request.data.get("per_unit_price")
            total_price = request.data.get("total_price")
            status_value = request.data.get("status")
            remarks = request.data.get("remarks", "")

            try:
                user_role = models.UserRole.objects.get(id=userRoleID)
            except models.UserRole.DoesNotExist:
                return Response({"message": "User not found"}, status=status.HTTP_400_BAD_REQUEST)

            log_entry = admin_models.TransactionLog.objects.create(
                user=user_role,
                transaction_type=transaction_type,
                no_of_units=no_of_units,
                per_unit_price=per_unit_price,
                total_price=total_price,
                status=status_value,
                remarks=remarks,
            )

            return Response(
                {
                    "message": "Transaction log created successfully",
                    "log_id": log_entry.id,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExtractInvoicesAPIView(APIView):
    """
    API endpoint for extracting invoices with products.
    """
    
    def post(self, request):
        try:
            data = request.data

            if not isinstance(data, list):
                return Response(
                    {"message": "Invalid input format, expected a list of objects"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            filtered_invoices = []

            for company in data:
                invoices = company.get("invoices", [])
                for invoice in invoices:
                    if invoice.get("product") is not None:
                        filtered_invoices.append(invoice)

            return Response({"filtered_invoices": filtered_invoices}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetInvoicesAPIView(APIView):
    """
    API endpoint for retrieving invoices by user.
    """
    
    def get(self, request, user_id, primary_invoice_id=None):
        try:
            if not user_id:
                return Response({"message": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = models.User.objects.get(id=user_id)
            except models.User.DoesNotExist:
                return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            if not user.is_admin:
                return Response(
                    {"message": "For this operation you have to register yourself with admin role"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            if primary_invoice_id:
                invoice_data = next(
                    (inv for inv in invoices_data["filtered_invoices"] if inv["id"] == primary_invoice_id),
                    None,
                )
                if not invoice_data:
                    return Response({"message": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND)
                filtered_invoice_data = filter_invoice_data(invoice_data)
                return Response(filtered_invoice_data, status=status.HTTP_200_OK)
            else:
                filtered_invoices_data = [
                    filter_invoice_data(inv) for inv in invoices_data["filtered_invoices"]
                ]
                return Response(filtered_invoices_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InvoiceMgtAPIView(APIView):
    """
    API endpoint for managing invoices.
    """
    
    def get(self, request, user, primary_invoice_id=None):
        try:
            try:
                user_role = models.UserRole.objects.get(id=user)
            except models.UserRole.DoesNotExist:
                return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            if not user_role.user.is_admin:
                return Response(
                    {"message": "For this operation you have to register yourself with admin role"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            if primary_invoice_id:
                invoice_data = next(
                    (inv for inv in invoices_data["filtered_invoices"] if inv["id"] == primary_invoice_id),
                    None,
                )
                if not invoice_data:
                    return Response({"message": "Invoice not found"}, status=status.HTTP_404_NOT_FOUND)
                filtered_invoice_data = filter_invoice_data(invoice_data)
                return Response(filtered_invoice_data, status=status.HTTP_200_OK)
            else:
                # Get configured invoices
                configured_invoices = models.Configurations.objects.filter(remaining_units__gt=0)
                configured_invoices_data = []
                for configured_invoice in configured_invoices:
                    invoice_data = {
                        "id": configured_invoice.invoice_id.id,
                        "invoice_id": configured_invoice.invoice_id.invoice_id,
                        "primary_invoice_id": configured_invoice.invoice_id.primary_invoice_id,
                        "configured_ID": configured_invoice.id,
                        "product_name": configured_invoice.invoice_id.product_name,
                        "irr": configured_invoice.invoice_id.irr,
                        "tenure_in_days": configured_invoice.invoice_id.tenure_in_days,
                        "interest_rate": configured_invoice.invoice_id.interest,
                        "xirr": configured_invoice.invoice_id.xirr,
                        "expiration_time": configured_invoice.invoice_id.expiration_time,
                        "principle_amt": configured_invoice.principal_price,
                        "per_unit_price": configured_invoice.per_unit_price,
                        "no_of_units": configured_invoice.no_of_units,
                        "user_id": configured_invoice.user_id.id,
                        "remaining_units": configured_invoice.remaining_units,
                        "type": "configured",
                    }
                    configured_invoices_data.append(invoice_data)
                
                # Get existing configured invoice IDs
                check_configured_invoices = models.Configurations.objects.all()
                configured_invoice_ids = {
                    inv.invoice_id.primary_invoice_id for inv in check_configured_invoices
                }
                
                # Get unfractionalized invoices
                unfractionalized_invoices = [
                    filter_invoice_data(inv) for inv in invoices_data["filtered_invoices"]
                ]
                unfractionalized_invoices_data = []

                for unfractionalized_invoice in unfractionalized_invoices:
                    if unfractionalized_invoice["primary_invoice_id"] not in configured_invoice_ids:
                        unfractionalized_data = {
                            "primary_invoice_id": unfractionalized_invoice["primary_invoice_id"],
                            "buyer_poc_name": unfractionalized_invoice["buyer_poc_name"],
                            "product_name": unfractionalized_invoice["product_name"],
                            "irr": unfractionalized_invoice["irr"],
                            "tenure_in_days": unfractionalized_invoice["tenure_in_days"],
                            "interest_rate": unfractionalized_invoice["interest_rate"],
                            "xirr": unfractionalized_invoice["xirr"],
                            "principle_amt": unfractionalized_invoice["principle_amt"],
                            "remaining_amt": unfractionalized_invoice["principle_amt"],
                            "expiration_time": unfractionalized_invoice["expiration_time"],
                            "type": "unfractionalized",
                        }
                        unfractionalized_invoices_data.append(unfractionalized_data)

                # Get fractionalized invoices
                fractionalized_invoice_data = models.Post_for_sale.objects.filter(
                    configurationID__isnull=False, is_admin=True
                )
                response_data = []
                for post in fractionalized_invoice_data:
                    invoice = post.invoice_id
                    configuration = post.configurationID
                    post_data = {
                        "id": invoice.id,
                        "invoice_id": invoice.invoice_id,
                        "primary_invoice_id": invoice.primary_invoice_id,
                        "post_for_saleID": post.id,
                        "configurationID": configuration.id,
                        "product_name": invoice.product_name,
                        "interest": invoice.interest,
                        "xirr": invoice.xirr,
                        "irr": invoice.irr,
                        "tenure_in_days": invoice.tenure_in_days,
                        "expiration_time": invoice.expiration_time,
                        "expired": invoice.expired,
                        "no_of_units": post.no_of_units,
                        "per_unit_price": post.per_unit_price,
                        "total_price": post.total_price,
                        "userID": post.user_id.id,
                        "remaining_units": post.remaining_units,
                        "withdrawn": post.withdrawn,
                        "post_time": post.post_time,
                        "post_date": post.post_date,
                        "from_date": post.from_date,
                        "to_date": post.to_date,
                        "type": "fractionalized",
                    }
                    response_data.append(post_data)

                # Combine all data
                all_data = response_data + configured_invoices_data + unfractionalized_invoices_data
                return Response({"user": user_role.id, "data": all_data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConfigurationAPIView(APIView):
    """
    API endpoint for configuring invoices.
    """
    
    def post(self, request):
        try:
            user = request.data.get("user")
            primary_invoice_id = request.data.get("primary_invoice_id")
            no_of_units = request.data.get("no_of_units")
            per_unit_price = request.data.get("per_unit_price")

            try:
                user_role = models.UserRole.objects.get(id=user)
            except models.UserRole.DoesNotExist:
                return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            if not user_role.user.is_admin:
                return Response(
                    {
                        "message": "For this operation you have to register yourself with admin role",
                        "user": user_role.id,
                    },
                    status=status.HTTP_403_FORBIDDEN
                )

            # Get invoice data from the invoices_data structure
            invoice_data = next(
                (
                    inv
                    for inv in invoices_data["filtered_invoices"]
                    if inv["id"] == primary_invoice_id
                ),
                None,
            )
            
            if not invoice_data or not invoice_data.get("product"):
                return Response(
                    {
                        "message": "Invoice data not found or product is null",
                        "user": user_role.id,
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
                
            with transaction.atomic():
                try:
                    invoice = models.Invoices.objects.get(primary_invoice_id=primary_invoice_id)
                    return Response(
                        {
                            "message": "Configuration of this invoice is already done",
                            "invoiceID": invoice.id,
                            "user": user_role.id,
                        },
                        status=status.HTTP_200_OK
                    )
                except models.Invoices.DoesNotExist:
                    # Extract product data and create invoice
                    product_data = invoice_data["product"]
                    product_name = product_data["name"]
                    principal_price = product_data["principle_amt"]
                    interest = product_data["interest"]
                    xirr = product_data["xirr_in_percentage"]
                    irr = product_data["interest_rate_fixed"]
                    tenure_in_days = product_data["tenure_in_days"]
                    expiration_time = timezone.now() + timezone.timedelta(days=tenure_in_days)

                    invoice = models.Invoices.objects.create(
                        primary_invoice_id=primary_invoice_id,
                        product_name=product_name,
                        principal_price=principal_price,
                        interest=interest,
                        xirr=xirr,
                        irr=irr,
                        tenure_in_days=tenure_in_days,
                        expiration_time=expiration_time,
                        expired=False,
                        created_At=timezone.now(),
                    )

                    # Create configuration
                    configure = models.Configurations.objects.create(
                        principal_price=principal_price,
                        per_unit_price=per_unit_price,
                        no_of_units=no_of_units,
                        invoice_id=invoice,
                        user_id=user_role,
                        remaining_units=no_of_units,
                    )

                    # Create fractional units
                    for _ in range(no_of_units):
                        models.FractionalUnits.objects.create(
                            invoice=invoice,
                            current_owner=None,
                            posted_for_sale=False,
                            configurationID=configure,
                            created_At=timezone.now(),
                        )
                        
                    return Response(
                        {
                            "message": "Successfully configured",
                            "invoice": invoice.id,
                            "configured": configure.id,
                            "user": user_role.id,
                        },
                        status=status.HTTP_200_OK
                    )
                    
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PostInvoiceAPIView(APIView):
    """
    API endpoint for posting invoices for sale.
    """
    
    def post(self, request):
        try:
            user_id = request.data.get("user")
            no_of_units = request.data.get("no_of_units")
            per_unit_price = request.data.get("per_unit_price")
            from_date = request.data.get("from_date")
            to_date = request.data.get("to_date")
            total_price = no_of_units * per_unit_price
            configureID = request.data.get("configureID")

            try:
                user_role = models.UserRole.objects.get(id=user_id)
            except models.UserRole.DoesNotExist:
                return Response({"message": "user does not exist"}, status=status.HTTP_400_BAD_REQUEST)

            if not user_role.user.is_admin:
                return Response(
                    {
                        "message": "For this operation you have to be admin",
                        "user": user_role.id,
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():
                try:
                    configure = models.Configurations.objects.get(id=configureID)
                    if configure.remaining_units < no_of_units:
                        return Response(
                            {
                                "message": "Not sufficient units for selling",
                                "user": user_role.id,
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )
                        
                    # Create post for sale
                    post_for_sale = models.Post_for_sale.objects.create(
                        no_of_units=no_of_units,
                        per_unit_price=per_unit_price,
                        user_id=user_role,
                        invoice_id=configure.invoice_id,
                        total_price=total_price,
                        remaining_units=no_of_units,
                        withdrawn=False,
                        post_time=timezone.now().time(),
                        post_date=timezone.now().date(),
                        from_date=from_date,
                        to_date=to_date,
                        post_dateTime=timezone.now(),
                        configurationID=configure,
                        is_admin=user_role.user.is_admin,
                    )
                    
                    # Get fractional units
                    fractional_units = models.FractionalUnits.objects.filter(
                        posted_for_sale=False,
                        invoice=configure.invoice_id,
                        configurationID=configure,
                        current_owner__isnull=True,
                    )[:no_of_units]
                    
                    if fractional_units.count() < no_of_units:
                        return Response(
                            {"message": "Not enough fractional units available"},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                    # Process each unit
                    for unit in fractional_units:
                        models.Post_For_Sale_UnitTracker.objects.create(
                            unitID=unit, post_for_saleID=post_for_sale, sellersID=None
                        )
                        models.FractionalUnits.objects.filter(id=unit.id).update(posted_for_sale=True)
                        
                    # Update configuration
                    configure.remaining_units -= no_of_units
                    configure.save()
                    
                    return Response(
                        {
                            "message": "Successfully posted for sale",
                            "posted_for_saleID": post_for_sale.id,
                            "invoice_id": post_for_sale.invoice_id.id,
                            "user": user_role.id,
                        },
                        status=status.HTTP_201_CREATED
                    )
                    
                except models.Configurations.DoesNotExist:
                    return Response(
                        {
                            "message": "Configuration does not exist",
                            "user": user_role.id,
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                    
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserManagementAPIView(APIView):
    """
    API endpoint for user management.
    """
    
    def get(self, request, user):
        messages = []
        try:
            try:
                user_is_admin = models.UserRole.objects.get(id=user)
            except models.UserRole.DoesNotExist:
                return Response(
                    {"message": "User not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            if not user_is_admin.user.is_admin and not user_is_admin.user.is_superadmin:
                messages.append("For this operation you should be admin or superadmin")
                return Response(
                    {"messages": messages, "data": None}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            user_roles = models.UserRole.objects.all()
            all_user_details = []

            for user_role in user_roles:
                try:
                    user_details = {
                        "id": user_role.id,
                        "user": user_role.user_role_id,
                        "user_role": user_role.role,
                        "email": user_role.user.email,
                        "mobile": user_role.user.mobile,
                        "date_of_joining": user_role.user.created_at,
                    }

                    # Handle Company details
                    if user_role.role == "Company":
                        try:
                            company_details = models.CompanyDetails.objects.get(user_role=user_role)
                            user_details["company_name"] = company_details.company_name
                        except models.CompanyDetails.DoesNotExist:
                            user_details["company_name"] = None
                            messages.append(f"Company details not found for user {user_role.id}")

                    # Handle Individual details
                    elif user_role.role == "Individual":
                        try:
                            individual_details = models.IndividualDetails.objects.get(user_role=user_role)
                            user_details.update({
                                "first_name": individual_details.first_name,
                                "last_name": individual_details.last_name,
                            })
                        except models.IndividualDetails.DoesNotExist:
                            user_details.update({
                                "first_name": None,
                                "last_name": None,
                            })
                            messages.append(f"Individual details not found for user {user_role.id}")

                    # Handle PAN card details
                    try:
                        pan_card = models.PanCardNos.objects.get(user_role=user_role)
                        user_details["pan_card_no"] = pan_card.pan_card_no
                    except models.PanCardNos.DoesNotExist:
                        user_details["pan_card_no"] = None
                        messages.append(f"PAN card details not found for user {user_role.id}")

                    user_details["is_admin"] = user_role.user.is_admin
                    user_details["is_superadmin"] = user_role.user.is_superadmin

                    all_user_details.append(user_details)

                except models.UserRole.DoesNotExist:
                    messages.append(f"UserRole does not exist for user {user_role.id}")
                except Exception as e:
                    messages.append(str(e))

            return Response(
                {"messages": messages, "data": all_user_details},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            messages.append(str(e))
            return Response(
                {"messages": messages, "data": None}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UsersLedgerAPIView(APIView):
    """
    API endpoint for retrieving users' ledger information.
    """
    
    def get(self, request, user):
        try:
            try:
                user_is_admin = models.UserRole.objects.get(id=user)
            except models.UserRole.DoesNotExist:
                return Response(
                    {"message": "User not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            if not user_is_admin.user.is_admin and not user_is_admin.user.is_superadmin:
                return Response(
                    {"message": "For this operation you should be admin or superadmin"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Get all non-admin users
            user_roles = models.UserRole.objects.exclude(
                Q(user__is_admin=True) | Q(user__is_superadmin=True)
            )

            response_data = []

            for user_role in user_roles:
                user_data = {
                    "user": user_role.id,
                    "role": user_role.role,
                    "mobile": user_role.user.mobile,
                    "email": user_role.user.email,
                    "bank_Accounts": [],
                    "wallet_balance": None,
                    "wallet_transaction": [],
                }

                try:
                    # Get bank accounts
                    bankAccs = models.BankAccountDetails.objects.filter(user_role=user_role)
                    user_data["bank_Accounts"] = [
                        {
                            "user": user_role.id,
                            "bankAcc_ID": bankAcc.id,
                            "account_number": bankAcc.account_number,
                            "ifc_code": bankAcc.ifc_code,
                            "account_type": bankAcc.account_type,
                        }
                        for bankAcc in bankAccs
                    ]

                    # Get wallet and transactions
                    wallet = models.Wallet.objects.get(user_role=user_role)
                    user_data["wallet_balance"] = wallet.OutstandingBalance
                    user_data["primary_bankAcc_ID"] = wallet.primary_bankID.id
                    
                    wallet_transactions = models.WalletTransaction.objects.filter(wallet=wallet)
                    user_data["wallet_transaction"] = [
                        {
                            "user": wallet_transaction.wallet.primary_bankID.user_role.id,
                            "walletID": wallet_transaction.wallet.id,
                            "transaction_id": wallet_transaction.transaction_id,
                            "type": wallet_transaction.type,
                            "creditedAmount": wallet_transaction.creditedAmount,
                            "debitedAmount": wallet_transaction.debitedAmount,
                            "status": wallet_transaction.status,
                            "source": wallet_transaction.source,
                            "purpose": wallet_transaction.purpose,
                            "from_bank_acc": (
                                wallet_transaction.from_bank_acc.account_number
                                if wallet_transaction.from_bank_acc
                                else None
                            ),
                            "from_user": (
                                wallet_transaction.from_bank_acc.user_role.id
                                if wallet_transaction.from_bank_acc
                                else None
                            ),
                            "to_bank_acc": (
                                wallet_transaction.to_bank_acc.account_number
                                if wallet_transaction.to_bank_acc
                                else None
                            ),
                            "to_user": (
                                wallet_transaction.to_bank_acc.user_role.id
                                if wallet_transaction.to_bank_acc
                                else None
                            ),
                            "invoice": (
                                wallet_transaction.invoice.invoice_id
                                if wallet_transaction.invoice
                                else None
                            ),
                            "time_date": wallet_transaction.time_date,
                        }
                        for wallet_transaction in wallet_transactions
                    ]

                except (models.BankAccountDetails.DoesNotExist, models.Wallet.DoesNotExist, 
                       models.WalletTransaction.DoesNotExist):
                    # Continue with partial data if some information is missing
                    pass

                response_data.append(user_data)

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SalesPurchasedReportAPIView(APIView):
    """
    API endpoint for retrieving sales and purchase reports.
    """
    
    def get(self, request, user):
        try:
            if not user:
                return Response(
                    {"message": "user ID is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                user_role = models.UserRole.objects.get(id=user)
            except models.UserRole.DoesNotExist:
                return Response(
                    {"message": "User not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            if not user_role.user.is_admin:
                return Response(
                    {"message": "For this operation you have to register yourself with admin role"},
                    status=status.HTTP_403_FORBIDDEN
                )

            with transaction.atomic():
                try:
                    sales_purchase_reports = models.SalePurchaseReport.objects.all()
                    report_list = []
                    
                    for report in sales_purchase_reports:
                        # Get seller information
                        if report.seller_ID.role == "Individual":
                            try:
                                seller_profile = models.IndividualDetails.objects.get(
                                    user_role=report.seller_ID
                                )
                                Seller_Name = seller_profile.first_name
                            except models.IndividualDetails.DoesNotExist:
                                Seller_Name = None
                        else:
                            try:
                                seller_profile = models.CompanyDetails.objects.get(
                                    user_role=report.seller_ID
                                )
                                Seller_Name = seller_profile.company_name
                            except models.CompanyDetails.DoesNotExist:
                                Seller_Name = None

                        # Get buyer information
                        if report.buyerID_ID.role == "Individual":
                            try:
                                buyer_profile = models.IndividualDetails.objects.get(
                                    user_role=report.buyerID_ID
                                )
                                Buyer_Name = buyer_profile.first_name
                            except models.IndividualDetails.DoesNotExist:
                                Buyer_Name = None
                        else:
                            try:
                                buyer_profile = models.CompanyDetails.objects.get(
                                    user_role=report.buyerID_ID
                                )
                                Buyer_Name = buyer_profile.company_name
                            except models.CompanyDetails.DoesNotExist:
                                Buyer_Name = None

                        # Get PAN card information
                        try:
                            seller_pancard = models.PanCardNos.objects.get(
                                user_role=report.seller_ID
                            )
                            Seller_PAN = seller_pancard.pan_card_no
                        except models.PanCardNos.DoesNotExist:
                            Seller_PAN = None

                        try:
                            buyer_pancard = models.PanCardNos.objects.get(
                                user_role=report.buyerID_ID
                            )
                            Buyer_PAN = buyer_pancard.pan_card_no
                        except models.PanCardNos.DoesNotExist:
                            # Fix potential bug: use seller_profile.first_name only if seller_profile exists
                            Buyer_PAN = getattr(seller_profile, 'first_name', None) if 'seller_profile' in locals() else None

                        # Create report data
                        report_data = {
                            "id": report.id,
                            "invoiceID": report.invoiceID.invoice_id,
                            "unitID": report.unitID.fractional_unit_id,
                            "Listing_Date": report.ListingDate,
                            "Seller_ID": report.seller_ID.id,
                            "Seller_Name": Seller_Name,
                            "Seller_PAN": Seller_PAN,
                            "Sale_Buy_Date": report.Sale_Buy_Date,
                            "Sale_Buy_per_unit_price": report.Sale_Buy_per_unit_price,
                            "Buyer_ID": report.buyerID_ID.id,
                            "Buyer_Name": Buyer_Name,
                            "Buyer_PAN": Buyer_PAN,
                            "transfer_date": "2024-08-01",
                            "no_of_days_units_held": report.no_of_days_units_held,
                            "interest_due_to_seller": report.interest_due_to_seller,
                            "TDS_deducted": report.TDS_deducted,
                            "IRR": report.IRR,
                        }
                        report_list.append(report_data)
                        
                    return Response(
                        {"sales_purchase_reports": report_list, "user": user_role.id},
                        status=status.HTTP_200_OK
                    )

                except models.SalePurchaseReport.DoesNotExist:
                    return Response(
                        {"message": "SalePurchaseReport not found"}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
                    
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TdsReportAPIView(APIView):
    """
    API endpoint for retrieving TDS reports.
    """
    
    def get(self, request, user):
        try:
            if not user:
                return Response(
                    {"message": "user ID is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                user_role = models.UserRole.objects.get(id=user)
            except models.UserRole.DoesNotExist:
                return Response(
                    {"message": "User not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            if not user_role.user.is_admin:
                return Response(
                    {"message": "For this operation you have to register yourself with admin role"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Sample TDS report data (static for now)
            report_data = {
                "id": 1,
                "PurchaserID": 1,
                "Name_of_the_Purchaser_of_Units": "NAME",
                "PAN_No": "BUYER",
                "Name_of_the_Co": "None",
                "PAN_No_of_the_Co": "None",
                "TAN_No_of_the_Co": "None",
                "Value_of_Per_Unit": 10000,
                "Units_Purchased": 2,
                "Date_of_Purchase": "2024-08-01",
                "Interest_date ": "2024-08-01",
                "ROI": 3.7,
                "Sale_price_per_unit": 10000,
                "Sell_Date": "2024-08-01",
                "Total_No_of_days_Units_were_held": 84,
                "Total_Amount_credited": 10000,
                "Expected_Interest": 6.78,
                "Actual_Interest_credited": 6.73,
                "Date_of_Payment": "2024-08-01",
                "Nature_of_Payment": "MONTHLY",
                "Quarter": "None",
                "TDS": 20,
                "Reciept_No_of_TDS": 21,
                "CIN details": "None",
            }
            
            return Response(
                {"sales_purchase_reports": "nksjxnk", "user": user_role.id},
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BidReportAPIView(APIView):
    """
    API endpoint for retrieving bid reports.
    """
    
    def get(self, request, user):
        try:
            if not user:
                return Response(
                    {"message": "user ID is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                user_role = models.UserRole.objects.get(id=user)
            except models.UserRole.DoesNotExist:
                return Response(
                    {"message": "User not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            if not user_role.user.is_admin:
                return Response(
                    {"message": "For this operation you have to register yourself with admin role"},
                    status=status.HTTP_403_FORBIDDEN
                )

            with transaction.atomic():
                bids_report = models.BidReport.objects.all()
                report_list = []
                
                for report in bids_report:
                    # Get seller information
                    if report.post_for_saleID.user_id.role == "Individual":
                        try:
                            seller_profile = models.IndividualDetails.objects.get(
                                user_role=report.post_for_saleID.user_id
                            )
                            Seller_Name = seller_profile.first_name
                        except models.IndividualDetails.DoesNotExist:
                            Seller_Name = None
                    else:
                        try:
                            seller_profile = models.CompanyDetails.objects.get(
                                user_role=report.post_for_saleID.user_id
                            )
                            Seller_Name = seller_profile.company_name
                        except models.CompanyDetails.DoesNotExist:
                            Seller_Name = None

                    # Get buyer information
                    if report.user_BidID.user_id.role == "Individual":
                        try:
                            buyer_profile = models.IndividualDetails.objects.get(
                                user_role=report.user_BidID.user_id
                            )
                            Buyer_Name = buyer_profile.first_name
                        except models.IndividualDetails.DoesNotExist:
                            Buyer_Name = None
                    else:
                        try:
                            buyer_profile = models.CompanyDetails.objects.get(
                                user_role=report.user_BidID.user_id
                            )
                            Buyer_Name = buyer_profile.company_name
                        except models.CompanyDetails.DoesNotExist:
                            Buyer_Name = None

                    # Get PAN card information
                    try:
                        seller_pancard = models.PanCardNos.objects.get(
                            user_role=report.post_for_saleID.user_id
                        )
                        Seller_PAN = seller_pancard.pan_card_no
                    except models.PanCardNos.DoesNotExist:
                        Seller_PAN = None

                    try:
                        buyer_pancard = models.PanCardNos.objects.get(
                            user_role=report.user_BidID.user_id
                        )
                        Buyer_PAN = buyer_pancard.pan_card_no
                    except models.PanCardNos.DoesNotExist:
                        # Fix potential bug: use seller_profile.first_name only if seller_profile exists
                        Buyer_PAN = getattr(seller_profile, 'first_name', None) if 'seller_profile' in locals() else None

                    # Create report data
                    report_data = {
                        "id": report.id,
                        "PurchaserID": report.user_BidID.user_id.user_role_id,
                        "FractionalID": report.unitID.fractional_unit_id,
                        "Listing_Date": report.ListingDate,
                        "Seller_Name": Seller_Name,
                        "Seller_PAN": Seller_PAN,
                        "Seller_ID": report.post_for_saleID.user_id.user_role_id,
                        "Open_to_Bid_Date": report.post_for_saleID.post_dateTime,
                        "Bidding_base_price": report.post_for_saleID.per_unit_price,
                        "Buyer_Bid": report.user_BidID.per_unit_bid_price,
                        "Buyer_Bid_date": report.user_BidID.datetime,
                        "Buyer_ID": report.user_BidID.user_id.user_role_id,
                        "Buyer_Name": Buyer_Name,
                        "Buyer_PAN": Buyer_PAN,
                    }
                    report_list.append(report_data)
                    
                return Response(
                    {"Bid_Report": report_list, "user": user_role.id}, 
                    status=status.HTTP_200_OK
                )
                
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TradingActivityReportAPIView(APIView):
    """
    API endpoint for retrieving trading activity reports.
    """
    
    def get(self, request, user):
        try:
            if not user:
                return Response(
                    {"message": "user ID is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                user_role = models.UserRole.objects.get(id=user)
            except models.UserRole.DoesNotExist:
                return Response(
                    {"message": "User not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            if not user_role.user.is_admin:
                return Response(
                    {"message": "For this operation you have to register yourself with admin role"},
                    status=status.HTTP_403_FORBIDDEN
                )

            with transaction.atomic():
                # Get active bids
                active_bids = models.Post_for_sale.objects.filter(
                    type="Bidding", open_for_bid=True, withdrawn=False, sold=False
                )
                report_list = []
                
                for active_bid in active_bids:
                    # Get seller information
                    if active_bid.user_id.role == "Individual":
                        try:
                            seller_profile = models.IndividualDetails.objects.get(
                                user_role=active_bid.user_id
                            )
                            Seller_Name = seller_profile.first_name
                        except models.IndividualDetails.DoesNotExist:
                            Seller_Name = None
                    else:
                        try:
                            seller_profile = models.CompanyDetails.objects.get(
                                user_role=active_bid.user_id
                            )
                            Seller_Name = seller_profile.company_name
                        except models.CompanyDetails.DoesNotExist:
                            Seller_Name = None
                            
                    # Get user bids for this active bid
                    user_bids = models.User_Bid.objects.filter(
                        posted_for_sale_id=active_bid.id
                    )
                    bids_history = []
                    
                    for bid in user_bids:
                        buyer_name = None
                        if bid.user_id.role == "Individual":
                            try:
                                buyer_profile = models.IndividualDetails.objects.get(
                                    user_role=bid.user_id
                                )
                                buyer_name = buyer_profile.first_name
                            except models.IndividualDetails.DoesNotExist:
                                buyer_name = None
                        else:
                            try:
                                buyer_profile = models.CompanyDetails.objects.get(
                                    user_role=bid.user_id
                                )
                                buyer_name = buyer_profile.company_name
                            except models.CompanyDetails.DoesNotExist:
                                buyer_name = None

                        # Create bid data
                        bid_data = {
                            "PurchaserID": bid.user_id.user_role_id,
                            "Bid_withdrawn": bid.withdraw,
                            "Bid_modified": bid.updated_at,
                            "Date_of_Bid": bid.datetime,
                            "Name_of_Buyer": buyer_name,
                            "Per_unit_bid_price": bid.per_unit_bid_price,
                            "Number_of_units": bid.no_of_units,
                            "Status": bid.status,
                        }
                        bids_history.append(bid_data)
                        
                    # Create report data
                    report_data = {
                        "id": active_bid.id,
                        "Fractional_Ids": active_bid.no_of_units,
                        "Name_of_Seller": Seller_Name,
                        "Listed_per_unit_price": active_bid.per_unit_price,
                        "Bids_made": active_bid.no_of_bid,
                        "Bids_history": bids_history,
                    }
                    report_list.append(report_data)
                    
                return Response(
                    {"Trading_Activity_Report": report_list, "user": user_role.id},
                    status=status.HTTP_200_OK
                )
                
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class APIMgtReportAPIView(APIView):
    """
    API endpoint for retrieving API management reports.
    """
    
    def get(self, request, user):
        try:
            if not user:
                return Response(
                    {"message": "user ID is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                user_role = models.UserRole.objects.get(id=user)
            except models.UserRole.DoesNotExist:
                return Response(
                    {"message": "User not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            if not user_role.user.is_admin:
                return Response(
                    {"message": "For this operation you have to register yourself with admin role"},
                    status=status.HTTP_403_FORBIDDEN
                )

            try:
                with open("APIMgtReport.json", "r") as file:
                    APIMgtReport_data = json.load(file)
            except FileNotFoundError:
                return Response(
                    {"message": "APIMgt Report file not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
                
            return Response(APIMgtReport_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def generate_token(admin_id, user_role_id):
    timestamp = int(time.time())
    token = f"{admin_id}:{user_role_id}:{timestamp}"
    signature = hashlib.sha256(f"{token}:{settings.SECRET_KEY}".encode()).hexdigest()
    token_with_signature = f"{token}:{signature}"
    encoded_token = base64.urlsafe_b64encode(token_with_signature.encode()).decode()
    return encoded_token


def decode_token(token):
    try:
        decoded_token = base64.urlsafe_b64decode(token.encode()).decode()
        parts = decoded_token.split(":")
        if len(parts) != 4:
            return None

        admin_id, user_role_id, timestamp, received_signature = parts
        token_without_signature = f"{admin_id}:{user_role_id}:{timestamp}"
        expected_signature = hashlib.sha256(
            f"{token_without_signature}:{settings.SECRET_KEY}".encode()
        ).hexdigest()

        if received_signature != expected_signature:
            return "token is invalid"

        return admin_id, user_role_id, int(timestamp)
    except Exception as e:
        return "failed to decode the token"


class GenerateTokenAPIView(APIView):
    """
    API endpoint for generating authentication tokens for admin users.
    """
    
    def get(self, request, admin_id, user_role_id):
        try:
            # Verify admin user exists and is a superadmin
            try:
                admin = models.User.objects.get(id=admin_id, is_superadmin=True)
            except models.User.DoesNotExist:
                return Response(
                    {"message": "Admin not found or not authorized"}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            # Verify user role exists
            try:
                user = models.UserRole.objects.get(id=user_role_id)
            except models.UserRole.DoesNotExist:
                return Response(
                    {"message": "User not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            # Generate token
            token = generate_token(admin_id, user_role_id)
            return Response({"token": token}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"message": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserImpersonateAPIView(APIView):
    """
    API endpoint for user impersonation by admin users.
    """
    
    def get(self, request, admin_id, user_role_id):
        try:
            # Verify admin user exists and is a superadmin
            try:
                admin = models.User.objects.get(id=admin_id, is_superadmin=True)
            except models.User.DoesNotExist:
                return Response(
                    {"message": "Admin not found or not authorized"}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            # Get user role and user
            try:
                user_role = models.UserRole.objects.get(id=user_role_id)
                user = user_role.user
            except models.UserRole.DoesNotExist:
                return Response(
                    {"message": "User not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check if bank details exist
            is_BankDetailsExists = models.BankAccountDetails.objects.filter(
                user_role=user_role
            ).exists()

            # Determine user role
            if user.is_superadmin:
                role = "superadmin"
            elif user.is_admin:
                role = "admin"
            else:
                role = "user"

            # Create JWT payload
            payload = {
                "user_id": user_role.id,
                "user_email": user.email,
                "role": role,
                "is_BankDetailsExists": is_BankDetailsExists,
                "exp": int((datetime.utcnow() + timedelta(hours=24)).timestamp()),
            }

            # Generate JWT token
            new_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
            response_data = {"token": new_token}

            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"message": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

