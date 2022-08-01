#from silence_tensorflow import silence_tensorflow
#silence_tensorflow()
import cv2
import os
import numpy as np
from django.conf import settings
from .models import *
from django.utils import timezone
import pytz
#import face_processing as fp
import random
timezones = pytz.all_timezones
from threading import Thread
from lms.settings import MEDIA_ROOT
from datetime import datetime
from datetime import timedelta
from datetime import date

from class_.models import Class, ClassJoined, Stream, Comment, Room, Configuration, Attendance
from student.models import Student

face_detection = cv2.CascadeClassifier(os.path.join(
			settings.HAARCASCADE_DIR,'haarcascade_frontalface_default.xml'))
 

video_capture = None
image_size = (640, 480)
fps = 24.0 
font = cv2.FONT_HERSHEY_SIMPLEX
org = (20, 20)
fontScale = 0.7
color = (0, 255, 255)
thickness = 2
THRESH_SIZE = 1000


message = ""
current_detection = ""

def getInfoFromStatus(tuple, value):
    for pair in tuple:
        if (value in pair):
            return pair[1]
    
    return "No info fround from given value"

def generate(random_chars=12, alphabet="0123456789abcdefghijklmnopqrstABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    r = random.SystemRandom()
    return ''.join([r.choice(alphabet) for i in range(random_chars)])

def recognizePerson(image):
    global current_detection
    person_name = "Unknown"
    person_type = None
    identified = "unknown"
    p = Student.objects.all()
    img = fp.imageResize(image)
    cord, faceImg = fp.extract_face_from_frame(img, cord = True)
    if (len(faceImg)==0):
        return "No face is found"
    saved_filename = generate()+'.png'
    
    cv2.imwrite(settings.REALTIME_DIR+saved_filename, faceImg)
    faceEmbedding = fp.getFaceEmbeddingsFromImage(faceImg)
    for i in range(len(p)):
        print(p[i].full_name)
        knownEmbedding = fp.getEmbeddingsFromFile(settings.EMBEDDINGS_DIR+p[i].embedding)
        result = fp.compare_faces(faceEmbedding, knownEmbedding)[0]
        if (result):
            person_type = p[i]
            person_name = p[i].full_name
            identified = "known"
            
            break
	
        
    #Save attendance in Database
    timestamp_intruder = (timezone.now()).strftime("%m/%d/%Y %H:%M:%S")
    message =  "Student has been identified as " + person_name+" at "+timestamp_intruder
    return message
            
class VideoCamera(object):
    
	def __init__(self, link, code = None):
		self.video =  cv2.VideoCapture(0)
		self.code = None
		self.subject_class  = None
		self.students = None
		self.first_time = None
		self.second_time = None
		self.threhsold_time = None

	def set_database(self, code):
		self.code = code
		self.subject_class = Class.objects.get(code = code)
		self.students = ClassJoined.objects.filter(class_join_id = self.subject_class.id)
		self.first_time = self.subject_class.timing.start_time	
		delta = timedelta(minutes= (Configuration.objects.first()).class_duration)
		self.second_time = (datetime.combine(date(1,1,1),self.first_time) + delta).time()
		delta = timedelta(minutes= (Configuration.objects.first()).attendance_duration)
		self.threshold_time = (datetime.combine(date(1,1,1),self.first_time) + delta).time()
		
  
	def get_frame(self):
		global message
		global current_detection
  
		if (True
      		#(datetime.now().time() >= self.first_time and datetime.now().time() <= self.second_time)
			#	and
			#(self.subject_class.day == datetime.today().strftime('%A').lower()[0:3])
      		):
			success, image = self.video.read()
			gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
			faces_detected = face_detection.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
			for (x, y, w, h) in faces_detected:
				cv2.rectangle(image, pt1=(x, y), pt2=(x + w, y + h), color=(255, 0, 0), thickness=2)

			if (len(faces_detected) > 0):
				current_detection = "Last Motion detected at "+ (datetime.now()).strftime("%m/%d/%Y %H:%M:%S")
				if (faces_detected[0][3]>=THRESH_SIZE):
					for i in range(len(self.students)):
						img_url = str(self.students[i].student.profile)
						student_img_arr = cv2.imread(os.path.join(MEDIA_ROOT, img_url ))
						result = fp.compare_images(student_img_arr, image)
						if (result):
							current_date = datetime.now()
							start_day = datetime(current_date.year, current_date.month,
                            					current_date.day, 0, 0, 0, 0
                            						)
							end_day = datetime(current_date.year, current_date.month,
                            					current_date.day, 23, 59, 59, 999999
                            						)
							is_marked = Attendance.objects.filter(student_id = self.students[i].student.id,
                                 					 timestamp__range = (start_day, end_day))
							if (len(is_marked) > 0):
								message = "Already done"
							
							#elif (datetime.now().time() <= self.threshold_time):
							elif(True):
								a = Attendance(class_room_id = self.students[i].class_join.id,
                      						student_id = self.students[i].student.id,
                            				is_present = True,
                                			timestamp = datetime.now())
								a.save()
								message = "In Last, "+self.students[i].student.name+" is recognized with time"
							else:
								message = "In Last, "+self.students[i].student.name+" is late. Not marked"
							break
					#message = "Person is not recognized"
							
			timestamp = (datetime.now()).strftime("%m/%d/%Y %H:%M:%S")
			frame = cv2.putText(image, timestamp+" Class Attendance", org, font, 
                   			fontScale, color, thickness, cv2.LINE_AA)
			frame = cv2.putText(image, current_detection , (20,40), font, 
                   			fontScale, (0, 0, 255), thickness, cv2.LINE_AA)
			frame = cv2.putText(image, message, (20,60), font, 
                   			fontScale, (124, 200, 0), thickness, cv2.LINE_AA)
   
			ret, jpeg = cv2.imencode('.jpg', frame)
		

		else:
			frame = cv2.imread(os.path.join(MEDIA_ROOT, "no_class.jpg"))
			frame = cv2.resize(frame, (600,600))
			ret, jpeg = cv2.imencode('.jpg', frame)
		return jpeg.tobytes()
			

	def stop_frame(self):
		self.video = None
  
	def start_frame(self):
		self.video =  cv2.VideoCapture(self.link)

