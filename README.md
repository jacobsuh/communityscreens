# communityscreens

Twitter Bot that posts screenshots from all 6 seasons of Community every 2 hours: [https://twitter.com/Community_Caps](https://twitter.com/Community_Caps)

## Running and Requirements

We developed this with Python 3.7. You should have the `ffmpeg` library installed on your system for processing frames.

You can install python package dependencies with the included `requirements.txt` file:
```bash
python -m pip install -r requirements.txt
```

## Scripts

`process.py` will process videos into thumbnails and place them into the `images/` directory with a URL-safe filename. Additionally, it will create the file `frames.yaml` that specifies the contents of `images/` and metadata about each frame. This script takes as arguments the directory containing the videos and the frequency with which to produce frames. Run `python process.py --help` for more details.

Example usage:
```
python process.py --input=videos/ --frames-per-second=14
```

Details:
- Requires a directory as input that contains the videos to be processed. This directory can have an directory sub-structure, but all videos must have the extension ".mkv".
- Produces frames at a specified interval using the `ffmpeg` command and places them in a directory called `staging/`
- Moves files from `staging/` to `images/` with url-safe file names to be published at `jacobysuh.github.io/communityscreens/images/<filename>`
- Produces `frames.yaml`, which is a YAML text files specifying the content of the `images` directory with metadata about each image. An example entry in the file is:
```
0001-Community-S01E01-Pilot.jpg: # the file name of the frame in the images/ directory
  season: 01
  episode: 01
  name: Pilot
  include: true
```
one entry is included for each file in `images/`.

`publish.py` uses the `tweepy` Python package to publish individual frames to our [Twitter page](https://twitter.com/Community_Caps). It uses the contents fo `frames.yaml` to select an image at random from `images/`. It then builds a tweet using the image selected and its associated metadata from `frames.yaml` and pushes it to Twitter.
