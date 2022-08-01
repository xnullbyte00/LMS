from distutils import extension
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from numpy import identity
from account.models import Account
from class_.forms import ClassForm
import random
import string
from class_.models import Class
from django.contrib import messages
from teacher.models import Teacher
from student.models import Student
from lms.settings import EMBEDDINGS_ROOT, PROFILE_ROOT, PROFILE_URL, MEDIA_URL
import os
import cv2
import face_processing as fp
import numpy as np
# Create your views here.


def randomcode(length = 5):
    code = ''
    letters = string.ascii_letters + string.digits
    for i in range(length):
        code = code+str(random.choice(letters))
    return code


def checkcode(code):
    try:
        Class.objects.get(code=code)
        return True
    except:
        return False


def getLoginTeacherId(user_id):
    t = Teacher.objects.get(user_id=user_id)
    return t.id


class TeacherView(View):
    template_name = 'teacher/dashboard.html'
    form_class = ClassForm

    @method_decorator(login_required, 'signin')
    def get(self, request, *args, **kwargs):
        
        context = {
            'form': self.form_class(),
            'class': Class.objects.filter(teacher_id=getLoginTeacherId(request.user.id)),
            'teacher': Teacher.objects.get(id=getLoginTeacherId(request.user.id)),
            #'photo': PROFILE_URL+Teacher.objects.get(id=getLoginTeacherId(request.user.id)).profile.url.split('/')[-1]
        }
        if request.user.is_firstLogin:
            return redirect(reverse_lazy('password_change'))
        else:
            return render(request, self.template_name, context)

    def post(self, request, *arg, **kwargs):
        class_form = self.form_class(request.POST)
       
        if class_form.is_valid():
            data = class_form.save(commit=False)
            code = randomcode()
            isvalidcode = checkcode(code)
            while isvalidcode:
                code = randomcode()
                isvalidcode = checkcode(code)
            data.code = code
            data.teacher_id = getLoginTeacherId(request.user.id)
            data.save()
            messages.add_message(request, messages.SUCCESS,
                                 'successfully created')
            return redirect(reverse_lazy('teacher_dashboard'))
        else:
            messages.add_message(request, messages.ERROR,
                                 'Sorry could not create right now. If fields are correct then maybe timeslot is not vacant')
            return redirect(reverse_lazy('teacher_dashboard'))


def teacher_profile(request):
    teacher = Teacher.objects.get(user = request.user)
    classes = Class.objects.filter(teacher_id = teacher.id).values("name")
    if (teacher.profile == ''):
        return render(request, "teacher/teacher_side_info.html", {"classes":classes, "teacher":teacher,
                                                            "photo":MEDIA_URL+"default.png"})
    photo_name = teacher.profile.url.split('/')[-1]
    return render(request, "teacher/teacher_side_info.html", {"classes":classes, "teacher":teacher,
                                                            "photo":PROFILE_URL+photo_name})

def teacher_store(request):
    content = {
        "teacher":Teacher.objects.get(user = request.user)
    }
    return render(request, "teacher/store.html", content)

def teacher_update(request):
    
    teacher = Teacher.objects.get(user = request.user)
    user = Account.objects.get(email = request.user)

    if (request.POST.get("name") != None and request.POST.get("name") != ''):
        teacher.name = request.POST.get("name")
    
    if (request.POST.get("contact") != None and request.POST.get("contact") != ''):
        teacher.contact_no = request.POST.get("contact")
    
    if (request.POST.get("department") != None and request.POST.get("department") != ''):
        teacher.department = request.POST.get("department")
    

    
    try:
   
        response  = request.FILES["photo"]
        
        photo_name = response.name
        img = cv2.imdecode(np.fromstring(response.read(), np.uint8), cv2.IMREAD_COLOR)
        resized_img = fp.image_resize(img)
        faceImg = fp.extract_face_from_frame(resized_img)
        if (len(faceImg)==0):
            
            return JsonResponse({
            "message":"Face is not detected in the photo",
            "status":False
            })
            
        faceEmbedding = fp.getFaceEmbeddingsFromImage(faceImg)
        
        for embedding_file in os.listdir(EMBEDDINGS_ROOT):
            knownEmbedding = fp.getEmbeddingsFromFile(os.path.join(EMBEDDINGS_ROOT,embedding_file))
            result = fp.compare_faces(faceEmbedding, knownEmbedding)[0]
            if (result):
                return JsonResponse({
                "message":"Profile already exists",
                "status":False
                })
        
        teacher.profile = request.FILES['photo']
        teacher.save()
        
        profile_path = os.path.join(PROFILE_ROOT, photo_name)
        cv2.imwrite(profile_path, faceImg)
        embedding_name =  "embeddings_"+randomcode(8)+".txt"
        embeddings_file = os.path.join(EMBEDDINGS_ROOT,embedding_name)
        with open(embeddings_file, 'w') as filehandle:
            for listitem in faceEmbedding[0]:
                filehandle.write('%s\n' % listitem)
        filehandle.close()
        user.embedding = embedding_name
        teacher.save()
    
    except:
        pass
   
    
    
    
    user.is_updated = True
    user.save()
    
    
    
    return JsonResponse({
        "message":"Updated",
        "status":True
    })
    
        