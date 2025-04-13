from django.urls import path , include
from . import views

#  user = user role id
urlpatterns = [
    path('generate-otp/',views.GenerateOtpAPI.as_view()),
    path('verify-otp/',views.VerifyOtpAPI.as_view()),
    path('verify-status/<int:user>',views.VerifyStatusAPI.as_view()), 
    path('phone-to-prefill/<int:user>',views.PhoneToPrefillAPI.as_view()),   
    path('pan-to-gst/',views.PANToGSTAPI.as_view()),
    path('profile/', views.ProfileAPIView.as_view()),
    path('profile/<int:user>/', views.ProfileAPIView.as_view()),
    path('bank-account-details/', views.BankAccountDetailsAPIView.as_view()),
    path('credit-funds/', views.CreditFundsAPIView.as_view()),
    path('withdraw-funds/', views.WithdrawFundsAPIView.as_view()),
    path('ledger/<int:user>/', views.LedgerAPIView.as_view()),
    path('show-funds/<int:user_role_id>/', views.ShowFundsAPIView.as_view()),
    path('get-sell-purchase-details/<int:user>/', views.GetSellPurchaseDetailsAPIView.as_view()),
    path('to-buy/', views.ToBuyAPIView.as_view()),
    path('post-for-sell/', views.ToSellAPIView.as_view()),
    path('check-balance-against-bid-price/', views.CheckBalanceAgainstBidPriceAPIView.as_view()),
    path('proceed-to-bid/', views.ProceedToBidAPIView.as_view()),
    path('modify-bid/', views.ModifyBidAPIView.as_view()),
    path('withdraw-bid/', views.WithdrawBidAPIView.as_view(), name='withdraw-bid'),
    path('accept-bid/', views.AcceptBidAPIView.as_view(), name='accept-bid'),
    path('cash-flow/<int:invoiceID>/', views.CashFlowAPIView.as_view(), name='cash-flow'),
]
