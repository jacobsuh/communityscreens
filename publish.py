import tweepy
import yaml
import random
import requests
import os
import json

def main(event, context):
    # TODO implement
    pick_image()
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
    
def pick_image ():

	# Download YAML file
	frames_data_url = "https://jacobysuh.github.io/communityscreens/frames-new.yaml"
	print("Downloading frame data from:", frames_data_url)
	request = requests.get(frames_data_url)
	if request.status_code != 200:
		print("Error: Got status code:", request.status_code)
		exit()

	frames_write_location = "/tmp/frames.yaml"
	print("Saving frame data to disk at:", frames_write_location)
	open(frames_write_location, 'wb').write(request.content)
	
	# Get metadata
	with open(frames_write_location, "r") as stream:
		data_loaded = yaml.safe_load(stream)
	list_of_frames = data_loaded.keys()
	chosen_frame = random.choice(list(list_of_frames))
	print("Chose image:", chosen_frame)

	metadata =  data_loaded[chosen_frame]
	season = metadata.get("season")
	episode = metadata.get("episode")
	name = metadata.get("name")
	include = metadata.get("include")
	image_url = metadata.get("url")

	tweet_text = "From S" + str(season) + "E" + str(episode) + ": " + name + " #CommunityLivesOn"

	if include == True:
		publish(chosen_frame, tweet_text, image_url)
	else:
		print("Image should not be published, selecting again...")
		pick_image()

def publish (chosen_frame, tweet_text, image_url):
	# Authenticate to Twitter
	auth = tweepy.OAuthHandler("XXXXXXXXXXXXXXXXXXX", 
	    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
	auth.set_access_token("XXXXXXXXXXXXXXXXXXX-XXXXXXXXXXXXXXXXXXXXXXXXXXX", 
	    "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
	api = tweepy.API(auth)

	# Download picture and tweet
	image_location = "/tmp/" + chosen_frame
	
	if not image_url:
		print("Error: No image url found!")
		exit()
	
	print("Downloading image from:", image_url)
	request = requests.get(image_url, stream=True)
	if request.status_code == 200:
		with open(image_location, 'wb') as image:
			for chunk in request:
				image.write(chunk)
		
		print("Publishing image with status:", tweet_text)
		api.update_with_media(image_location, status=tweet_text)		
		os.remove(image_location)
	else:
		print("Image cannot be downloaded")
	
if __name__ == "__main__":
	main(None, None)
