from django.contrib import admin
from django.urls import path, include

# from django.conf import settings
# from django.conf.urls.static import static
# from django.conf import settings
# from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # for simple jwt token
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # other urls
    path("admin/", admin.site.urls),
    path("", include("UserFeatures.urls")),
    path("appAdmin/", include("AdminFeatures.urls")),
    path("irr/", include("IRRCalc.urls")),
    path("api-management/", include("ApiManagement.urls")),
    path("primary-apis/", include("PrimaryApis.urls")),
]
urlpatterns += staticfiles_urlpatterns()
