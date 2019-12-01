import tweepy
import yaml
import random
import requests
import os

def pick_image ():

	# Download YAML file
	request = requests.get("https://jacobysuh.github.io/communityscreens/frames.yaml")
	open("frames.yaml", 'wb').write(request.content)
	
	# Get metadata
	with open("frames.yaml", "r") as stream:
		data_loaded = yaml.safe_load(stream)
	list_of_frames = data_loaded.keys()
	chosen_frame = random.choice(list(list_of_frames))

	metadata =  data_loaded[chosen_frame]
	season = metadata.get("season")
	episode = metadata.get("episode")
	name = metadata.get("name")
	include = metadata.get("include")

	tweet_text = "From S" + str(season) + "E" + str(episode) + ": " + name + " #CommunityLivesOn"

	if include == True:
		publish(chosen_frame, tweet_text)
	else:
		pick_image()

def publish (chosen_frame, tweet_text):

	# Authenticate to Twitter
	auth = tweepy.OAuthHandler("XXXXXXXXXXXXXXXXXX", 
	    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
	auth.set_access_token("XXXXXXXXXXXXXXXXXX-XXXXXXXXXXXXXXXXXX", 
	    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
	api = tweepy.API(auth)

	# Download picture and tweet
	image_url = "https://jacobysuh.github.io/communityscreens/images/" + chosen_frame
	request = requests.get(image_url, stream=True)
	if request.status_code == 200:
		with open(chosen_frame, 'wb') as image:
			for chunk in request:
				image.write(chunk)
		api.update_with_media(chosen_frame, status=tweet_text)
		os.remove(chosen_frame)
	else:
		print("Image cannot be downloaded")

pick_image()