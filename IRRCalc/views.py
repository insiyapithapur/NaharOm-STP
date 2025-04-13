import datetime
from django.shortcuts import render
from django.http import JsonResponse
from .Balloon_Interest_Only import (
    calculate_BallonInterestOnlyBuyer_price_to_XIRR,
    calculate_BalloonInterestOnlySeller_XIRR_to_price,
    calculate_BalloonInterestOnlySeller_price_to_XIRR,
)
from .fixed_price import (
    calculate_Fixedbuyer_price_to_XIRR,
    calculate_FixedSeller_price_to_XIRR,
    calculate_FixedSeller_XIRR_to_price,
)
from .Declining_Principal import (
    calculate_DecliningBuyer_price_to_XIRR,
    calculate_DecliningSeller_price_to_XIRR,
    calculate_DecliningSeller_XIRR_to_price,
)
from .Balloon_Loan_Principal import (
    calculate_BaloonPrincipalBuyer_price_to_XIRR,
    calculate_BalloonPrinipalSeller_price_to_XIRR,
    calculate_BalloonPrincipalSeller_XIRR_to_price,
)
import json
import numpy_financial as npf
from django.views.decorators.csrf import csrf_exempt


# for rest framework
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from .serializers import *

import logging

logger = logging.getLogger(__name__)

# integrate with primary platform and fetch required input params from it


