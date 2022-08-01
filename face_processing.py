from os import name as os_name
from os import getcwd, path
from PIL import Image
from numpy import asarray
from mtcnn.mtcnn import MTCNN
from numpy import expand_dims
from keras.models import load_model
import numpy as np
import cv2
import time
from sklearn.preprocessing import Normalizer

detector = MTCNN()
model = load_model(path.join(getcwd(), "models/model/facenet_keras.h5"))
print(model)
print('Loaded Model')

def image_resize(cv_img, k1 = 640, k2 = 480):
    x = cv_img.shape[0]
    y = cv_img.shape[1]
    if (x < y):
        x, y = y, x
    return cv2.resize(cv_img, (0, 0), fx = (k1/x), fy =k2/y)

def extract_face_from_file(filename, required_size=(160, 160)):
	image = Image.open(filename)
	image = image.convert('RGB')
	pixels = asarray(image)
	results = detector.detect_faces(pixels)
	x1, y1, width, height = results[0]['box']
	x1, y1 = abs(x1), abs(y1)
	x2, y2 = x1 + width, y1 + height
	face = pixels[y1:y2, x1:x2]
	image = Image.fromarray(face)
	image = image.resize(required_size)
	face_array = asarray(image)
	return face_array

def extract_face_from_frame(pixels, required_size=(160, 160)):
    results = detector.detect_faces(pixels)
    if (len(results)==1):  
        x1, y1, width, height = results[0]['box']
        x1, y1 = abs(x1), abs(y1)
        x2, y2 = x1 + width, y1 + height
        face = pixels[y1:y2, x1:x2]
        face_array = cv2.resize(face, required_size)
        
        return face_array   
    else:
        return []

def get_embedding(model, face_pixels):
	face_pixels = face_pixels.astype('float32')

	mean, std = face_pixels.mean(), face_pixels.std()
	face_pixels = (face_pixels - mean) / std
	samples = expand_dims(face_pixels, axis=0)
	yhat = model.predict(samples)
	return yhat[0]

def initiate_known_embed(filename):
    frame = cv2.imread(filename)
    face = extract_face_from_frame(frame)
    embed = get_embedding(model, face)
    in_encoder = Normalizer(norm='l2')
    norm_encod = in_encoder.transform([embed])
    return norm_encod

def getFaceEmbeddingsFromImage(face_img):
    embed = get_embedding(model, face_img)
    in_encoder = Normalizer(norm='l2')
    return in_encoder.transform([embed])

def face_distance(face_encodings, face_to_compare):
    if len(face_encodings) == 0:
        return np.empty((0))    
    probability = np.linalg.norm(face_encodings - face_to_compare, axis=1)
    print(probability)
    return probability

def compare_faces(known_face_encodings, face_encoding_to_check, tolerance=0.96):
    return (face_distance(known_face_encodings, face_encoding_to_check) <= tolerance)



def get_results_with_detected_face(face, known_embed):
    return compare_faces(known_embed, getFaceEmbeddingsFromImage(face))[0]

def initiate_embeddings_from_file(filename):
    frame = cv2.imread(filename)
    face = extract_face_from_frame(frame)
    embed = get_embedding(model, face)
    in_encoder = Normalizer(norm='l2')
    norm_encod = in_encoder.transform([embed])
    return norm_encod

def initiate_embeddings_from_array(frame):
    face = extract_face_from_frame(frame)
    embed = get_embedding(model, face)
    in_encoder = Normalizer(norm='l2')
    norm_encod = in_encoder.transform([embed])
    return norm_encod



def setEmbeddingsInFile(personpath, calculate_encodings = []):
    if (calculate_encodings == []):
        known_embed = initiate_known_embed(personpath)
    else:
        known_embed = calculate_encodings
    embeddings = known_embed[0]
    
    first_split = personpath.split('/')


    second_split = first_split[len(first_split)-1].split('.')
    filename = path+second_split[0]+'.txt'

    with open(filename, 'w') as filehandle:
        for listitem in embeddings:
            filehandle.write('%s\n' % listitem)

    filehandle.close()

    return second_split[0]+'.txt'

def getEmbeddingsFromFile(path):
    embed = []
    with open(path, 'r') as filehandle:
        for line in filehandle:
            currentPlace = line[:-1]
            embed.append(float(currentPlace))
    filehandle.close()
    return [embed]

# def compare_two_images(img_arr1, img_arr2):
#     img_arr1 = image_resize(img_arr1)
#     img_arr2 = image_resize(img_arr2)
#     return compare_faces(initiate_embeddings_from_array(img_arr1),
#                          initiate_embeddings_from_array(img_arr2))[0]


def getResults(frame, embedding_file_path):
    face = extract_face_from_frame(frame)
    if (len(face)==0):
        print("returning false")
        return False
    else:
        file_embedding = getEmbeddingsFromFile(embedding_file_path)
        frame_embedding = getFaceEmbeddingsFromImage(face)
        return (compare_faces(file_embedding, frame_embedding)[0])