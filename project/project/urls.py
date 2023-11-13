from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # admin url
    path('admin/', admin.site.urls),
    # blockstepauction app url
    path('', include('blockstepauction.urls')),
]
