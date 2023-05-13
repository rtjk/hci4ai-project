import json
import pickle


main_dir="data/"
heatmaps_directory = main_dir + 'heatmaps/'
images_directory = main_dir + 'images/'

file = open(main_dir + 'confidence/confidence_p.pkl', 'rb')
confidence_p = pickle.load(file)
file.close()

file = open(main_dir + 'confidence/confidence_n.pkl', 'rb')
confidence_n = pickle.load(file)
file.close()

file = open(main_dir + 'embeddings/embeddings_p.pkl', 'rb')
embeddings_p = pickle.load(file)
file.close()

file = open(main_dir + 'embeddings/embeddings_n.pkl', 'rb')
embeddings_n = pickle.load(file)
file.close()


used_images = []
N_SIMILAR = 3
CONFIDENCE_THRESHOLD = 0.75

# inuput: json response from dialogflow
# output: variables representing the state of the conversation
def parse_response(result):
  page = result.current_page.display_name
  message = ''
  if result.response_messages:
    message = result.response_messages[0].text.text[0]
  user_wants_to_play = -1
  user_prediction = -1
  if result.parameters:
    user_wants_to_play = int(result.parameters['play-value'])
    if 'continue_playing-value' in result.parameters.keys():
        user_wants_to_play = int(result.parameters['continue_playing-value'])
    if 'user_guess' in result.parameters.keys():
        user_prediction = int(result.parameters['user_guess'])
  if result.match.event == 'sys.no-match-default':
     page = 'error'
  return page, message, user_wants_to_play, user_prediction

# inuput: json response from dialogflow
# output: object containing text and images to be displayed on the webpage
def handle_response(response):
    
    # a list of strings
    # some strings represents simple text to be printed
    # some other strings represent images (encoded in base64) to be displayed
    # text and images should appear on the webpage according to the list order
    webpage_data = []

    isSimilar = False

    page, message, user_wants_to_play, user_prediction = parse_response(response)

    if page == 'Play':
        if (user_wants_to_play == 1):
            webpage_data.append(get_new_image())
        elif (user_wants_to_play == 0):
            webpage_data.append('Goodbye')
            message = ''

    elif page == 'Guess' and user_prediction != -1:
        label = get_label()
        if (user_prediction == label):
            webpage_data.append('Correct!')
        else:
            webpage_data.append('Oops, you made a mistake')
        if (label == 1):
            webpage_data.append('This patient has pneumonia')
        else :
            webpage_data.append('This patient does not have pneumonia')

    elif page == 'HeatMap':
        webpage_data.append(get_heatmap())
    
    elif page == 'HeatMapSimilarity':
        webpage_data.append(get_heatmap())
        webpage_data.append('Here is a heatmap for our patient')
        webpage_data = webpage_data + get_n_heatmaps()

    elif page == 'Similarity':
        label = get_label()
        isSimilar = True

    elif page == 'Explainability':
        webpage_data = webpage_data + get_heatmap_explanation()

    if(message!=''):
        if(isSimilar):
              webpage_data = webpage_data + get_n_similar()
              webpage_data.append(message)
              if (label == 1):
                webpage_data.append('All showing presence of pneumonia')
                webpage_data.append('I can show you why they are similar or present a new patient')
              else:
                  webpage_data.append('All showing absence of pneumonia')
                  webpage_data.append('I can show you why they are similar or present a new patient')
        else:
           webpage_data.append(message)

    print('----')
    print(page)
    print(user_wants_to_play)
    print(user_prediction)
    print(used_images)
    print('----')
    return webpage_data

from random import randrange
import base64
import numpy as np
from scipy.spatial import distance
import json
import cv2

# output: an image (encoded in base64) that the user has yet to see
def get_new_image():

  binary_label = randrange(2) # 0 or 1
  label = 'p' if binary_label==1 else 'n'
  index = randrange(500) # a number between 0 and 499
  image = images_directory + label + '_' + str(index) + '.jpg'
  with open(image, 'rb') as img_file:
    base64_image = base64.b64encode(img_file.read())

  if(used_images and image == used_images[-1]):
    return get_new_image()
  else:
    used_images.append(image)
    return base64_image.__str__()

# output: the label for the current image
def get_label():
  binary_label = 1 if ('p' in used_images[-1].replace('.jpg', '')) else 0
  return binary_label

# output: the index for the current image
def get_index():
  image = used_images[-1]
  image = image.replace('.jpg', '')
  image = image.replace(images_directory, '')
  image = image[2:]
  return int(image)

# output: the heatmap (encoded in base 64) for the current image
def get_heatmap():
  heatmap = heatmaps_directory + 'h_' + used_images[-1].replace(images_directory, "")
  with open(heatmap, 'rb') as img_file:
    base64_heatmap = base64.b64encode(img_file.read())
  return base64_heatmap.__str__()

