from django.urls import path
from . import views

urlpatterns = [
    path('fixed_price/', views.FixedPriceIRRAPIView.as_view()),
    path('declining_principal/', views.DecliningPrincipalAPIView.as_view()),
    path('balloon_principal/', views.BalloonPrincipalAPIView.as_view()),
    path('balloon_interest_only/', views.BalloonInterestOnlyAPIView.as_view()),
]