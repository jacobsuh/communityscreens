# communityscreens


## Repository Contents 

`process.py`

- Requires a `videos/` directory that contains the videos to be processed. `videos/` directory can have an directory sub-structure, but all videos must have the extension ".mkv".
- Produces frames at a specified interval using the `ffmpeg` command and places them in a directory called `staging/`
- Moves files from `staging/` to `images/` with url-safe file names to be published at `jacobysuh.github.io/communityscreens/images/<filename>`
- Produces `frames.yaml`, which is a YAML text files specifying the content of the `images` directory with metadata about each image. An example entry in the file is:
```
001-Community-S01E01-Pilot.jpg: # the file name of the frame in the images/ directory
  season: 01
  episode: 01
  name: Pilot
  include: true
```
one entry is included for each file in `images/`
