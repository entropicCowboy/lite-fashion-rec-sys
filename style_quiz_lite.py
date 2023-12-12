import json
import os
from PIL import Image
import random
import requests
# from io import BytesIO
from pynput.keyboard import Key, Listener, Controller

# load keywords
f = open('keywords.json')
data = json.load(f)
f.close()
# load clusters
f = open('clusters.json')
global clusters
clusters = json.load(f)
f.close()
# load list of picture names
f = open('pic_names.json')
global pic_names
pic_names = json.load(f)
f.close()

ROOT_PATH = "https://github.com/entropicCowboy/fashion-rec-sys/blob/master/image_scraping/style_images/"
styles = {}
global status
global best_ratio
global best_style
best_ratio = -1

class Style:
    def __init__(self, name: str):
        self.name = name
        self.path = ROOT_PATH + self.name + "/"
        # a list of the pic names in the style's folder
        self.pics = pic_names[self.name]
        self.num_pics = len(self.pics) # the number of pics the style has in its folder
        self.pics_left = self.pics # the pics that haven't been shown
        self.num_pics_left = self.num_pics # the number of pics that haven't been shown
        self.ratio = 0
        self.has_pics = True
    
    """Picks random image that has not yet been shown from its stash"""
    def get_image(self) -> str:
        if self.has_pics == False:
            raise Exception("No images left to show")
        index = random.randint(0,self.num_pics_left-1)
        # decrement num pics left
        self.num_pics_left -= 1
        if self.num_pics_left == 0:
            self.has_pics = False
        # remove and return style pic
        return self.pics_left.pop(index)
    
    """Updates the style's ratio
        state: 1 if the user liked the image, -1 if they disliked the image"""
    def update_ratio(self, status:int) -> None:
        global best_ratio
        global best_style
        if status != 1 and status != -1:
            raise Exception("Status must be equal to 1 or -1")
        self.ratio += status/self.num_pics
        if self.ratio > best_ratio:
            best_ratio = self.ratio
            best_style = self.name
    
    """Updates the equilibrium based on the style's ratio and returns whether that style can be chosen for the user"""
    def equil_reached(self) -> bool:
        # if the style has 5 or less pictures, all must be liked by the user
        if self.num_pics < 6:
            if self.ratio == 1:
                return True
        # if the styles has less than 10 pictures, a greater majority must be liked by the user
        elif self.num_pics < 10:
            if self.ratio >= 0.7:
                return True
        else:
            if self.num_pics >= 0.5:
                return True
        return False
        
"""Used for detecting 'y' and 'n' key presses on a presented image"""
def on_press(key) -> None:
    global status
    try:
        k = key.char
        if k == 'y':
            status = 1
        elif k == 'n':
            status = -1
    except AttributeError:
        pass

"""Used for killing the listener for a presented image"""
def on_release(key):
    global status
    if key == Key.esc or status != 0:
        # Stop listener
        return False

"""Presents an image to the user, awaits their input, and updates the ratio of the style accordingly. Returns whether or not 
    the style has reached equilibium and can be chosen for the user"""
def present_image(style: Style) -> bool:
    response = requests.get(style.path + style.get_image() + "?raw=true", stream=True)
    img = Image.open(response.raw)
    img.show()
    #image = Image.open(BytesIO(response.content))
    #image = Image.open(style.path + style.get_image())
    #image.show()
    global status
    status = 0
    while(True):
        with Listener(
            on_press=on_press,
            on_release=on_release) as listener:
            listener.join()
        if status != 0:
            break
    img.close() # haven't figured out a way to actually close the window yet
    # Controller.press(Key.esc)
    # Controller.release(Key.esc)
    style.update_ratio(status)
    return style.equil_reached()

def initial_present():
    for cluster in new_clusters:
        num_styles = len(cluster)
        if num_styles < 1:
            print(f"no styles for cluster: {cluster}")
            continue
        index = random.randint(0,num_styles-1)
        rand_style = cluster[index]
        style = styles[rand_style]
        present_image(style)

def style_quiz():
    initial_present()
    initial_present()
    initial_present()
    print(f"Style: {best_style}, ratio: {best_ratio}")

for style_name in list(data.keys()):
    try:
        style = Style(style_name)
        # if there are photos in the file, add it to the list
        if style.num_pics > 0:
            styles[style_name] = style
    except:
        pass

new_clusters = []
for i in range(len(clusters)):
    new_clusters.append([])
    for style in clusters[i]:
        if style in styles:
            new_clusters[i].append(style)

# style_quiz()

