# Community Screencaps

Twitter Bot that posts screenshots from all 6 seasons of Community every 2 hours: [https://twitter.com/Community_Caps](https://twitter.com/Community_Caps)

## Running and Requirements

We developed this with Python 3.7. You should have the `ffmpeg` library installed on your system for processing frames.

You can install python package dependencies with the included `requirements.txt` file:
```bash
python -m pip install -r requirements.txt
```

## Scripts

`process.py` will process videos pulled from the directory specified by `--input` into a set of frames and place them into the directory specified with the `--output` argument with a URL-safe filename. Additionally, it will create the file `frames.yaml` that specifies metadata about the frames created. Additionally, one must specify a URL that the images will be published and avaialble at. Run `python process.py --help` for more details.

Example usage:
```
python process.py --input=videos/ --output=images/ --frames-per-second=14 --remote_url=https://jacobysuh.gitlab.io/community/images"
```

Details:
- Requires a directory that contains the videos to be processed passed as `--input`. This directory can have an directory sub-structure, but all videos must have the extension ".mkv".
- Requires a directory to place images into, specified with `--output`
- Produces frames at a specified interval using the `ffmpeg` command and places them in a directory called `staging/`
- Moves files from `staging/` to the output directory with url-safe file names
- Produces `frames.yaml`, which is a YAML text files specifying the content of the output directory with metadata about each image. An example entry in the file is:
```
0001-Community-S01E01-Pilot.jpg: # the file name of the frame in the images/ directory
  season: 01
  episode: 01
  name: Pilot
  include: true
  url: https://jacobysuh.gitlab.io/community/images/0001-Community_S01E01_Pilot.jpg
```
One entry is included for each file in the ouput directory.

`publish.py` uses the `tweepy` Python package to publish individual frames to our [Twitter page](https://twitter.com/Community_Caps). It uses the contents of `frames.yaml` to select an image at random from `images/`. It then builds a tweet using the image selected and its associated metadata from `frames.yaml` and pushes it to Twitter.
