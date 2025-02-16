
import os
import torch
import datetime

from transformers import pipeline 
from moviepy import VideoFileClip

def load_wisper():
    return pipeline("automatic-speech-recognition", model="openai/whisper-medium.en", torch_dtype=torch.bfloat16, device_map="auto")

def stt():
    output_text = f""
    audio_files = []
    text_list = []

    video_folder_path = input("Video Folder to parse: ")
    files = os.listdir(video_folder_path)

    for file in files:
        video_path = os.path.join(video_folder_path, file)

        mp4_file = video_path

        date_str = datetime.datetime.now().strftime("%Y-%m-%d%H-%M-%S")
        mp3_file = os.path.join("audio_output", f"Notes_{date_str}_{len(text_list)}.mp3")

        #video_clip = VideoFileClip(mp4_file)

        with VideoFileClip(mp4_file) as video_clip:

            audio_clip = video_clip.audio

            if audio_clip is not None:
                audio_clip.write_audiofile(mp3_file)
                audio_clip.close()

        audio_files.append(mp3_file)

    transcriber = load_wisper()
    
    for audio in audio_files:
        notes_text = transcriber(audio)
        text_list.append(notes_text["text"]) # type: ignore
    
    del transcriber
    
    for text in text_list:
        output_text += f" {text}"

    with open("full_output.txt", "w") as f:
        f.write(output_text)

    return output_text