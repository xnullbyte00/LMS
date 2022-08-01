from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from class_.models import Class, ClassJoined
from django.db.models import Q
from .models import Student
from django.contrib import messages
import cv2
import os
import face_processing as fp
import numpy as np
from lms.settings import EMBEDDINGS_ROOT, PROFILE_ROOT
import string
import random
from account.models import Account
# Create your views here.

def randomcode(length = 5):
    code = ''
    letters = string.ascii_letters + string.digits
    for i in range(length):
        code = code+str(random.choice(letters))
    return code

def getLogedInStudentId(user_id):
    s = Student.objects.get(user_id=user_id)
    return s.id


class StudentView(View):
    template_name = 'student/dashboard.html'

    @method_decorator(login_required, 'signin')
    def get(self, request, *args, **kwargs):
        all_id = [x.class_join_id for x in ClassJoined.objects.filter(
            student_id=getLogedInStudentId(request.user.id), is_accept=True)]
        all_class = Class.objects.filter(id__in=all_id)
        if request.user.is_firstLogin:
            return redirect(reverse_lazy('password_change'))
        else:
            return render(request, self.template_name, {'class': all_class})


def searchclass(reqeust):
    if reqeust.method == 'GET':
        key = reqeust.GET.get('key')
        s = Class.objects.filter(Q(name__contains=key) | Q(code=key))
        c = ClassJoined.objects.filter(student_id=getLogedInStudentId(
            reqeust.user.id)).only('class_join_id')
        class_id = [x.id for x in c]
        context = {
            'result': s,
            'key': key,
            'class_id': class_id,
        }
        return render(reqeust, 'student/search.html', context)
    else:
        return redirect(reverse_lazy('student_dashbaord'))


login_required(login_url='signin')


def classJoin(request, class_id):
    if request.method == 'GET':
        try:
            c = ClassJoined()
            c.student_id = getLogedInStudentId(request.user.id)
            c.class_join_id = class_id
            c.save()
            messages.add_message(request, messages.SUCCESS,
                                 'Your request to join the class has been sent')
            return redirect(reverse_lazy('student_dashbaord'))
        except Exception as e:
            messages.add_message(
                request, messages.ERROR, 'sorry we could not sent your request right now : '+str(e))
            return redirect(reverse_lazy('student_dashbaord'))
    else:
        return redirect(reverse_lazy('student_dashbaord'))

def student_profile(request):
    student = Student.objects.get(user = request.user)
    classes = ClassJoined.objects.filter(student_id = student.id).values("class_join__name")
    
    return render(request, "student/student_side_info.html", {"student":student, 
                                                              "classes":classes})


def student_store(request):
    content = {
        "student":Student.objects.get(user = request.user)
    }
    return render(request, "student/store.html", content)

def student_update(request):
    
    student = Student.objects.get(user = request.user)
    user = Account.objects.get(email = request.user)
    
    if (request.POST.get("name") != None and request.POST.get("name") != ''):
        student.name = request.POST.get("name")
    
    if (request.POST.get("contact") != None and request.POST.get("contact") != ''):
        student.contact_no = request.POST.get("contact")
    
    

    
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
        
        student.profile = request.FILES['photo']
        student.save()
        
        profile_path = os.path.join(PROFILE_ROOT, photo_name)
        cv2.imwrite(profile_path, faceImg)
        embedding_name =  "embeddings_"+randomcode(8)+".txt"
        embeddings_file = os.path.join(EMBEDDINGS_ROOT,embedding_name)
        with open(embeddings_file, 'w') as filehandle:
            for listitem in faceEmbedding[0]:
                filehandle.write('%s\n' % listitem)
        filehandle.close()
        user.embedding = embedding_name
        student.save()
    
    except:
        pass
   
    
    
    
    user.is_updated = True
    user.save()
    
    
    
    return JsonResponse({
        "message":"Updated",
        "status":True
    })