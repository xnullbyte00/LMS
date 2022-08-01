from . import views
from django.urls import path
from .views import (TeacherView,
                    teacher_profile,
                    teacher_store,
                    teacher_update,
                    )
urlpatterns = [
    path('dashboard/',TeacherView.as_view(),name='teacher_dashboard'),
    path('dashboard/profile', teacher_profile, name = "teacher_profile"),
    path('dashboard/store', teacher_store, name = "teacher_store"),
     path('dashboard/update', teacher_update, name = "teacher_update")
]