class FixedPriceIRRAPIView(APIView):
    """
    API endpoint for calculating Fixed Price IRR.
    """
    
    def post(self, request):
        try:
            data = request.data
            type = data.get("type", "").upper()
            loan_amount = data.get("loan_amount")
            num_fractions = data.get("num_fractions")
            fractional_unit_value = data.get("fractional_unit_value")
            annual_interest_rate = data.get("annual_interest_rate")
            loan_period_years = data.get("loan_period_years")
            units_bought = data.get("units_bought")
            disbursed_date = datetime.date(2024, 4, 1)
            first_payment_date = datetime.date(2024, 5, 1)
            payment_frequency = data.get("payment_frequency")
            total_installments = data.get("total_installments")

            if type == "BUYER":
                # Calculate for buyer
                dates, amounts, xirr_value = calculate_Fixedbuyer_price_to_XIRR(
                    fractional_unit_value,
                    loan_amount,
                    num_fractions,
                    annual_interest_rate,
                    total_installments,
                    units_bought,
                    loan_period_years,
                    disbursed_date,
                    first_payment_date,
                    payment_frequency,
                )
                
                # Format payment schedule
                payments = [
                    {
                        "payment_number": i,
                        "date": dates[i].strftime("%Y-%m-%d"),
                        "amount": f"{amounts[i]:.2f}",
                    }
                    for i in range(1, len(dates))
                ]

                # Prepare response
                response_data = {
                    "XIRR": f"{xirr_value * 100:.2f}%",
                    "investment_amount": f"{abs(amounts[0]):.2f}",
                    "payments": payments,
                }
                return Response(response_data, status=status.HTTP_200_OK)

            elif type == "SELLER":
                target_xirr = data.get("target_xirr")
                additional_payment = data.get("additional_payment")
                end_date = datetime.date(2024, 8, 18)
                
                if target_xirr:
                    # Calculate price for target XIRR
                    investment_amount = fractional_unit_value * units_bought
                    result = calculate_FixedSeller_XIRR_to_price(
                        fractional_unit_value,
                        loan_amount,
                        num_fractions,
                        annual_interest_rate,
                        units_bought,
                        loan_period_years,
                        disbursed_date,
                        first_payment_date,
                        payment_frequency,
                        end_date,
                        target_xirr,
                    )
                    
                    response_data = {
                        "verified_target_xirr": result["verified_target_xirr"],
                        "difference_from_target": result["difference_from_target"],
                        "cashflow_details": result["cashflow_details"],
                        "sale_price": result["sale_price"],
                    }
                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    # Calculate XIRR for fixed price
                    # Case: Buying 3 units
                    units_bought = 3
                    dates, amounts, xirr_value = calculate_FixedSeller_price_to_XIRR(
                        fractional_unit_value,
                        loan_amount,
                        num_fractions,
                        annual_interest_rate,
                        units_bought,
                        loan_period_years,
                        disbursed_date,
                        first_payment_date,
                        payment_frequency,
                        additional_payment,
                        end_date,
                    )
                    
                    # Format payment schedule
                    payments = [
                        {
                            "payment_number": i,
                            "date": dates[i].strftime("%Y-%m-%d"),
                            "amount": f"{amounts[i]:.2f}",
                        }
                        for i in range(1, len(dates))
                    ]
                    
                    response_data = {
                        "investment_amount": f"{abs(amounts[0]):.2f}",
                        "payments": payments,
                        "XIRR": f"{xirr_value * 100:.2f}%",
                    }
                    return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response({"message": "type is invalid"}, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DecliningPrincipalAPIView(APIView):
    """
    API endpoint for calculating Declining Principal.
    """
    
    def post(self, request):
        try:
            data = request.data
            type = data.get("type").upper()
            loan_amount = data.get("loan_amount")
            num_fractions = data.get("num_fractions")
            fractional_unit_value = data.get("fractional_unit_value")
            annual_interest_rate = data.get("annual_interest_rate")
            total_installments = data.get("total_installments")
            loan_period_years = data.get("loan_period_years")
            units_bought = data.get("units_bought")
            payment_frequency = data.get("payment_frequency").upper()
            monthly_payment = data.get("monthly_payment")
            disbursed_date = datetime.date(2024, 4, 1)
            first_payment_date = datetime.date(2024, 5, 1)
            additional_payment = data.get("additional_payment")
            end_date = datetime.date(2024, 8, 18)

            if type == "BUYER":
                # Calculate for buyer
                dates, amounts, xirr_value = calculate_DecliningBuyer_price_to_XIRR(
                    fractional_unit_value,
                    loan_amount,
                    num_fractions,
                    annual_interest_rate,
                    units_bought,
                    loan_period_years,
                    disbursed_date,
                    first_payment_date,
                    payment_frequency,
                    additional_payment,
                    end_date,
                    monthly_payment,
                )
                
                # Format response
                response_data = {
                    "investment_amount": f"{abs(amounts[0]):.2f}",
                    "payments": [
                        {
                            "payment_number": i,
                            "date": dates[i].strftime("%Y-%m-%d"),
                            "amount": f"{amounts[i]:.2f}",
                        }
                        for i in range(1, len(dates))
                    ],
                    "xirr": f"{xirr_value * 100:.2f}%",
                }
                return Response(response_data, status=status.HTTP_200_OK)

            elif type == "SELLER":
                target_xirr = data.get("target_xirr")
                
                if target_xirr:
                    # Calculate price for target XIRR
                    result = calculate_DecliningSeller_XIRR_to_price(
                        fractional_unit_value,
                        loan_amount,
                        num_fractions,
                        annual_interest_rate,
                        units_bought,
                        loan_period_years,
                        disbursed_date,
                        first_payment_date,
                        payment_frequency,
                        end_date,
                        target_xirr,
                        monthly_payment,
                    )

                    response_data = {
                        "verified_target_xirr": result["verified_target_xirr"],
                        "difference_from_target": result["difference_from_target"],
                        "cashflow_details": result["cashflow_details"],
                        "sale_price": result["sale_price"],
                    }
                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    # Calculate XIRR for fixed price
                    dates, amounts, xirr_value = calculate_DecliningSeller_price_to_XIRR(
                        fractional_unit_value,
                        loan_amount,
                        num_fractions,
                        annual_interest_rate,
                        units_bought,
                        loan_period_years,
                        disbursed_date,
                        first_payment_date,
                        payment_frequency,
                        additional_payment,
                        end_date,
                        monthly_payment,
                    )

                    # Format response
                    response_data = {
                        "investment_amount": f"{abs(amounts[0]):.2f}",
                        "payments": [
                            {
                                "payment_number": i,
                                "date": dates[i].strftime("%Y-%m-%d"),
                                "amount": f"{amounts[i]:.2f}",
                            }
                            for i in range(1, len(dates))
                        ],
                        "xirr": f"{xirr_value * 100:.2f}%",
                    }
                    return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response({"message": "type is invalid"}, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def calculate_monthly_total_payment(annual_interest_rate, nper, pv):
    print("annual_interest_rate ncd", annual_interest_rate)
    monthly_interest_rate = (1 + annual_interest_rate) ** (1 / 12) - 1
    print("monthly_interest_rate ", monthly_interest_rate)
    print("nper ", nper)
    print("-pv ", -pv)
    return npf.pmt(monthly_interest_rate, nper, -pv)

def calculate_monthly_total_payment(annual_interest_rate, nper, pv):
    monthly_interest_rate = (1 + annual_interest_rate) ** (1 / 12) - 1
    return npf.pmt(monthly_interest_rate, nper, -pv)


class BalloonPrincipalAPIView(APIView):
    """
    API endpoint for calculating Balloon Principal payments and XIRR.
    """
    
    def post(self, request):
        try:
            data = request.data
            type = data.get("type", "").upper()
            loan_amount = data.get("loan_amount")
            num_fractions = data.get("num_fractions")
            fractional_unit_value = data.get("fractional_unit_value")
            annual_interest_rate = data.get("annual_interest_rate")
            total_installments = data.get("total_installments")
            loan_period_years = data.get("loan_period_years")
            units_bought = data.get("units_bought")
            payment_frequency = data.get("payment_frequency", "").upper()
            disbursed_date = datetime.date(2024, 4, 1)
            first_payment_date = datetime.date(2024, 5, 1)
            additional_payment = data.get("additional_payment")
            end_date = datetime.date(2024, 8, 18)
            number_of_period = data.get("number_of_period")

            if type == "BUYER":
                # Calculate monthly payment
                monthly_payment = calculate_monthly_total_payment(
                    annual_interest_rate=annual_interest_rate,
                    nper=number_of_period,
                    pv=fractional_unit_value * units_bought,
                )
                
                # Calculate XIRR for buyer
                dates, amounts, xirr_value = calculate_BaloonPrincipalBuyer_price_to_XIRR(
                    fractional_unit_value,
                    loan_amount,
                    num_fractions,
                    annual_interest_rate,
                    total_installments,
                    units_bought,
                    loan_period_years,
                    disbursed_date,
                    first_payment_date,
                    payment_frequency,
                    monthly_payment,
                )
                
                # Format response data
                response_data = {
                    "investment_amount": f"{abs(amounts[0]):.2f}",
                    "payments": [
                        {
                            "payment_number": i,
                            "date": dates[i].strftime("%Y-%m-%d"),
                            "amount": f"{amounts[i]:.2f}",
                        }
                        for i in range(1, len(dates))
                    ],
                    "xirr": f"{xirr_value * 100:.2f}%",
                }
                return Response(response_data, status=status.HTTP_200_OK)

            elif type == "SELLER":
                target_xirr = data.get("target_xirr")
                monthly_payment = 25019.2749869395 * units_bought
                
                if target_xirr:
                    # Calculate price based on target XIRR
                    result = calculate_BalloonPrincipalSeller_XIRR_to_price(
                        fractional_unit_value,
                        loan_amount,
                        num_fractions,
                        annual_interest_rate,
                        units_bought,
                        loan_period_years,
                        disbursed_date,
                        first_payment_date,
                        payment_frequency,
                        end_date,
                        target_xirr,
                        monthly_payment,
                    )
                    
                    response_data = {
                        "verified_target_xirr": result["verified_target_xirr"],
                        "difference_from_target": result["difference_from_target"],
                        "cashflow_details": result["cashflow_details"],
                        "sale_price": result["sale_price"],
                    }
                    return Response(response_data, status=status.HTTP_200_OK)
                
                # Calculate XIRR for seller
                dates, amounts, xirr_value = calculate_BalloonPrinipalSeller_price_to_XIRR(
                    fractional_unit_value,
                    loan_amount,
                    num_fractions,
                    annual_interest_rate,
                    units_bought,
                    loan_period_years,
                    disbursed_date,
                    first_payment_date,
                    payment_frequency,
                    additional_payment,
                    end_date,
                )
                
                # Format response data
                response_data = {
                    "investment_amount": f"{abs(amounts[0]):.2f}",
                    "payments": [
                        {
                            "payment_number": i,
                            "date": dates[i].strftime("%Y-%m-%d"),
                            "amount": f"{amounts[i]:.2f}",
                        }
                        for i in range(1, len(dates))
                    ],
                    "xirr": f"{xirr_value:.2%}",
                }
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response({"message": "type is invalid"}, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BalloonInterestOnlyAPIView(APIView):
    """
    API endpoint for calculating Balloon Interest Only payments and XIRR.
    """
    
    def post(self, request):
        try:
            data = request.data
            type = data.get("type", "").upper()
            loan_amount = data.get("loan_amount")
            num_fractions = data.get("num_fractions")
            fractional_unit_value = loan_amount / num_fractions
            annual_interest_rate = data.get("annual_interest_rate")
            total_installments = data.get("total_installments")
            loan_period_years = data.get("loan_period_years")
            units_bought = data.get("units_bought")
            payment_frequency = data.get("payment_frequency", "").upper()
            disbursed_date = datetime.date(2024, 4, 1)
            first_payment_date = datetime.date(2024, 5, 1)
            additional_payment = data.get("additional_payment")
            end_date = datetime.date(2024, 8, 18)
            investment_amount = data.get("investment_amount")

            if type == "BUYER":
                # Calculate XIRR for buyer
                dates, amounts, xirr_value = calculate_BallonInterestOnlyBuyer_price_to_XIRR(
                    fractional_unit_value,
                    loan_amount,
                    num_fractions,
                    annual_interest_rate,
                    total_installments,
                    units_bought,
                    loan_period_years,
                    disbursed_date,
                    first_payment_date,
                    payment_frequency,
                    investment_amount,
                )
                
                # Format response data
                response_data = {
                    "investment_amount": f"{abs(amounts[0]):.2f}",
                    "payments": [
                        {
                            "payment_number": i,
                            "date": dates[i].strftime("%Y-%m-%d"),
                            "amount": f"{amounts[i]:.2f}",
                        }
                        for i in range(1, len(dates))
                    ],
                    "xirr": f"{xirr_value * 100:.2f}%",
                }
                return Response(response_data, status=status.HTTP_200_OK)

            elif type == "SELLER":
                monthly_payment = 25019.2749869395 * units_bought
                target_xirr = data.get("target_xirr")
                
                if target_xirr:
                    # Calculate price based on target XIRR
                    result = calculate_BalloonInterestOnlySeller_XIRR_to_price(
                        fractional_unit_value,
                        loan_amount,
                        num_fractions,
                        annual_interest_rate,
                        units_bought,
                        loan_period_years,
                        disbursed_date,
                        first_payment_date,
                        payment_frequency,
                        end_date,
                        target_xirr,
                        monthly_payment,
                    )
                    
                    response_data = {
                        "verified_target_xirr": result["verified_target_xirr"],
                        "difference_from_target": result["difference_from_target"],
                        "cashflow_details": result["cashflow_details"],
                        "sale_price": result["sale_price"],
                    }
                    return Response(response_data, status=status.HTTP_200_OK)

                # Calculate XIRR for seller
                selling_price = data.get("selling_price")
                dates, amounts, xirr_value = calculate_BalloonInterestOnlySeller_price_to_XIRR(
                    fractional_unit_value,
                    loan_amount,
                    num_fractions,
                    annual_interest_rate,
                    units_bought,
                    loan_period_years,
                    disbursed_date,
                    first_payment_date,
                    payment_frequency,
                    additional_payment,
                    end_date,
                    monthly_payment,
                    selling_price,
                )
                
                # Format response data
                response_data = {
                    "investment_amount": f"{abs(amounts[0]):.2f}",
                    "payments": [
                        {
                            "payment_number": i,
                            "date": dates[i].strftime("%Y-%m-%d"),
                            "amount": f"{amounts[i]:.2f}",
                        }
                        for i in range(1, len(dates))
                    ],
                    "xirr": f"{xirr_value:.2%}",
                }
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response({"message": "type is invalid"}, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
