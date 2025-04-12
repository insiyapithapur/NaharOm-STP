from django.urls import path
from . import views

urlpatterns = [
    path('fixed_price/',views.FixedPriceIRRAPI),
    path('declining_principal/',views.DecliningPrincipalAPI),
    path('balloon_principal/',views.BalloonPrincipalAPI),
    path('balloon_Interest_Only/',views.Balloon_Interest_OnlyAPI)
]