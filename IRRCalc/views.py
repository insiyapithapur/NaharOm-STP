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


@csrf_exempt
def FixedPriceIRRAPI(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
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
                payments = [
                    {
                        "payment_number": i,
                        "date": dates[i].strftime("%Y-%m-%d"),
                        "amount": f"{amounts[i]:.2f}",
                    }
                    for i in range(1, len(dates))
                ]

                response_data = {
                    "XIRR": f"{xirr_value * 100:.2f}%",
                    "investment_amount": f"{abs(amounts[0]):.2f}",
                    "payments": payments,
                }
                return JsonResponse(response_data, status=200)

            elif type == "SELLER":
                target_xirr = data.get("target_xirr")
                additional_payment = data.get("additional_payment")
                end_date = datetime.date(2024, 8, 18)
                if target_xirr:
                    investment_amount = fractional_unit_value * units_bought
                    end_date = datetime.date(2024, 8, 18)
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
                    return JsonResponse(response_data, status=200)

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
                return JsonResponse(response_data, status=200)
            else:
                return JsonResponse({"message": "type is invalid"}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=500)
    else:
        return JsonResponse({"message": "Only POST methods is allowed"}, status=405)


@csrf_exempt
def DecliningPrincipalAPI(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
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
                return JsonResponse(response_data, status=200)

            elif type == "SELLER":
                target_xirr = data.get("target_xirr")
                if target_xirr:
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
                    return JsonResponse(response_data, status=200)

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
                return JsonResponse(response_data, status=200)
            else:
                return JsonResponse({"message": "type is invalid"}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=500)
    else:
        return JsonResponse({"message": "Only POST methods is allowed"}, status=405)


def calculate_monthly_total_payment(annual_interest_rate, nper, pv):
    print("annual_interest_rate ncd", annual_interest_rate)
    monthly_interest_rate = (1 + annual_interest_rate) ** (1 / 12) - 1
    print("monthly_interest_rate ", monthly_interest_rate)
    print("nper ", nper)
    print("-pv ", -pv)
    return npf.pmt(monthly_interest_rate, nper, -pv)


@csrf_exempt
def BalloonPrincipalAPI(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            type = data.get("type").upper()
            loan_amount = data.get("loan_amount")
            num_fractions = data.get("num_fractions")
            fractional_unit_value = data.get("fractional_unit_value")
            print("fractional_unit_value ", fractional_unit_value)
            annual_interest_rate = data.get("annual_interest_rate")
            print("annual_interest_rate ,", annual_interest_rate)
            total_installments = data.get("total_installments")
            loan_period_years = data.get("loan_period_years")
            units_bought = data.get("units_bought")
            payment_frequency = data.get("payment_frequency").upper()
            disbursed_date = datetime.date(2024, 4, 1)
            first_payment_date = datetime.date(2024, 5, 1)
            additional_payment = data.get("additional_payment")
            end_date = datetime.date(2024, 8, 18)
            number_of_period = data.get("number_of_period")

            if type == "BUYER":
                monthly_payment = calculate_monthly_total_payment(
                    annual_interest_rate=annual_interest_rate,
                    nper=number_of_period,
                    pv=fractional_unit_value * units_bought,
                )
                print("monthly_payment ", monthly_payment)
                dates, amounts, xirr_value = (
                    calculate_BaloonPrincipalBuyer_price_to_XIRR(
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
                )
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
                return JsonResponse(response_data, status=200)

            elif type == "SELLER":
                target_xirr = data.get("target_xirr")
                monthly_payment = 25019.2749869395 * units_bought
                if target_xirr:
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
                    return JsonResponse(response_data, status=200)
                print("xsjnncb")
                dates, amounts, xirr_value = (
                    calculate_BalloonPrinipalSeller_price_to_XIRR(
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
                )
                print("1233")
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
                return JsonResponse(response_data, status=200)

            else:
                return JsonResponse({"message": "type is invalid"}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=500)
    else:
        return JsonResponse({"message": "Only POST methods is allowed"}, status=405)


@csrf_exempt
def Balloon_Interest_OnlyAPI(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            type = data.get("type").upper()
            loan_amount = data.get("loan_amount")
            num_fractions = data.get("num_fractions")
            fractional_unit_value = loan_amount / num_fractions
            print("fractional_unit_value ", fractional_unit_value)
            annual_interest_rate = data.get("annual_interest_rate")
            total_installments = data.get("total_installments")
            loan_period_years = data.get("loan_period_years")
            units_bought = data.get("units_bought")
            payment_frequency = data.get("payment_frequency").upper()
            disbursed_date = datetime.date(2024, 4, 1)
            first_payment_date = datetime.date(2024, 5, 1)
            additional_payment = data.get("additional_payment")
            end_date = datetime.date(2024, 8, 18)
            investment_amount = data.get("investment_amount")

            if type == "BUYER":
                dates, amounts, xirr_value = (
                    calculate_BallonInterestOnlyBuyer_price_to_XIRR(
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
                )
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
                return JsonResponse(response_data, status=200)

            elif type == "SELLER":
                monthly_payment = 25019.2749869395 * units_bought
                target_xirr = data.get("target_xirr")
                if target_xirr:
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
                    return JsonResponse(response_data, status=200)

                selling_price = data.get("selling_price")
                dates, amounts, xirr_value = (
                    calculate_BalloonInterestOnlySeller_price_to_XIRR(
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
                )
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
                return JsonResponse(response_data, status=200)

            else:
                return JsonResponse({"message": "type is invalid"}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"message": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"message": str(e)}, status=500)
    else:
        return JsonResponse({"message": "Only POST methods is allowed"}, status=405)
