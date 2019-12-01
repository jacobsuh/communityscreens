import subprocess
import glob
import os
import shutil
import yaml
import urllib.parse
import argparse

def find_all_video_files(path, extension="mkv"):
    print("Looking for video files in:", path)
    mkv_video_files = glob.glob(os.path.join(path, f"*.{extension}"))

    all_files = glob.glob(os.path.join(path, "*"))
    folders = [f for f in all_files if os.path.isdir(f)]
    num_folders = len(folders)

    if num_folders == 0:
        return mkv_video_files
    else:
        video_files_in_folders = []
        for folder in folders:
            video_files_in_folders.append(find_all_video_files(folder))

        return mkv_video_files + sum(video_files_in_folders, [])

def produce_frames(path, output_pattern, frames_per_second):
    command = f"ffmpeg -i {path} -vf fps=1/{frames_per_second} {output_pattern}"
    print(">", command)
    subprocess.call(command.split(" "))

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--output", "-o", help="The output directory for video frames.")
    parser.add_argument("--input", "-i", help="The directory containing video files to process.")
    parser.add_argument("--frames_per_second", "-f", help="How frequently to grab a frame in the video.")
    parser.add_argument("--remote_url", "-u", help="The base URL that the images we be available at.")
    parser.add_argument("--staging", "-s", default="staging", help="The staging directory to place images before they are put in the output directory.")

    args = parser.parse_args()

    output_path = args.output
    input_path = args.input
    staging_path = args.staging
    frames_per_second = args.frames_per_second
    remote_url = args.remote_url

    if not output_path:
        parser.error("Must pass directory for output with --output or -o.")
    if not output_path:
        parser.error("Must pass directory for input with --input or -i.")
    if not frames_per_second:
        parser.error("Must pass frames per second with --frames_per_second or -f.")
    if not remote_url:
        parser.error("Must pass remote url for images with --remote_url or -u")

    if not os.path.exists(input_path) and os.path.isdir(input_path):
        print(f"Error: folder {input_path} does not exist! Exiting...")
        exit(1)
    
    video_files = find_all_video_files(input_path)
    
    if not os.path.exists(staging_path):
        print("> mkdir", staging_path)
        os.makedirs(staging_path)
    
    if not os.path.exists(output_path):
        print("> mkdir", output_path)
        os.makedirs(output_path)

    frames_metadata_file = "frames.yaml"
    frames_metadata = {}
    if os.path.exists(frames_metadata_file):
        print(frames_metadata_file, "already exists. Reading data from it.")
        with open(frames_metadata_file, "r") as f:
            frames_metadata = yaml.safe_load(f)
    
    processing_metadata_file = "processing.yaml"
    processing_metadata = {}
    if os.path.exists(processing_metadata_file):
        print(processing_metadata_file, "already exists. Reading data from it.")
        with open(processing_metadata_file, "r") as f:
            processing_metadata = yaml.safe_load(f)
    else:
        processing_metadata['done'] = []

    for file in video_files:
        print("Processing file:", file)
        filename = os.path.basename(file)
        video_name, extension = os.path.splitext(filename)

        if filename in processing_metadata['done']:
            print("File already processed! Skipping...")
            continue

        video_name_split = video_name.split("_")

        # in format SxxEyy
        season_episode_encoding = video_name_split[1]
        season = season_episode_encoding[1:3]
        episode = season_episode_encoding[4:]
        epsiode_name = " ".join(video_name_split[2:])

        out_pattern = "%04d-" + video_name + ".jpg"
        # put frames in a staging location
        # let's us keep track of the output of a single produce_frames call
        out_location = os.path.join(staging_path, out_pattern)
        produce_frames(file, out_location, frames_per_second)
        
        frame_paths = glob.glob(os.path.join(staging_path, "*"))
        
        for frame_path in frame_paths:
            frame_name = os.path.basename(frame_path)

            # move frame to final location
            url_safe_frame_name = urllib.parse.quote_plus(frame_name)
            destination_path = os.path.join(output_path, url_safe_frame_name)
            print(f"> mv {frame_path} {destination_path}")
            shutil.move(frame_path, destination_path)

            # construct frame metadata
            frame_data = {}
            frame_data['name'] = epsiode_name
            frame_data['season'] = season
            frame_data['episode'] = episode
            frame_data['include'] = True
            frame_data['url'] = os.path.join(remote_url, url_safe_frame_name)

            frames_metadata[url_safe_frame_name] = frame_data
        
        processing_metadata['done'].append(filename)
        processing_metadata[filename] = {}
        processing_metadata[filename]['fps'] = frames_per_second

    with open(frames_metadata_file, "w") as f:
        f.write(yaml.safe_dump(frames_metadata))
    with open(processing_metadata_file, "w") as f:
        f.write(yaml.safe_dump(processing_metadata))

if __name__ == "__main__":
    main()

