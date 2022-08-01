from . import views
from django.urls import path
from .views import (StudentView,searchclass,classJoin, student_profile, 
                    student_store, student_update
                    )
urlpatterns = [
    path('dashboard/',StudentView.as_view(),name='student_dashbaord'),
    path('search/',searchclass,name='search'),
    path('classjoing/<int:class_id>',classJoin,name='class_join'),
    path('dashboard/profile', student_profile, name = "student_profile"),
      path('dashboard/store', student_store, name = "student_store"),
     path('dashboard/update', student_update, name = "student_update")
    

]
