import subprocess
import glob
import os
import shutil
import yaml
import urllib.parse
import argparse
from pythonopensubtitles.opensubtitles import OpenSubtitles
from pythonopensubtitles.utils import File
import logging
import time

logger = logging.getLogger('process')
log_level = "ERROR"
logger.setLevel(logging.ERROR)

def find_all_video_files(path, extension="mkv"):
    logger.info(f"Looking for video files in: {path}")
    
    if os.path.isfile(path):
        return [path]
    
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

def ffmpeg(path, filters=[], filter_complex=None, args=[]):
    command = ["ffmpeg", "-i", path]
    if len(filters) > 0:
        command.append("-vf")
        command.append(",".join(filters))
    if filter_complex:
        command.append("-filter_complex")
        command.append(f"{filter_complex}")
    global log_level
    if log_level in ['INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        command.append("-hide_banner")
    for arg in args:
        command.append(arg)
    logger.info("> " + " ".join(command))
    subprocess.call(command)

def produce_frames_at_interval(path, capture_interval, output_pattern):
    ffmpeg(path, filters=[f"fps=1/{capture_interval}"], args=[output_pattern])

def produce_frames_at_interval_with_subtitles(path, capture_interval, subs_location, subs_formatting, output_pattern):
    fps_filter = f"fps=1/{capture_interval}"

    subtitles_style = ",".join([f'{key}={value}' for key, value in subs_formatting.items()])
    subtitles_filter = f"subtitles={subs_location}:force_style='{subtitles_style}'"

    filter_complex = ",".join([subtitles_filter, fps_filter])

    ffmpeg(path, filter_complex=filter_complex, args=["-copyts", output_pattern])

def produce_frames(path, output_pattern, capture_interval, complex_filter=None, filters=[""]):
    video_filters_str = ",".join(filters)
    command = ["ffmpeg", "-i", path, "-vf", f"fps=1/{capture_interval}", output_pattern]
    logger.info("> " + " ".join(command))
    subprocess.call(command)

class Subtitler():
    def __init__(self, creds_file=None, username=None, password=None):
        if not creds_file:
            if not username and not password:
                print("Must pass credential file or both username and password when creating Subtitler")
                return None
            elif not username or not password:
                print("Must pass both username and password when creating Subtitler")
                return None
            else:
                self.username = username
                self.password = password
        else:
            logger.debug(f"Passed credentials file at {creds_file}")
            with open(creds_file, "r") as f:
                creds = yaml.safe_load(f)
                try:
                    self.username = creds['username']
                    self.password = creds['password']
                except KeyError as e:
                    logger.error("KeyError: " + str(e))
                    logger.error("Ensure file with OpenSubtitles credentials is YAMl formatted with 'username' and 'password' keys.")
                    return None
        
        self.ost_driver = OpenSubtitles()
        logger.info(f"Logging into OpenSubtitles with username: {self.username}")
        if self.ost_driver.login(self.username, self.password):
            logger.info("Log-in succeeded!")
        else:
            logger.error("Log-in failed with provided credentials.")
            return None

    def get_subtitles_for_file(self, video_file, language_id='eng', subtitle_output_directory="/tmp", subtitle_extension='srt', episode=None, season=None):
        logger.info(f"Searching for subtitles for file {video_file}")
        f = File(video_file)

        video_hash = f.get_hash()
        video_size = f.size

        query = {
                    'sublanguageid': language_id, 
                    'moviehash': video_hash, 
                    'moviebytesize': video_size
        }
        
        if episode:
            query['episode'] = episode
        
        if season:
            query['season number'] = season

        logger.debug("Sending OpenSubtitles Query:" + yaml.safe_dump(query))
        
        subs = None
        
        count = 0
        max_count = 10
        while count < max_count:
            time_to_sleep = (count + 1)
            count += 1
            try:
                subs = self.ost_driver.search_subtitles([query])
                break
            except Exception as e:
                logger.error("Error while searching for subtitles")
                logger.error("Exception: " + str(e))
                logger.error(f"Trying again in {time_to_sleep} seconds...")
                time.sleep(time_to_sleep)
                continue

        if subs is None:
            logger.error(f"Timed out searching for subs for video {video_file}")
            return None

        if len(subs) == 0:
            logger.error(f"No subs found for video {video_file}")
            return None
        elif len(subs) == 1:
            logger.info("Found exactly one subtitle match for video")
            id_subtitle_file = subs[0].get('IDSubtitleFile')
        else:
            logger.info(f"Found {len(subs)} options, choosing best one.")
            # sort based on quality indicators of subtitles
            subs_with_quality = [(sub.get("IDSubtitleFile"), int(not bool(int(sub.get('SubBad')))), float(sub.get("Score")), int(sub.get("SubFromTrusted")) ) for sub in subs]
            # returned results will be sorted first by whether they are good, followed by their score (descending), followed by whether they are from a trusted source
            subs_sorted_by_quality = sorted(sorted(sorted(subs_with_quality, key=lambda x : x[3]), key=lambda x : x[2], reverse=True), key=lambda x : x[1])
            best_subs = subs_sorted_by_quality[0]
            logger.debug(f"Best subs: id = {best_subs[0]}, Quality: SubGood = {best_subs[1]}, Score = {best_subs[2]}, Trusted = {best_subs[3]}")
            id_subtitle_file = best_subs[0]
        
        res = self.ost_driver.download_subtitles([id_subtitle_file], output_directory=subtitle_output_directory, extension=subtitle_extension)
        subs_file = res.get(id_subtitle_file)
        return subs_file

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--output", "-o", help="The output directory for video frames.")
    parser.add_argument("--input", "-i", help="The directory containing video files to process.")
    parser.add_argument("--capture_interval", "-f", help="How frequently to grab a frame in the video in seconds.")
    parser.add_argument("--remote_url", "-u", help="The base URL that the images we be available at.")
    parser.add_argument("--staging", "-s", default="staging", help="The staging directory to place images before they are put in the output directory.")
    parser.add_argument("--subtitles", action='store_true', help="Include this option to download and embed subtitles into the frames. Subtitles downloaded from OpenSubtitles.org")
    parser.add_argument("--subs_creds_file", default=None, help="A YAML file with keys 'username' and 'password' that can be used to log-in ot OpenSubtitles.org")
    parser.add_argument("--subs_username", default=None, help="A username for an account with OpenSubtitles.org")
    parser.add_argument("--subs_password", default=None, help="A password the can be used with the username passed with --subs_username to log-in to OpenSubtitles.org")
    parser.add_argument("--subs_format", default=None, help="A comma separated list of format options that would be passed to force_style in ffmpeg")
    parser.add_argument("--subs_format_file", default=None, help="A YAML file that specifies a dictionary of format that would be passed to force_style in ffmpeg")
    parser.add_argument("--log", default='ERROR', help="The logging level to use; DEBUG, INFO, WARNING, ERROR, or CRITICAL")

    args = parser.parse_args()

    output_path = args.output
    input_path = args.input
    staging_path = args.staging
    capture_interval = args.capture_interval
    remote_url = args.remote_url

    include_subtitles = args.subtitles
    subs_creds_file = args.subs_creds_file
    subs_username = args.subs_username
    subs_password = args.subs_password
    subs_format = args.subs_format
    subs_format_file = args.subs_format_file

    log = args.log
    global logger
    global log_level

    logging_options = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if log not in logging_options:
        logger.error(f"--logging must be one of {logging_options}")
        exit(-1)
    else:
        log_level = log
        if log_level == 'DEBUG':
            logger.setLevel(logging.DEBUG)
        elif log_level == 'INFO':
            logger.setLevel(logging.INFO)
        elif log_level == 'WARNING':
            logger.setLevel(logging.WARNING)
        elif log_level == 'ERROR':
            logger.setLevel(logging.ERROR)
        elif log_level == 'CRITICAL':
            logger.setLevel(logging.CRITICAL)
        logger.debug(f"Set log-level to {log_level}")

    if include_subtitles:
        if subs_creds_file:
            subs = Subtitler(creds_file=subs_creds_file)
        else:
            if subs_username and subs_password:
                subs = Subtitler(username=subs_username, password=subs_password)
            else:
                logging.error("If including subtitles, ensure you start this script with either --subs_creds_file or both of --subs_username and --subs_password")
                exit(-1)
        if subs_format and subs_format_file:
            logging.error("Pass only one of --subs_format or --subs_format_file.")
            exit(-1)

        subtitle_format_dict = {}

        if subs_format:
            subs_format_split = [ option.split("=") for option in subs_format.split(",") ]
            subtitle_format_dict = { option[0] : option[1] for option in subs_format_split }
        
        if subs_format_file:
            with open(subs_format_file, "r") as f:
                subtitle_format_dict = yaml.safe_load(f)
    else:
        subs = None

    if not output_path:
        parser.error("Must pass directory for output with --output or -o.")
    if not input_path:
        parser.error("Must pass directory for input with --input or -i.")
    if not capture_interval:
        parser.error("Must pass frames per second with --capture_interval or -f.")
    if not remote_url:
        parser.error("Must pass remote url for images with --remote_url or -u")

    if not os.path.exists(input_path) and os.path.isdir(input_path):
        logging.error(f"Error: folder {input_path} does not exist! Exiting...")
        exit(-1)
    
    video_files = find_all_video_files(input_path)
    
    if not os.path.exists(staging_path):
        logging.info("> mkdir", staging_path)
        os.makedirs(staging_path)
    
    if not os.path.exists(output_path):
        logging.info("> mkdir", output_path)
        os.makedirs(output_path)

    frames_metadata_file = "frames.yaml"
    frames_metadata = {}
    if os.path.exists(frames_metadata_file):
        logging.info(frames_metadata_file, "already exists. Reading data from it.")
        with open(frames_metadata_file, "r") as f:
            frames_metadata = yaml.safe_load(f)
    
    processing_metadata_file = "processing.yaml"
    processing_metadata = {}
    if os.path.exists(processing_metadata_file):
        logging.info(processing_metadata_file, "already exists. Reading data from it.")
        with open(processing_metadata_file, "r") as f:
            processing_metadata = yaml.safe_load(f)
    else:
        processing_metadata['done'] = []

    for file in video_files:
        logging.info("Processing file:", file)
        filename = os.path.basename(file)
        video_name, extension = os.path.splitext(filename)

        if filename in processing_metadata['done']:
            logging.info("File already processed! Skipping...")
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
        if subs:
            subs_file = subs.get_subtitles_for_file(file, episode=int(episode), season=int(season))
            if subs_file:
                produce_frames_at_interval_with_subtitles(file, capture_interval, subs_file, subtitle_format_dict, out_location)
            else:
                produce_frames_at_interval(file, capture_interval, out_location)
        else:
            produce_frames_at_interval(file, capture_interval, out_location)
        
        frame_paths = glob.glob(os.path.join(staging_path, "*"))
        
        for frame_path in frame_paths:
            frame_name = os.path.basename(frame_path)

            # move frame to final location
            url_safe_frame_name = urllib.parse.quote_plus(frame_name)
            destination_path = os.path.join(output_path, url_safe_frame_name)
            logging.info(f"> mv {frame_path} {destination_path}")
            shutil.move(frame_path, destination_path)

            # construct frame metadata
            frame_data = {}
            frame_data['name'] = epsiode_name
            frame_data['season'] = season
            frame_data['episode'] = episode
            frame_data['include'] = True
            frame_data['url'] = os.path.join(remote_url, url_safe_frame_name)

            frames_metadata[url_safe_frame_name] = frame_data

            logger.debug("Added entry to frames metadata:\n" + yaml.safe_dump(frames_metadata[url_safe_frame_name]))
        
        processing_metadata['done'].append(filename)
        processing_metadata[filename] = {}
        processing_metadata[filename]['capture_interval'] = capture_interval
        processing_metadata[filename]['subs'] = {}
        if subs:
            processing_metadata[filename]['subs']['enabled'] = True
            
            if subs_file:
                processing_metadata[filename]['subs']['download_successful'] = True
                processing_metadata[filename]['subs']['subs_file'] = subs_file
                subs_id, ext = os.path.splitext(os.path.basename(subs_file))
                processing_metadata[filename]['subs']['subs_id'] = subs_id
            else:
                processing_metadata[filename]['subs']['download_successful'] = False
            
            processing_metadata[filename]['subs']['format'] = subtitle_format_dict
        else:
            processing_metadata[filename]['subs']['enabled'] = False
        
        logger.debug("Added entry to processing metadata:\n" + yaml.safe_dump(processing_metadata[filename]))

    with open(frames_metadata_file, "w") as f:
        f.write(yaml.safe_dump(frames_metadata))
    with open(processing_metadata_file, "w") as f:
        f.write(yaml.safe_dump(processing_metadata))

if __name__ == "__main__":
    main()

