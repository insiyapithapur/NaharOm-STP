from UserFeatures import models


# @csrf_exempt
# def TobuyAPI(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             user_role_id = data.get('user_role_id')  
#             invoice_secondary_id = data.get('invoice_secondary_id')
#             wallet_id = data.get('wallet_id')
#             seller_id = data.get('seller_id') #if 2nd buyer
#             fractional_unit_id = data.get('fractional_unit_id') #automatically assign
#             no_of_partition = data.get('no_of_partition')
#             total_amount_invested = data.get('total_amount_invested')
#             purchase_date = timezone.now().date()
#             purchase_time = timezone.now().time()

#             try:
#                 user_role = models.UserRole.objects.get(id=user_role_id)
#             except models.UserRole.DoesNotExist:
#                 return JsonResponse({"message": "User role not found"}, status=404)

#             try:
#                 invoice = models.Invoices.objects.get(id=invoice_secondary_id)
#             except models.Invoices.DoesNotExist:
#                 return JsonResponse({"message": "Invoice not found"}, status=404)

#             try:
#                 buyer_wallet = models.OutstandingBalance.objects.get(id=wallet_id)
#             except models.OutstandingBalance.DoesNotExist:
#                 return JsonResponse({"message": "Buyer Wallet not found"}, status=404)

#             if not all([no_of_partition, total_amount_invested]):
#                 return JsonResponse({"message": "All fields are required"}, status=400)

#             with transaction.atomic():
#                 # first check if seller_id is there is request
#                 if seller_id:
#                     try:
#                         seller = models.Sellers.objects.get(id=seller_id)
#                     except models.Sellers.DoesNotExist:
#                         return JsonResponse({"message": "Seller not found"}, status=404)
                    
#                     # no_of_partition if 3 requested che so 3 remaining che k nai first a check karvanu 
#                     # from seller table ane if remaining che fractional_units table mathi koi bhi 3 j 
#                     # seller ni id ni hoi a assign kari devani 

#                     # checking if no_of_partition the user_role_id is requesting is there or not from Seller table
#                     if seller.remaining_partitions < no_of_partition :
#                         return JsonResponse({"message": "Not enough fractional units available"}, status=400)
                    
#                     fractional_units = models.FractionalUnits.objects.filter(
#                         current_owner=seller.buyer.user, sold=True)[:no_of_partition]
#                     fractional_units_count = fractional_units.count()
#                     print("fractional_units_count ",fractional_units_count)

#                     # checking if no_of_partition the user_role_id is requesting is there or not from FractionalUnits table whose current_owner is seller
#                     if fractional_units_count < no_of_partition :
#                         return JsonResponse({"message": "Not enough fractional units available"}, status=400)
                    
#                     # if there is fractional_units then it will register user_role_id as buyer
#                     buyer = models.Buyers.objects.create(
#                         user=user_role,
#                         invoice=invoice,
#                         no_of_partitions=no_of_partition,
#                         total_amount_invested=total_amount_invested,
#                         wallet=wallet,
#                         purchase_date=purchase_date,
#                         purchase_time=purchase_time,
#                     )
                    
#                     for unit in fractional_units:
#                         unit.current_owner = user_role
#                         unit.save()
#                         models.SalePurchaseReport.objects.create(
#                             unit=unit,
#                             seller=seller,
#                             buyer=buyer,
#                             transaction_date=timezone.now()
#                         )

#                     seller.remaining_partitions = seller.remaining_partitions - no_of_partition
#                     if seller.remaining_partitions == 0:
#                         seller.someone_purchased = True
#                     seller.save()

#                     # try:
#                     #     seller_wallet = models.OutstandingBalance.objects.get(id=seller.wallet.)
#                     # except models.OutstandingBalance.DoesNotExist:
#                     #     return JsonResponse({"message": "Wallet not found"}, status=404)
#                     seller_wallet = seller.wallet
#                     print("seller.wallet.balance " ,seller.wallet.balance)
#                     seller_wallet.balance = seller_wallet.balance + total_amount_invested
#                     seller_wallet.save()

