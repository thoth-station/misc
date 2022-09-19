#!/usr/bin/env sh

# take the default title screen from https://github.com/thoth-station/core/blob/master/images/Lets%20talk%20Thoth%20tech%20Sessions.png
title_screen="${TITLE:-title.png}"
input_file="${RECORDING:-recording.mp4}"

today=$(date +%Y-%m-%d)
video_date="${TALK_DATE:-$today}"
output_file="tech-talk-${video_date}.mp4"

video_title="Let's Talk Thoth Tech ${video_date}"
video_descr="This is the recording of the ${video_date} iteration of \
“Let’s Talk Thoth Tech”, a weekly series about Thoth and guidance on \
Python Software Stacks/Dependencies. \
See https://bit.ly/thoth-tech-talk-sessions for detailed show notes!"

ffmpeg -loop 1 -framerate 24 -t 3 -i "${title_screen}" \
       -f lavfi -t 1 -i anullsrc -i "${input_file}" \
       -filter_complex "[2:v]scale=1280:720,setsar=sar=1[video];[0:v][1:a][video][2:a]concat=n=2:v=1:a=1" \
       "${output_file}"

echo "
The video is ready to upload!

File: ${output_file}
Title: ${video_title}
Descr: ${video_descr}
"
