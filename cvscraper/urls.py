from django.contrib import admin
from django.urls import path
from home import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', views.upload_file, name='upload_cv'),
    path('process/', views.process_files, name='process_files'),
    path('download/', views.download_excel, name='download_excel'),
]