#                     models.OutstandingBalanceTransaction.objects.create(
#                         wallet=seller_wallet,
#                         transaction_id=uuid.uuid4(),
#                         type='sell',
#                         creditedAmount=total_amount_invested,
#                         debitedAmount=0,
#                         status='response',
#                         source='wallet_to_sell',
#                         purpose='Funds received from selling',
#                         bank_acc=None,
#                         invoice=invoice,
#                         time_date=timezone.now()
#                     )

#                     if buyer_wallet.balance < total_amount_invested:
#                         return JsonResponse({"message": "Insufficient funds in the wallet"}, status=400)
#                     else:
#                         buyer_wallet.balance = buyer_wallet - total_amount_invested
#                         buyer_wallet.save()

#                     models.OutstandingBalanceTransaction.objects.create(
#                         wallet=buyer_wallet,
#                         transaction_id=uuid.uuid4(),
#                         type='buy',
#                         creditedAmount=0,
#                         debitedAmount=total_amount_invested,
#                         status='response',
#                         source='wallet_to_buy',
#                         purpose='Funds used for purchasing',
#                         bank_acc=None,
#                         invoice=invoice,
#                         time_date=timezone.now()
#                     )

#                     return JsonResponse({"message": "Transaction completed successfully", "buyer_id": buyer.id}, status=201)
#                 else:
#                     fractional_units = models.FractionalUnits.objects.filter(
#                         current_owner=NULL, sold=False)[:no_of_partition]
#                     fractional_units_count = fractional_units.count()
#                     print("fractional_units_count ",fractional_units_count)

#                     # checking if no_of_partition the user_role_id is requesting is there or not from FractionalUnits table whose current_owner is seller
#                     if fractional_units_count < no_of_partition :
#                         return JsonResponse({"message": "Not enough fractional units available"}, status=400)
                    
#                     # if there is fractional_units then it will register user_role_id as buyer
#                     buyer = models.Buyers.objects.create(
#                         user=user_role,
#                         invoice=invoice,
#                         no_of_partitions=no_of_partition,
#                         total_amount_invested=total_amount_invested,
#                         wallet=wallet,
#                         purchase_date=purchase_date,
#                         purchase_time=purchase_time,
#                     )

#                     for unit in fractional_units:
#                         unit.current_owner = user_role
#                         unit.sold = True
#                         unit.save()
                    
#                     if buyer_wallet.balance < total_amount_invested:
#                         return JsonResponse({"message": "Insufficient funds in the wallet"}, status=400)
#                     else:
#                         buyer_wallet.balance = buyer_wallet - total_amount_invested
#                         buyer_wallet.save()

#                     models.OutstandingBalanceTransaction.objects.create(
#                         wallet=buyer_wallet,
#                         transaction_id=uuid.uuid4(),
#                         type='buy',
#                         creditedAmount=0,
#                         debitedAmount=total_amount_invested,
#                         status='response',
#                         source='wallet_to_buy',
#                         purpose='Funds used for purchasing',
#                         bank_acc=None,
#                         invoice=invoice,
#                         time_date=timezone.now()
#                     )
#                     return JsonResponse({"message": "Transaction completed successfully", "buyer_id": buyer.id}, status=201)
#         except json.JSONDecodeError:
#             return JsonResponse({"message": "Invalid JSON"}, status=400)
#         except Exception as e:
#             return JsonResponse({"message": str(e)}, status=500)

