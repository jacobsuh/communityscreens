import tweepy
import yaml
import random
import requests
import os
import json

def lambda_handler(event, context):
    # TODO implement
    pick_image()
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
    
def pick_image ():

	# Download YAML file
	request = requests.get("https://jacobysuh.github.io/communityscreens/frames.yaml")
	open("/tmp/frames.yaml", 'wb').write(request.content)
	
	# Get metadata
	with open("/tmp/frames.yaml", "r") as stream:
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
	auth = tweepy.OAuthHandler("XXXXXXXXXXXXXXXXXXX", 
	    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
	auth.set_access_token("XXXXXXXXXXXXXXXXXXX-XXXXXXXXXXXXXXXXXXXXXXXXXXX", 
	    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
	api = tweepy.API(auth)

	# Download picture and tweet
	image_url = "https://jacobysuh.github.io/communityscreens/images/" + chosen_frame
	image_location = "/tmp/" + chosen_frame
	
	request = requests.get(image_url, stream=True)
	if request.status_code == 200:
		with open(image_location, 'wb') as image:
			for chunk in request:
				image.write(chunk)
		
		api.update_with_media(image_location, status=tweet_text)		
		os.remove(image_location)
	else:
		print("Image cannot be downloaded")