
import os
import torch
from transformers import pipeline
from moviepy import VideoFileClip

def stt():
    output_text = f""
    text_list = []

    folder_path = '/home/lunamidori/nfsshares/Videos'
    files = os.listdir(folder_path)

    for file in files:
        if file.endswith('.mp4'):
            video_path = os.path.join(folder_path, file)

            mp4_file = video_path
            mp3_file = "audio.mp3"

            video_clip = VideoFileClip(mp4_file)

            audio_clip = video_clip.audio

            audio_clip.write_audiofile(mp3_file)

            audio_clip.close()
            video_clip.close()

            transcriber = pipeline("automatic-speech-recognition", model="openai/whisper-small", torch_dtype=torch.bfloat16, device_map="auto")
            notes_text = transcriber(mp3_file)

            os.remove(mp3_file)

            text_list.append(notes_text["text"])
    
    for text in text_list:
        output_text += f" {text}"

    with open("full_output.txt", "w") as f:
        f.write(output_text)

    return output_text