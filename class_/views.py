from django.shortcuts import render, HttpResponseRedirect, redirect, HttpResponse
from django.urls import reverse_lazy
from django.views.generic import DetailView
from class_.models import Attendance, Class, ClassJoined, Recording, Stream, Comment, Room
from student.models import Student
from django.contrib import messages
# Create your views here.

from django.views.decorators import gzip
from django.http import JsonResponse, StreamingHttpResponse
import os
from django.utils import timezone
from threading import Thread

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile


from class_.camera import VideoCamera

def stream_all_cameras(cameras):
    while (True):
        for camera in cameras:
            camera["object"].video.read()
    
    

rooms_info = Room.objects.all().values("id", "name", "camera", "link")

information = []
for room in rooms_info:
    if ("rtsp" not in room["link"]):
        room["object"] = VideoCamera(int(room["link"]))
    else:
        room["object"] = VideoCamera(room["link"])
    print(room["link"])
    #room["object"] = VideoCamera(0)
    information.append(room)
# Create your views here.
#camera = VideoCamera()

#Thread(target = stream_all_cameras, args = (information,), daemon = True).start()

def find_index(array, id):
    for row in array:
        if (int(id) == row["id"]):
            return row["id"]-1
    return None

def stream_camera(request, code):
  
    class_info = Class.objects.get(code = code)
    recordings = Recording.objects.filter(class_room_id = class_info.id)
    template = "class_/camera.html"
    
    content = {
        'index': class_info.id,
        'teacher_name':class_info.teacher.name,
        'teacher_email':class_info.teacher.user,
        'assignments':'/class/details/'+code,
        'stream':'/class/stream_camera/'+code,
        'students':'/class/request/student/'+str(class_info.id),
        'recordings':recordings,
        'class_name':class_info.name,
    }
    return render(request, template, content)

def gen(id):
    class_obj = Class.objects.get(id = id)
    index = find_index(information, class_obj.room.id)
    
    (information[index]["object"]).set_database(class_obj.code) 
    while True:
        frame = information[index]["object"].get_frame()
        yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

def stop_feed(request, value):
    
    try:
        class_info = Class.objects.get(code = value)
        index = find_index(information, class_info.room.id)
        information[index]["object"].stop_frame()
        return JsonResponse(
            {"message":"stopped",
            "status":True}
        )
    except:
        return JsonResponse(
            {"message":"Problem Occured",
            "status":False}
        )

def start_feed(request, value):
    try:
        class_info = Class.objects.get(code = value)
        index = find_index(information, class_info.room.id)
        information[index]["object"].start_frame()
        return JsonResponse(
            {"message":"started",
            "status":True}
        )
    except:
        return JsonResponse(
            {"message":"Problem Occured",
            "status":False}
        )
    

def video_feed(request, value):
    
    return StreamingHttpResponse(gen(value),
					content_type='multipart/x-mixed-replace; boundary=frame')


def requeststudent(request, id):
        
    all_id = [x.student_id for x in ClassJoined.objects.filter(
        class_join_id=id, is_accept=True)]
    reqeust_id = [x.student_id for x in ClassJoined.objects.filter(
        class_join_id=id, is_accept=False)]
    context = {
        'class': Class.objects.get(id=id),
        'student': Student.objects.filter(id__in=all_id),
        'request_student': Student.objects.filter(id__in=reqeust_id),
        'attendance':Attendance.objects.filter(class_room = id)
    }
    return render(request, 'class_/class_student_request.html', context)


def classRemove(request, id):
    class_ = Class.objects.get(id=id)
    class_.delete()
    return redirect(reverse_lazy('teacher_dashboard'))


def requestAccept(request, class_id, student_id):
    classJoin = ClassJoined.objects.get(
        class_join_id=class_id, student_id=student_id)
    classJoin.is_accept = True
    classJoin.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def studentRemoveFromClass(request, class_id, student_id):
    print(class_id)
    print(student_id)
    classJoin = ClassJoined.objects.get(
        class_join_id=class_id, student_id=student_id)
    classJoin.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def stream(request):
    if request.method == 'GET':
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    else:
        try:
            content = request.POST.get('content')
            file = request.FILES.get('file')
            class_id = request.POST.get('class_id')
            s = Stream(content=content, file=file, class_stream_id=class_id)
            s.save()
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        except:
            messages.add_message(request, messages.ERROR, 'some error occured')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def comment(request):
    if request.method == 'GET':
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    else:
        try:
            comment = request.POST.get('comment')
            stream_id = request.POST.get('stream_id')
            s = Comment(comment=comment, stream_id=stream_id,
                        user_id=request.user.id)
            s.save()
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        except:
            messages.add_message(request, messages.ERROR, 'some error occured')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


def getClassId(code):
    print(code)
    c = Class.objects.get(code=code)
    return c.id


class ClassDetailView(DetailView):
    model = Class
    slug_field = 'code'

    def get_context_data(self, **kwargs):
        context = super(ClassDetailView, self).get_context_data(**kwargs)
        class_id = getClassId(self.kwargs['slug'])
        s = Stream.objects.filter(class_stream_id=class_id)
        c = Comment.objects.all()
        context['stream'] = s
        context['comment'] = c
        return context
