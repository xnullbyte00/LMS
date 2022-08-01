from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.views import View
from django.utils.decorators import method_decorator
from psycopg2 import Timestamp
from .forms import ManagerForm
from account.models import Account
from .models import Manager
from lms.mail import Mail
import random
import string
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from teacher.models import Teacher
from student.models import Student
from lms.suspend import suspend_user, unsuspend_user
from django.core.cache import cache
from django.views.generic import DetailView
from class_.models import Attendance, ClassJoined, Recording, Class, Room, Configuration, Schedule, TeacherAttendance
from threading import Thread
from time import sleep
from datetime import time as clocktime
from google_drive import GoogleDrive
import shutil
from lms.settings import RECORDINGS_URL, RECORDING_ROOT
from datetime import datetime
drive = GoogleDrive()
from lms.constants import *
import os
from moviepy.editor import VideoFileClip
from django.db.models import Count
from django.db.models import Prefetch


# Create your views here.

def getInfoFromStatus(tuple, value):
    for pair in tuple:
        if (value in pair):
            return pair[1]
    
    return "No info fround from given value"

def getSeconds(datetime_time):
    return datetime_time.hour*3600+datetime_time.minute*60+datetime_time.second


def convertVideo(file_url):
    print("Converting video ....")
    VideoFileClip(file_url).write_videofile(file_url.split('.mp4')[0]+"_lms.mp4")
    print("Converted ....")
    return True
    

def downloadVideos():
    is_list = True
    items = drive.get_information(page_size = 20)
    try:
        items.keys()
        is_list = False     
    except:
        pass
    if (is_list):
        for item in items:  
            
            timestamp_datetime = datetime.strptime(item["name"].split('_')[1] + \
                                       " " + item["name"].split('_')[2].split('.')[0] ,
                                       "%Y-%m-%d %H-%M-%S")
            
            timestamp = clocktime(timestamp_datetime.hour, 
                                  timestamp_datetime.minute,
                                  timestamp_datetime.second)
            minimum_time_arr = []
            all_schedules = Schedule.objects.all() 
            
            for i in range(len(all_schedules)):
                time_diff = abs(getSeconds(timestamp)-getSeconds(all_schedules[i].start_time))
                minimum_time_arr.append(time_diff)
            index = minimum_time_arr.index(min(minimum_time_arr))
            
            drive.get_file(item["id"], item["name"])
            shutil.move(item["name"], RECORDINGS_URL[1:]+item["name"])
            convertVideo(RECORDINGS_URL[1:]+item["name"])
            os.remove(RECORDINGS_URL[1:]+item["name"])
            drive.delete_file(item["id"])
            class_room = Class.objects.filter(room = 
                                      Room.objects.get(camera = int(item["name"].split("_")[0])),
                                      day = timestamp_datetime.strftime('%A').lower()[0:3], 
                                      timing_id = all_schedules[index].id)
            if (class_room.count() > 0):
                try:
                    r = Recording(class_room_id = class_room[0].id,
                            video  = item["name"].split('.mp4')[0]+"_lms.mp4", 
                            timestamp = timestamp_datetime)
                    r.save()
                except:
                    print("Already saved")
            else:
                r = Recording(class_room = None,
                            video  = item["name"].split('.mp4')[0]+"_lms.mp4", 
                            timestamp = timestamp_datetime)
                r.save()
                
            
    else:
        print("No file found")
      
def call_thread():
    
    while (True):
        permission = Configuration.objects.first().uploading_allowed
        print("Permision status:",permission)
        if (permission):
            print("Granted...!")
            permission = Configuration.objects.first().uploading_allowed
            downloadVideos()
            sleep(Configuration.objects.first().uploading_time)
        else:
            sleep(Configuration.objects.first().uploading_time)

t = Thread(target = call_thread, args = (), daemon=True)
t.start()    


def randomPassword():
    password = ''
    letters = string.ascii_letters + string.digits + string.punctuation
    for i in range(10):
        password = password+str(random.choice(letters))
    return password


class FirstManager(View):
    template_name = 'manager/first.html'
    form = ManagerForm

    @method_decorator(login_required, 'signin')
    def get(self, request, *arg, **kwargs):
        
        
        try:
            a = Manager.objects.get(user_id=request.user.id)
            return redirect(reverse_lazy('manager_dashboard'))
        except:
            context = {
                'form': self.form()
            }
            return render(request, self.template_name, context)

    def post(self, request, *arg, **kwargs):
        myform = self.form(request.POST)
        if myform.is_valid():
            data = myform.save(commit=False)
            data.user_id = request.user.id
            data.save()
            user = Account.objects.get(id=request.user.id)
            user.is_firstLogin = False
            user.save()
            return redirect(reverse_lazy('manager_dashboard'))
        else:
            return render(request, self.template_name, {'form': myform})


