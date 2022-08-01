#from silence_tensorflow import silence_tensorflow
#silence_tensorflow()
import cv2
import os
import numpy as np
from django.conf import settings

from face_processing import getResults
from .models import *
from account.models import Account
from django.utils import timezone
import pytz
timezones = pytz.all_timezones
from threading import Thread
from lms.settings import MEDIA_ROOT, EMBEDDINGS_ROOT
from datetime import datetime
from datetime import timedelta
from datetime import date
from random import random

from class_.models import (Class, ClassJoined, Stream, 
                           Comment, Room, Configuration, 
                           Attendance, TeacherAttendance)
from student.models import Student

face_detection = cv2.CascadeClassifier(os.path.join(
			settings.HAARCASCADE_DIR,'haarcascade_frontalface_default.xml'))
 

video_capture = None
font = cv2.FONT_HERSHEY_SIMPLEX
org = (20, 20)
fontScale = 0.5
color = (0, 255, 255)
thickness = 2

       

        
class VideoCamera(object):
    
	def __init__(self, link, code = None):
		self.video =  cv2.VideoCapture(link)
		self.code = None
		self.subject_class  = None
		self.students = None
		self.first_time = None
		self.second_time = None
		self.threhsold_time = None
		self.message = ""
		self.frame = cv2.imread(os.path.join(MEDIA_ROOT, "no_class.jpg"))
		self.frame = cv2.resize(self.frame, (600,600))
		self.flag_raised = False
		self.timestamp_message = ""
		self.recognition_message = ""
  
	@staticmethod
	def random_color():
		return int(random()*255+1)

	@staticmethod
	def get_whole_day():
		current_date = datetime.now()
		start_day = datetime(current_date.year, current_date.month,
													current_date.day, 0, 0, 0, 0
														)
		end_day = datetime(current_date.year, current_date.month,
					current_date.day, 23, 59, 59, 999999)
		return start_day, end_day


	def set_database(self, code):
		self.code = code
		self.subject_class = Class.objects.get(code = code)
		self.students = ClassJoined.objects.filter(class_join_id = self.subject_class.id)
		self.first_time = self.subject_class.timing.start_time	
		delta = timedelta(minutes= (Configuration.objects.first()).class_duration)
		self.second_time = (datetime.combine(date(1,1,1),self.first_time) + delta).time()
		delta = timedelta(minutes= (Configuration.objects.first()).attendance_duration)
		self.threshold_time = (datetime.combine(date(1,1,1),self.first_time) + delta).time()
  
	def get_embeddings_list(self):
		embeddings_list = []
		if (self.students.count == 0):
			return embeddings_list
		embeddings_list.append(os.path.join(EMBEDDINGS_ROOT,
											self.students[0].class_join.teacher.user.embedding))
		
		for student_joined in self.students:
			embeddings_list.append(os.path.join(EMBEDDINGS_ROOT,
												student_joined.student.user.embedding))
		return embeddings_list
    
	
 
	def processing(self):
		self.flag_raised = True
		gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
		faces_detected = face_detection.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
		self.message = ("Detected persons are: "+str(len(faces_detected)))
		for (x, y, w, h) in faces_detected:
			cv2.rectangle(self.frame, pt1=(x, y), pt2=(x + w, y + h), 
				color=(VideoCamera.random_color(), 
           			   VideoCamera.random_color(),
                 		VideoCamera.random_color()), thickness=2)
		embeddings_list = self.get_embeddings_list()
		for person_face in faces_detected:
			
			if (person_face[3] > Configuration.objects.first().threshold_pixels):
				for embedding in embeddings_list:
					crop_image = self.frame[person_face[1]:person_face[1]+person_face[3], 
									person_face[0]:person_face[0]+person_face[2]]
					old_message = self.recognition_message
					self.recognition_message = "Recognition in the process..."
					result = getResults(crop_image, embedding)
					if (result):
						user = Account.objects.get(embedding = 
								embedding.split(EMBEDDINGS_ROOT)[1][1:])
						
						embeddings_list.remove(embedding)
						if (user.is_student):
							self.student_attendance(user.id)
							
						elif (user.is_teacher):
							self.teacher_attendance(user.id)
							
						break
					else:
						self.recognition_message = old_message
		timestamp = (datetime.now()).strftime("%m/%d/%Y %H:%M")
		self.timestamp_message = timestamp+" Class Attendance"
		
		self.flag_raised = False
  
  
	def get_frame(self):
  
		if (
      		(datetime.now().time() >= self.first_time and datetime.now().time() <= self.second_time)
				and
			(self.subject_class.day == datetime.today().strftime('%A').lower()[0:3])
      		):
			success, self.frame = self.video.read()
   
			if (not self.flag_raised):
				Thread(target = self.processing, args = (), daemon = True).start()

			self.frame = cv2.putText(self.frame, self.message, (20,50), font, 
				0.5, (124, 200, 0), thickness, cv2.LINE_AA)
			self.frame = cv2.putText(self.frame, self.recognition_message, (20,70), font, 
				0.5, (186, 156, 255), thickness, cv2.LINE_AA)
								
			self.frame = cv2.putText(self.frame, self.timestamp_message, org, font, 
						fontScale, color, thickness, cv2.LINE_AA)
			
			try:
				ret, jpeg = cv2.imencode('.jpg', self.frame)
			except:
				temp_frame = cv2.imread(os.path.join(MEDIA_ROOT, "no_class.jpg"))
				temp_frame = cv2.resize(self.frame, (600,600))
				ret, jpeg = cv2.imencode('.jpg', )
		

		else:
			self.frame = cv2.imread(os.path.join(MEDIA_ROOT, "no_class.jpg"))
			self.frame = cv2.resize(self.frame, (600,600))
			ret, jpeg = cv2.imencode('.jpg', self.frame)
		return jpeg.tobytes()

	def student_attendance(self, user_id):
		student = Student.objects.get(user_id = user_id)
		start_day, end_day = VideoCamera.get_whole_day()
		is_marked = Attendance.objects.filter(
					student_id = student.id,
					timestamp__range = (start_day, end_day))
		
		
		if (len(is_marked) > 0):
			print("in already done")
			self.recognition_message = "Student attendance already done" 
		
		elif(datetime.now().time() <= self.threshold_time):
			print("in elif")
			a = Attendance(class_room_id = self.subject_class.id,
						student_id = student.id,
						is_present = True,
						timestamp = datetime.now())
			a.save()
			self.recognition_message = "In Last, Student: "+student.name+" is recognized with time"
		else:
			print("in else")
			self.recognition_message = "In Last, Student: "+student.name+" is late. Not marked"
			
	def teacher_attendance(self, user_id):     
		teacher = Teacher.objects.get(user_id = user_id)
		start_day, end_day = VideoCamera.get_whole_day()
		is_marked = TeacherAttendance.objects.filter(
					class_room_id = self.subject_class.id,
					timestamp__range = (start_day, end_day))
		if (len(is_marked) > 0):
			self.recognition_message = "Teacher attendance already done"
		else:
			t_a = TeacherAttendance(class_room_id = self.subject_class.id,
						timestamp = datetime.now())
			t_a.save()
			self.recognition_message= "In Last, Teacher: "+teacher.name+" is recognized with time"
   
   
	def stop_frame(self):
		self.video = None
  
	def start_frame(self):
		self.video =  cv2.VideoCapture(self.link)

