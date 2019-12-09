#!/usr/bin/env bash

python process.py --input videos --output images --capture_interval 14 --remote_url https://jacobysuh.gitlab.io/community/images/ --subtitles --subs_creds_file secrets.yaml --subs_format_file subs.yaml --log DEBUG 