class ManagerView(View):
    template_name = 'manager/dashboard.html'
    
    @method_decorator(login_required, 'signin')
    def get(self, request, *arg, **kwargs):
        if request.user.is_firstLogin:
            return redirect(reverse_lazy('first_manager'))
        else:
            m = Manager.objects.get(user_id=request.user.id)
            c = Configuration.objects.first()
            timings = Schedule.objects.all()
                        
            content = {
                'manager_name':m.name,
                'college_name':COLLEGE_NAME,
                'config':c,
                'schedule':timings,
            }
            
            return render(request, self.template_name, content)


class TeacherView(View):
    template_name = 'manager/teacher.html'

    @method_decorator(login_required, 'signin')
    def get(self, request, *arg, **kwargs):
        teacher = Teacher.objects.all()
        context = {
            'teacher': teacher
        }
        cache.clear()
        return render(request, self.template_name, context)

    @method_decorator(login_required, 'signin')
    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        name = request.POST.get('name')
        password_ = randomPassword()
        try:
            user = Account(email=email, password=make_password(
                password_), is_teacher=True)
            user.save()
            msg = f'{name}, Your account is created Please use the following credential to login into your account \n Email: {email} \n password: {password_}'
            Mail(subject="Account Creation",
                 message=msg, recipient_list=[email, ])
            teacher = Teacher(name=name, user_id=user.id)
            teacher.save()
            messages.add_message(request, messages.SUCCESS,
                                 'Teacher Account is created successfully')
            return redirect(reverse_lazy('manage_teacher'))
        except Exception as e:
            messages.add_message(request, messages.ERROR, str(e))
            return redirect('manage_teacher')


class TeacherDetailsView(DetailView):
    model = Teacher


class StudentView(View):
    template_name = 'manager/student.html'

    @method_decorator(login_required, 'signin')
    def get(self, request, *arg, **kwargs):
        student = Student.objects.all()
        context = {
            'student': student
        }
        cache.clear()
        return render(request, self.template_name, context)

    @method_decorator(login_required, 'signin')
    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        name = request.POST.get('name')
        password_ = randomPassword()
        try:
            user = Account(email=email, password=make_password(
                password_), is_student=True)
            user.save()
            msg = f'{name}, Your account is created Please use the following credential to login into your account \n Email: {email} \n password: {password_}'
            Mail(subject="Account Creation",
                 message=msg, recipient_list=[email, ])
            student = Student(name=name, user_id=user.id)
            student.save()
            messages.add_message(request, messages.SUCCESS,
                                 'Student Account is created successfully')
            return redirect('manage_student')
        except Exception as e:
            messages.add_message(request, messages.ERROR, str(e))
            return redirect('manage_student')


class StudentDetailsView(DetailView):
    model = Student


def delete_teacher(request, id):
    try:
        t = Account.objects.get(id=id)
        t.delete()
        messages.add_message(request, messages.SUCCESS, 'Successfully Delete')
        return redirect(reverse_lazy('manage_teacher'))
    except:
        messages.add_message(request, messages.ERROR, 'some error occured')
        return redirect(reverse_lazy('manage_teacher'))


def suspend_teacher(request, user_id):
    try:
        if suspend_user(user_id):
            messages.add_message(request, messages.SUCCESS,
                                 'successfully suspended')
        else:
            messages.add_message(
                request, messages.ERROR, 'could not suspend right now plase try again later')
        return redirect(reverse_lazy('manage_teacher'))
    except:
        messages.add_message(request, messages.ERROR,
                             'could not suspend right now plase try again later')
        return redirect(reverse_lazy('manage_teacher'))


def unsuspend_teacher(request, user_id):
    try:
        if unsuspend_user(user_id):
            messages.add_message(request, messages.SUCCESS,
                                 'successfully Released')
        else:
            messages.add_message(
                request, messages.ERROR, 'could not release right now plase try again later')
        return redirect(reverse_lazy('manage_teacher'))
    except:
        messages.add_message(request, messages.ERROR,
                             'could not release right now plase try again later')
        return redirect(reverse_lazy('manage_teacher'))


def delete_student(request, id):
    try:
        t = Account.objects.get(id=id)
        t.delete()
        messages.add_message(request, messages.SUCCESS, 'Successfully Delete')
        return redirect(reverse_lazy('manage_student'))
    except:
        messages.add_message(request, messages.ERROR, 'some error occured')
        return redirect(reverse_lazy('manage_student'))


