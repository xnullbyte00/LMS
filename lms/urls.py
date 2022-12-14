from django.contrib import admin
from django.urls import path,include
from . import views
from django.contrib.auth.views import (PasswordResetView,
 PasswordResetDoneView,
 PasswordResetConfirmView,
 PasswordChangeDoneView
 )
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static


admin.site.site_header = "IoT Powered Learning Management System Admin"
admin.site.site_title = "IoT Powered Learning Management System Admin Portal"
admin.site.index_title = "Welcome to IoT Powered Learning Management System"

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('',views.signin,name='signin'),
    path('manager/',include('manager.urls')),
    path('teacher/',include('teacher.urls')),
    path('student/', include('student.urls')),
    path('class/',include('class_.urls')),
    path('rest-password/',PasswordResetView.as_view(),name='forget_password'),
    path('rest-password/done/',PasswordResetDoneView.as_view(),name='password_reset_done'),
    path('rest-password/confirmation/<str:uidb64>/<str:token>',PasswordResetConfirmView.as_view(),name='password_reset_confirm'),
    path('rest-password/complete/',PasswordChangeDoneView.as_view(),name='password_reset_complete'),
    path('change-password/',views.PasswordChangeManager.as_view(),name='password_change'),
    path('logout/',LogoutView.as_view(),name='logout'),
    
    

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
