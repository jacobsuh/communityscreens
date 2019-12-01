import subprocess
import glob
import os
import shutil
import yaml
import urllib.parse

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
    videos_path = "videos"
    if not os.path.exists(videos_path) and os.path.isdir("videos"):
        print("Error: folder 'videos' does not exist! Exiting...")
        exit(1)
    
    video_files = find_all_video_files(videos_path)
    
    staging_dir = "staging"
    if not os.path.exists(staging_dir):
        print("> mkdir staging")
        os.makedirs(staging_dir)
    
    images_dir = "images"
    if not os.path.exists(images_dir):
        print("> mkdir images")
        os.makedirs(images_dir)

    metadata = {}
    for file in video_files:
        print("Processing file:", file)
        video_name, extension = os.path.splitext(os.path.basename(file))

        video_name_split = video_name.split("_")

        # in format SxxEyy
        season_episode_encoding = video_name_split[1]
        season = season_episode_encoding[1:3]
        episode = season_episode_encoding[4:]
        epsiode_name = " ".join(video_name_split[2:])

        out_pattern = "%04d-" + video_name + ".jpg"
        # put frames in a staging location
        # let's us keep track of the output of a single produce_frames call
        out_location = os.path.join(staging_dir, out_pattern)
        produce_frames(file, out_location, 14)
        
        frame_paths = glob.glob(os.path.join(staging_dir, "*"))
        
        for frame_path in frame_paths:
            frame_name = os.path.basename(frame_path)

            # move frame to final location
            url_safe_frame_name = urllib.parse.quote_plus(frame_name)
            destination_path = os.path.join(images_dir, url_safe_frame_name)
            print(f"> mv {frame_path} {destination_path}")
            shutil.move(frame_path, destination_path)

            # construct frame metadata
            frame_data = {}
            frame_data['name'] = epsiode_name
            frame_data['season'] = season
            frame_data['epsiode'] = episode
            frame_data['include'] = True

            metadata[url_safe_frame_name] = frame_data
        
    open("frames.yaml", "w").write(yaml.safe_dump(metadata))

if __name__ == "__main__":
    main()