#     else:
#         return JsonResponse({"message": "Only POST method is allowed"}, status=405)
                    # return JsonResponse({"message": "Transaction completed successfully", "buyer_id": buyer.id}, status=201)
                

                    #now current_owner will change
                    # try:
                    #         fractional_unit = models.FractionalUnits.objects.get(unit_id=fractional_unit_id, invoice=invoice, current_owner=seller.buyer.user, sold=True)
                    #         fractional_units = [fractional_unit]
                    # except models.FractionalUnits.DoesNotExist:
                    #     fractional_units = models.FractionalUnits.objects.filter(invoice=invoice ,  sold=False)[:no_of_partition]
                    # if len(fractional_units) < no_of_partition:
                    #         return JsonResponse({"message": "Not enough fractional units available"}, status=400)

                    
                    # for unit in fractional_units:
                    #     unit.sold = True
                    #     unit.current_owner = user_role
                    #     unit.save()

                    #     models.SalePurchaseReport.objects.create(
                    #         unit=unit,
                    #         seller=seller,
                    #         buyer=buyer,
                    #     )
                # else:

                # buyer = models.Buyers.objects.create(
                #     user=user_role,
                #     invoice=invoice,
                #     no_of_partitions=no_of_partition,
                #     total_amount_invested=total_amount_invested,
                #     wallet=wallet,
                #     purchase_date=purchase_date,
                #     purchase_time=purchase_time,
                # )

                # if seller_id:
                #     try:
                #         seller = models.Sellers.objects.get(id=seller_id, remaining_partitions__gte=no_of_partition)
                #     except models.Sellers.DoesNotExist:
                #         return JsonResponse({"message": "Seller not found or not enough partitions available"}, status=404)

                    # seller_wallet = seller.wallet

                    # if fractional_unit_id:
                    #     try:
                    #         fractional_unit = models.FractionalUnits.objects.get(unit_id=fractional_unit_id, invoice=invoice, current_owner=seller.buyer.user, sold=True)
                    #         fractional_units = [fractional_unit]
                    #     except models.FractionalUnits.DoesNotExist:
                    #         return JsonResponse({"message": "Requested fractional unit not available"}, status=404)
                    # else:
                    #     fractional_units = models.FractionalUnits.objects.filter(invoice=invoice ,  sold=False)[:no_of_partition]
                    #     if len(fractional_units) < no_of_partition:
                    #         return JsonResponse({"message": "Not enough fractional units available"}, status=400)

                    # for unit in fractional_units:
                    #     unit.sold = True
                    #     unit.current_owner = user_role
                    #     unit.save()

                    #     models.SalePurchaseReport.objects.create(
                    #         unit=unit,
                    #         seller=seller,
                    #         buyer=buyer,
                    #     )

                    # seller.remaining_partitions -= no_of_partition
                    # if seller.remaining_partitions == 0:
                    #     seller.someone_purchased = True
                    # seller.save()

                    # seller_wallet.balance += total_amount_invested
                    # seller_wallet.save()

                    # models.OutstandingBalanceTransaction.objects.create(
                    #     wallet=seller_wallet,
                    #     transaction_id=uuid.uuid4(),
                    #     type='sell',
                    #     creditedAmount=total_amount_invested,
                    #     debitedAmount=0,
                    #     status='response',
                    #     source='wallet_to_sell',
                    #     purpose='Funds received from selling',
                    #     bank_acc=None,
                    #     invoice=invoice,
                    #     time_date=timezone.now()
                    # )

                # else:
                    fractional_units = models.FractionalUnits.objects.filter(invoice=invoice, sold=False)[:no_of_partition]
                    for unit in fractional_units:
                        unit.sold = True
                        unit.current_owner = user_role
                        unit.save()

                # if wallet.balance < total_amount_invested:
                #     return JsonResponse({"message": "Insufficient funds in the wallet"}, status=400)
                # else:
                #     wallet.balance -= total_amount_invested
                #     wallet.save()

                # models.OutstandingBalanceTransaction.objects.create(
                #     wallet=wallet,
                #     transaction_id=uuid.uuid4(),
                #     type='buy',
                #     creditedAmount=0,
                #     debitedAmount=total_amount_invested,
                #     status='response',
                #     source='wallet_to_buy',
                #     purpose='Funds used for purchasing',
                #     bank_acc=None,
                #     invoice=invoice,
                #     time_date=timezone.now()
                # )

            return JsonResponse({"message": "Transaction completed successfully", "buyer_id": buyer.id}, status=201)

    #     except json.JSONDecodeError:
    #         return JsonResponse({"message": "Invalid JSON"}, status=400)
    #     except Exception as e:
    #         return JsonResponse({"message": str(e)}, status=500)

    # else:
    #     return JsonResponse({"message": "Only POST method is allowed"}, status=405)