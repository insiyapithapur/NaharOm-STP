from django.urls import path , include
from . import views
from .views import UserPersonateAPI
from .views import TransactionLogAPI

urlpatterns = [
    path('extract-invoices/',views.ExtractInvoicesAPI, name='extract_invoices_api'),
    path('transaction-logs/', TransactionLogAPI.as_view(), name='transaction_log_api'),
    path('get-invoices/<int:user_id>/', views.GetInvoicesAPI),
    path('get-invoices/<int:user_id>/<int:primary_invoice_id>/', views.GetInvoicesAPI),
    path('invoice-management/<int:user>',views.InvoiceMgtAPI),  #DONE
    path('configurations/',views.ConfigurationAPI), #DONE
    path('post-invoice/',views.PostInvoiceAPI), #DONE
    path('onboarding-report/<int:user>',views.UserManagementAPI), #DONE
    path('transaction-report/<int:user>',views.usersLedgerAPI),
    path('sales-purchased-report/<int:user>',views.SalesPurchasedReportAPI),
    path('tds-report/<int:user>',views.TdsReportAPI),
    path('bid-report/<int:user>',views.BidReportAPI),
    path('trading-activity-report/<int:user>',views.TradingActivityReportAPI),
    path('api-management-report/<int:user>',views.APIMgtReportAPI),
    path('generate-token/<int:admin_id>/<int:user_role_id>/',views.GenerateTokenAPI),
    path('impersonate/<int:admin_id>/<int:user_role_id>/', UserPersonateAPI.as_view(), name='user_impersonate_api'),
]
