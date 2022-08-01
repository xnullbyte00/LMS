from django.contrib import admin
from .models import (Attendance, Class,ClassJoined,Comment,
                     Configuration, Recording,Stream,
                     Room, TeacherAttendance, Schedule)
# Register your models here.
admin.site.register([Class,Comment,Stream,ClassJoined,
                     Room, Configuration, 
                     Attendance, Recording, TeacherAttendance, Schedule])