def suspend_student(request, user_id):
    try:
        if suspend_user(user_id):
            messages.add_message(request, messages.SUCCESS,
                                 'successfully suspended')
        else:
            messages.add_message(
                request, messages.ERROR, 'could not suspend right now plase try again later')
        return redirect(reverse_lazy('manage_student'))
    except:
        messages.add_message(request, messages.ERROR,
                             'could not suspend right now plase try again later')
        return redirect(reverse_lazy('manage_student'))


def unsuspend_student(request, user_id):
    try:
        if unsuspend_user(user_id):
            messages.add_message(request, messages.SUCCESS,
                                 'successfully Released')
        else:
            messages.add_message(
                request, messages.ERROR, 'could not release right now plase try again later')
        return redirect(reverse_lazy('manage_student'))
    except:
        messages.add_message(request, messages.ERROR,
                             'could not release right now plase try again later')
        return redirect(reverse_lazy('manage_student'))


def videos(request):
    
    recordings = Recording.objects.all()
    content = {
        "recordings": recordings
    }
    return render(request, "manager/videos.html", content)

def delete_video(request):
    try:
        recording = Recording.objects.get(video = request.POST.get("video_name"))
        os.remove(os.path.join(RECORDING_ROOT, recording.video))
        video = recording.video
        recording.delete()
        return JsonResponse({
            "message":video+" file has been deleted from server",
            "status":True
        })
    except:
        return JsonResponse({
            "message":"Some error occured. Please report to the administrator",
            "status":False
        })
        

def modify_configuration(request, option):
    c = Configuration.objects.first()
    try:
        if (option == "class"):
            if (int(request.POST.get("value")) > MAX_CLASS_DURATION):
                return JsonResponse({
                "message": ("Class duration cannot be more than "+str(MAX_CLASS_DURATION/60)+ " Hours"),
                "status":False,
                })
                
            c.class_duration = request.POST.get("value")
        elif (option == "attendance"):
            if (int(request.POST.get("value")) > c.class_duration):
                return JsonResponse({
                "message": ("Attendance duration cannot be more than class duration"),
                "status":False,
                })
            
            c.attendance_duration = request.POST.get("value")
        elif (option == "uploading"):
            c.uploading_time = request.POST.get("value")
        elif (option == "pixels"):
            c.threshold_pixels = request.POST.get("value")
        elif (option == "allowed"):
            if (c.uploading_allowed):
                c.uploading_allowed = False
            else:
                c.uploading_allowed = True
        else:
            pass
        c.save()
        return JsonResponse({
            "message": "Modified",
            "status":True,
        })
    except:
         return JsonResponse({
            "message": "Not modified",
            "status":False,
        })

def modify_schedule(request, option):
    try:
        s = Schedule.objects.get(id = option)
        t_preprocess = datetime.strptime(request.POST.get("timing"), '%H:%M').time()
        all_schedule = Schedule.objects.all()
        diff_arr = []
        for schedule in all_schedule:
            t1 = schedule.start_time.hour*60+schedule.start_time.minute
            t2 = t_preprocess.hour*60+t_preprocess.minute
            diff_arr.append(abs(t2-t1))
        
        print(diff_arr)
        diff_arr.insert(option-1, 99999999)
        diff_arr.remove(diff_arr[option])
        print(diff_arr)
        if (min(diff_arr) <= Configuration.objects.first().class_duration):
            return JsonResponse({
                "message": "Your schedule time has overlapping conflicts with Schedule No: "+str(diff_arr.index(min(diff_arr))+1),
                "status":False,
            })
        
        s.start_time = request.POST.get("timing")
        s.save()
            
        return JsonResponse({
                "message": "Modified",
                "status":True,
            })
    except:
         return JsonResponse({
            "message": "Not modified",
            "status":False,
        })
         
def classes(request):

    class_details = Class.objects.prefetch_related(
    Prefetch('classjoined_set')).values("name", "room__name", "department",
                                        "timing__start_time", "day", "code",
                                        "teacher__name", "teacher__profile").annotate(total 
                = Count("classjoined__student__name")).order_by("id")
    


    content = {
        "class_details":class_details,
        "teacher_attendance":TeacherAttendance.objects.all(),
        "student_attendance":Attendance.objects.all(),
    }
    return render(request, "manager/classes.html", content)
   
def classes_delete(request):
    code = request.POST.get("code")
    try:
        class_ = Class.objects.get(code = code)
        class_.delete()
        return JsonResponse({
                    "message": "Deleted",
                    "status":True,
                })
    except:
       
        return JsonResponse({
                    "message": "Some error occured. Not deleted",
                    "status":False,
                })
        