from django.contrib import admin
from django.urls import path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns # <-- NOVO IMPORT

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("portfolio.urls")),
    path("aporte/", include("aporte.urls")), 
    path("panorama/", include("panorama.urls")),  
    path("playbook/", include("playbook.urls")),
]

# <-- ISTO FORÇA O DJANGO A SERVIR O CSS MESMO RODANDO VIA UVICORN -->
urlpatterns += staticfiles_urlpatterns()