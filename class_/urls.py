from django.urls import path
from .views import (
    ClassDetailView,
    classRemove,
    requestAccept,
    requeststudent,
    studentRemoveFromClass,
    stream,
    comment,video_feed,
    start_feed,
    stop_feed,
    stream_camera
)
from django.conf.urls import url

urlpatterns = [
    path('details/<slug:slug>/',ClassDetailView.as_view(),name='class_details'),
    path('remove/<int:id>/',classRemove,name='class_remove'),
    path('request/student/<int:id>',requeststudent,name='class_student_request'),
    path('accept/<int:class_id>/<int:student_id>',requestAccept,name='requestAccept'),
    path('student/remove/<int:class_id>/<int:student_id>', studentRemoveFromClass, name='remove_student'),
    path('stream/',stream,name='stream_class'),
    path('comment/',comment,name='comment'),
    url(r'^video_feed/(?P<value>\d+)/$', video_feed, name='video_feed'),
    path('start_feed/<str:value>/',start_feed,name='start_feed'),
    path('stop_feed/<str:value>/',stop_feed,name='stop_feed'),
    path('stream_camera/<str:code>/',stream_camera,name='stream_camera'),
    
]