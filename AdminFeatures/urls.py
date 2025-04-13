from django.urls import path , include
from . import views

urlpatterns = [
    path('extract-invoices/', views.ExtractInvoicesAPIView.as_view()),
    path('transaction-logs/', views.TransactionLogAPIView.as_view()),
    path('get-invoices/<int:user_id>/', views.GetInvoicesAPIView.as_view()),
    path('get-invoices/<int:user_id>/<int:primary_invoice_id>/', views.GetInvoicesAPIView.as_view()),
    path('invoice-management/<int:user>/', views.InvoiceMgtAPIView.as_view()),
    path('configurations/', views.ConfigurationAPIView.as_view()),
    path('post-invoice/', views.PostInvoiceAPIView.as_view()),
    path('onboarding-report/<int:user>/', views.UserManagementAPIView.as_view()),
    path('transaction-report/<int:user>/', views.UsersLedgerAPIView.as_view()),
    path('sales-purchased-report/<int:user>/', views.SalesPurchasedReportAPIView.as_view()),
    path('tds-report/<int:user>/', views.TdsReportAPIView.as_view()),
    path('bid-report/<int:user>/', views.BidReportAPIView.as_view()),
    path('trading-activity-report/<int:user>/', views.TradingActivityReportAPIView.as_view()),
    path('api-management-report/<int:user>/', views.APIMgtReportAPIView.as_view()),
    path('generate-token/<int:admin_id>/<int:user_role_id>/', views.GenerateTokenAPIView.as_view()),
    path('impersonate/<int:admin_id>/<int:user_role_id>/', views.UserImpersonateAPIView.as_view()),
]
