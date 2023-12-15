import json
from PIL import Image
import random
import requests
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
# load recommendations
f = open('recommendations.json')
global recommendations_list
recommendations_list = json.load(f)
f.close()
# load recommendations
f = open('returndata.json')
global final_data
return_data = json.load(f)
f.close()

# pulls style images from the public githhub repo
ROOT_PATH = "https://github.com/entropicCowboy/fashion-rec-sys/blob/master/image_scraping/style_images/"
styles = {}
global total_style_names
global total_num_styles
global status
global any_equil_reached
any_equil_reached = False
global best_ratio
best_ratio = -10
global best_style
best_style = ""
global liked_styles
liked_styles = set()

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
    def update_ratio(self, status:float) -> None:
        global best_ratio
        global best_style
        global liked_styles

        self.ratio += status/self.num_pics
        if status == 1:
            liked_styles.add(self)
        if self.ratio > best_ratio:
            best_ratio = self.ratio
            best_style = self.name

    """For an inputed style and status, updates similar styles' equilibriums according to that status"""
    def update_similar_ratios(self, status:float) -> None:
        # allow the style to have an effect on similar styles
        for style_name in recommendations_list[self.name]:
            try:
                styles[style_name].update_ratio(status/2)
            except:
                pass
    
    """Updates the equilibrium based on the style's ratio and returns whether that style can be chosen for the user"""
    def equil_reached(self) -> bool:
        global any_equil_reached
        global best_style
        global best_ratio
        # if any style has reached the defined equilibriums, update best style and ratio
        # if the style has 5 pics, all but 1 must be liked; if it has < 5, all must be liked
        if self.num_pics < 6:
            if self.ratio >= 0.8:
                any_equil_reached = True
                best_ratio = self.ratio
                best_style = self.name
                print("1st equil reached")
                return True
        else:
            if self.ratio > 0.5:
                any_equil_reached = True
                best_ratio = self.ratio
                best_style = self.name
                print("3rd equil reached")
                return True
        return False
    

        
"""Used for detecting 'y' and 'n' key presses on a presented image"""
def on_press(key) -> None:
    global status
    try:
        k = key.char
        if k == 'y':
            status = 1.0
        # disliking an image has a smaller effect on the equil than liking one
        elif k == 'n': 
            status = -0.5
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
    image = Image.open(response.raw)
    image.show()
    global status
    status = 0
    while(True):
        with Listener(
            on_press=on_press,
            on_release=on_release) as listener:
            listener.join()
        if status != 0:
            break
    image.close() # haven't figured out a way to actually close the window yet
    # Controller.press(Key.esc)
    # Controller.release(Key.esc)
    style.update_ratio(status)
    style.update_similar_ratios(status)
    return style.equil_reached()


"""For each of the 20 total clusters, it randomly selects a style from the cluster, and a random image from the style,
then presents it to the user"""
def initial_present():
    for cluster in new_clusters:
        num_styles = len(cluster)
        if num_styles < 1:
            continue
        index = random.randint(0,num_styles-1)
        rand_style = cluster[index]
        style = styles[rand_style]
        present_image(style)


"""Prints the user's top style, and its description, and next top 5 styles along with a short message"""
def print_results():
    print("\n******************************************************\n")
    print(f"Style: {best_style}")

    # print description
    print("Description: ")
    for desc in return_data[best_style]["descriptions"]:
        print(desc)

    # print related aesthetics if there are any
    aesthetics = return_data[best_style]["rel_aesthetics"]
    if aesthetics:
        print("\nRelated aesthetics: ")
        print(", ".join(aesthetics))
    
    # print colors
    colors = return_data[best_style]["key_colors"]
    if colors:
        print("\nKey colors: ")
        print(", ".join(colors))
    
    # print brands
    brands = return_data[best_style]["brands"]
    if brands:
        print("\nKey brands: ")
        print(", ".join(brands))
    
    # print next top 5 styles
    print("\nDoesn't seem accurate? Here are your next top 5 styles:\n")
    top_styles = []
    for style in liked_styles:
        top_styles.append((style.ratio, style.name))
    counter = 1
    for style in sorted(top_styles, reverse=True)[1:6]:
        print(f"{counter}. {style[1]}")
        counter += 1

    print("\nNone of those sound like you? Since there are so many styles, part of")
    print("this quiz is based on luck, so you can always try taking it again to see")
    print("if you get a style that fits yours better.")
        

"""Has the sole purpose of displaying the introduction page"""
def show_intro():
    image = Image.open("../tutorial/intro.png")
    image.show()
    global status
    status = 0
    while(True):
        with Listener(
            on_press=on_press,
            on_release=on_release) as listener:
            listener.join()
        if status != 0:
            break

"""The style quiz: begins with showing the user an image describing the quiz they are about to take, then presents them with an 
image from each cluster 5 times, it will then either continue calling initial_present or begin showing them images based on 
what images they have liked or disliked until an equilibium is reached or the cap # of rounds exceeded"""
def style_quiz():
    global best_style

    show_intro()

    # present a photo from each cluster twice
    for _ in range(5):
        initial_present
    # if user has not liked any photos, keep presenting from each cluster
    while best_ratio <= 0:
        initial_present()
    
    rounds = 0
    while (any_equil_reached == False and rounds < 20):
        # if liked photo was a fluke (user doesn't like best_style)
        if best_ratio <= 0:
            initial_present()
        # generate 5 styles based on best_style for next images to present
        recommendations = (recommendations_list[best_style])
        recommendations.append(best_style)
        # add in a random style just for fun
        index = random.randint(0,total_num_styles-1)
        recommendations.append(total_style_names[index])
        # present a pic from each style
        for style_name in recommendations:
            try:
                style = styles[style_name]
                if style.has_pics:
                    present_image(style)
            except:
                pass
        rounds += 1
    
    # tell user they're done with the quiz
    image = Image.open("../tutorial/ending-pic.png")
    image.show()
    image.close()

    # uncomment for more information
    # if any_equil_reached == False:
    #     print(f"{rounds} rounds hit--no equil")

    print_results()
    

    
    

# set up styles
for style_name in list(data.keys()):
    try:
        style = Style(style_name)
        # if there are photos in the file, add it to the list
        if style.num_pics > 0:
            styles[style_name] = style
    except:
        # print(f"No folder: {style_name}")
        pass

# update global variables
total_style_names = list(styles.keys())
total_num_styles = len(total_style_names)

new_clusters = []
for i in range(len(clusters)):
    new_clusters.append([])
    for style in clusters[i]:
        if style in styles:
            new_clusters[i].append(style)

style_quiz()