# output: a textual explanation of the heatmap
def get_heatmap_explanation():
  explanation = []
  explanation.append('The heatmap colors the image according to this scale, red means very important, blue means negligible')
  with open(main_dir + 'jet.png', 'rb') as img_file:
    base64_jet = base64.b64encode(img_file.read())
  explanation.append(base64_jet.__str__())
  area = reddest_area()
  if(area != 'error'):
    explanation.append('To make this diagnosis you should focus on the ' + area + ' area of the X-ray scan')
    confidence_text, confidence = get_confidence()
    confidence = np.interp(confidence, (0.5, 1), (0, 1)) # rescale confidence between 0 and 1
    explanation.append('The pneumonia detection algorithm has highlighted this area with ' + confidence_text + ' confidence' + ' (' + "{:.2f}".format((confidence)*100) + f'%)')
  return explanation

# output: binary classification from the CNN for the current image
def get_confidence():
  binary_label = get_label()
  if(binary_label == 1):
    confidence = confidence_p
    label = 'p'
  else:
    confidence = confidence_n
    label = 'n'
  index = get_index()
  level = confidence[index]
  if binary_label == 0:
    level = 1 - level
  # confidence level is between 0.5 and 1
  if level > CONFIDENCE_THRESHOLD:
    level_text = 'high'
  else:
    level_text = 'low'
  return level_text, level

# output: n images (encoded in base 64) similar to the current one
def get_n_similar():
  index = get_index()
  binary_label = get_label()
  if(binary_label == 1):
    embeddings = embeddings_p
    label = 'p'
  else:
    embeddings = embeddings_n
    label = 'n'
  target = embeddings[index]
  vectors = np.delete(embeddings, index, axis=0)
  distances = distance.cdist([target], vectors, "cosine")[0]
  min_indexes = distances.argsort()[:N_SIMILAR]
  img_arr = []
  image = used_images[-1]
  for i in min_indexes:
    with open(images_directory + label + '_' + str(i) + '.jpg', 'rb') as img_file:
      img_arr.append(base64.b64encode(img_file.read()).__str__())
      img_arr.append("{:.2f}".format((1-distances[i])*100) + f'% similar')
  return img_arr

# output: n heatmaps (encoded in base 64)
def get_n_heatmaps():
  index = get_index()
  binary_label = get_label()
  if(binary_label == 1):
    embeddings = embeddings_p
    label = 'p'
  else:
    embeddings = embeddings_n
    label = 'n'
  target = embeddings[index]
  vectors = np.delete(embeddings, index, axis=0)
  distances = distance.cdist([target], vectors, "cosine")[0]
  min_indexes = distances.argsort()[:N_SIMILAR]
  img_arr = []
  image = used_images[-1]
  for i in min_indexes:
    with open(heatmaps_directory + 'h_' + label + '_' + str(i) + '.jpg', 'rb') as img_file:
      img_arr.append(base64.b64encode(img_file.read()).__str__())
  return img_arr

# output: a textual explanation of the most relevant area of the heatmap
def reddest_area():
  position_text = ''
  # Load the image
  img = cv2.imread(heatmaps_directory + 'h_' + used_images[-1].replace(images_directory, ""))
  # Convert the image to HSV color space
  hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV) 
  # find the red points
  lower_red = np.array([0, 50, 50])
  upper_red = np.array([10, 255, 255])
  mask1 = cv2.inRange(hsv, lower_red, upper_red)
  lower_red = np.array([170, 50, 50])
  upper_red = np.array([180, 255, 255])
  mask2 = cv2.inRange(hsv, lower_red, upper_red)
  mask = cv2.bitwise_or(mask1, mask2)
  # get all non zero values
  coord=cv2.findNonZero(mask)
  coord = np.squeeze(coord)
  position = 'error'
  if coord.size > 2:
    average = [sum(x)/len(x) for x in zip(*coord)]
    MAX = 180 # image size
    step = MAX/3
    x = average[0]
    y = average[1]
    ####
    if(x <= step and y <= step):
      position = 'top left'
    elif(x <= step and y <= 2*step):
      position = 'left'
    elif(x <= step and y <= 3*step):
      position = 'bottom left'
    ####
    elif(x <= 2*step and y <= step):
      position = 'top'
    elif(x <= 2*step and y <= 2*step):
      position = 'central'
    elif(x <= 2*step and y <= 3*step):
      position = 'bottom'
    ####
    elif(x <= 3*step and y <= step):
      position = 'top right'
    elif(x <= 3*step and y <= 2*step):
      position = 'right'
    elif(x <= 3*step and y <= 3*step):
      position = 'bottom right'
  return position
