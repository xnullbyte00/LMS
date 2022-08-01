
from cv2 import threshold
from django.db import models
from pytz import timezone
from teacher.models import Teacher
from student.models import Student
from account.models import Account
import datetime
from random import random
# Create your models here.




class Room(models.Model):
    name = models.CharField(max_length=50, default = "A13")
    camera = models.IntegerField(unique=True, default = 53992178)
    link = models.CharField(max_length=200, unique=True, default = "rtsp://lms_camera:Vamos4185@192.168.8.104")
    def __str__(self):
       return self.name
    
class Schedule(models.Model):
    start_time = models.TimeField()  
    def __str__(self):
        return self.start_time.strftime("%H:%M:%S")  
class Class(models.Model):
    
    
    DAYS = (
        ('mon',  'Monday'),
        ('tue',  'Tuesday'),
        ('wed',  'Wednesday'),
        ('thu',  'Thursday'),
        ('fri',  'Friday'),
    )
    
    
    name = models.CharField(max_length=100)
    room = models.ForeignKey('Room', on_delete=models.CASCADE, default = 1)
    department = models.CharField(max_length=150,null=True,blank=True)
    code = models.CharField(max_length=10,unique=True)
    teacher = models.ForeignKey(Teacher,on_delete=models.CASCADE)
    timing = models.ForeignKey(Schedule, on_delete=models.CASCADE, default=1)
    day = models.CharField(max_length=3, choices=DAYS, default='mon')
    class Meta:
        unique_together = (('timing', 'day', 'room'),)

    def __str__(self):
        return self.name

class Attendance(models.Model):
    class_room = models.ForeignKey('Class', on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    is_present = models.BooleanField(default = False)
    timestamp = models.DateTimeField()
    
    def __str__(self):
        if (self.is_present):
            status = "present"
        else:
            status = "absent"
        return self.student.name +" was "+status+ " at "+self.class_room.name +" class on "+self.timestamp.strftime("%H:%M:%S %d/%m/%Y")
    
class TeacherAttendance(models.Model):
    class_room = models.ForeignKey(Class, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    
    def __str__(self):
        return self.class_room.teacher.name+" has started class of "+self.class_room.name+" at "+self.timestamp.strftime("%H:%M:%S %d/%m/%Y")
        
    

class ClassJoined(models.Model):
    student = models.ForeignKey(Student,on_delete=models.CASCADE)
    class_join = models.ForeignKey(Class,on_delete=models.CASCADE)
    is_accept = models.BooleanField(default=False)

    def __str__(self):
        return self.student.name
    class Meta:
        db_table = 'class_join'
        unique_together = ('student','class_join',)


class Stream(models.Model):
    content = models.TextField()
    file = models.FileField(upload_to='stream/')
    class_stream = models.ForeignKey(Class,on_delete=models.CASCADE)

    def __str__(self):
        return self.class_stream.name

class Recording(models.Model):
    class_room = models.ForeignKey(Class, on_delete=models.CASCADE, null=True, blank=True)
    video = models.CharField(max_length=100, default = "initial.mp4", unique=True)
    timestamp = models.DateTimeField(unique=True)
    def __str__(self):
        return self.video

class Comment(models.Model):
    comment = models.TextField()
    stream = models.ForeignKey(Stream,on_delete=models.CASCADE)
    user = models.ForeignKey(Account,on_delete=models.CASCADE)

    def __str__(self):
        return self.user.email
    
class Configuration(models.Model):
    class_duration = models.IntegerField(default = 120)
    attendance_duration = models.IntegerField(default=20)
    uploading_allowed = models.BooleanField(default=False)
    uploading_time = models.IntegerField(default=30)
    threshold_pixels = models.IntegerField(default=600)
    
    def __str__(self):
        
        uploading = "permitted."
        if (not self.uploading_allowed):
            uploading = "not "+uploading
            
        return "Class duration: "+str(self.class_duration/60)+\
            " hours | Attendance duration: "+str(self.attendance_duration)+\
                " minutes | Uploading is "+uploading

    
    
    
    

