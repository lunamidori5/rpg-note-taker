from __future__ import annotations

import os

import stt
import torch
import docker
import datetime

from docker import DockerClient, types

from halo import Halo

from elroy.api import Elroy

from huggingface_downloader import download_file_from_midori_ai

from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1096 * 2,
    chunk_overlap=0,
    length_function=len,
)

client = docker.from_env()

spinner = Halo(text='Loading', spinner='dots', color='green')

if torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"

def setup_lrm_server():

    download_file_from_midori_ai("DeepSeek-R1-Distill-Llama-8B-Q3_K_M.gguf", "unsloth", "DeepSeek-R1-Distill-Llama-8B-GGUF", "DeepSeek-R1-Distill-Llama-8B-Q3_K_M.gguf")
    download_file_from_midori_ai("all-MiniLM-L6-v2-Q8_0.gguf", "second-state", "All-MiniLM-L6-v2-Embedding-GGUF", "all-MiniLM-L6-v2-Q8_0.gguf")

    print("Starting server builder, this can take up to 2 hours on slower computers...")

    spinner.start(text=f"Building Llama CPP server")

    if device == "cuda":
        spinner.start(text=f"Building Llama CPP server - With GPU Support")
        client.images.build(path=os.getcwd(), rm=True, dockerfile="dockerfile-gpu", tag="llamacpp-server")
    else:
        client.images.build(path=os.getcwd(), rm=True, dockerfile="dockerfile", tag="llamacpp-server")

    spinner.succeed(text=f"Llama CPP server Built")

    if "llama-cpp-server" in client.containers.list(all=False):
        container = client.containers.get("llama-cpp-server")
        return container
    
    spinner.start(text=f"Starting Llama CPP server")

    models_folder = os.path.join(os.getcwd(), "models")
    
    container_config = {
        "name": "llama-cpp-server",
        "image": "llamacpp-server",
        "auto_remove": True,
        "ports": {'8000/tcp': 8000},
        "volumes": [f"{models_folder}:/models"],
        "detach": True
    }

    if device == "cuda":
        try:
            gpu = types.DeviceRequest(capabilities=[['gpu']])
            container_config["device_requests"] = [gpu]
            container = client.containers.run(**container_config)
        except Exception:
            container = client.containers.run(**container_config)
    else:
        container = client.containers.run(**container_config)

    spinner.succeed(text=f"Llama CPP server running")

    return container

def shutdown_lrm_server(container):
    container.kill()

class Character:
    def __init__(self, player_name: str, assistant_name: str, persona: str, text_color: str):
        self.text_color = text_color
        self.name = assistant_name
        self.ai = Elroy(token=f"{player_name}_{assistant_name}", config_path="elroy_config.yaml", persona=persona, assistant_name=assistant_name, database_url=f"sqlite:///{os.path.join(os.getcwd(), "databases", f"{assistant_name}.db")}")

    def message(self, input: str) -> str:
        spinner.start(text=f"LRM is thinking...")
        text = self.ai.message(input)
        spinner.succeed(text=f"LRM done thinking")
        return text

def load_file():
    with open("persona_prompt", "r") as f:
        prompt_data = f.read()
    
    return f"{prompt_data}"

def main():
    containerd = setup_lrm_server()

    notes = stt.stt()

    notes = input("Input test: ")

    texts = text_splitter.create_documents([notes])

    persona_folder = os.path.join(os.path.pardir)
    
    files = os.listdir(persona_folder); files.sort()

    notetaker = Character("Luna Midori", "Note Taker", load_file(), "Green")

    char_loop = [notetaker]

    for text in texts:
        for char in char_loop:
            print("~" * 55)
            while True:
                try:
                    output = char.message(f"Review this chunk of notes: ```{text}```")
            
                    if len(output) < 1:
                        raise Exception("\nModel failed to reply")

                    char_nots_file = os.path.join(os.path.pardir, "Notes", char.name, f"{datetime.datetime.now():%Y-%m-%d %H-%M-%S}.txt")

                    print(f"{char.name}: {output}")

                    break
                except Exception as Error:
                    output = str(Error)

            with open(char_nots_file, "w") as f:
                f.write(output)

    notes_folder = os.path.join(os.path.pardir, "Notes")
    all_notes = []
    for char_dir in os.listdir(notes_folder):
        char_path = os.path.join(notes_folder, char_dir)
        if os.path.isdir(char_path):
            for note_file in os.listdir(char_path):
                note_path = os.path.join(char_path, note_file)
                with open(note_path, "r") as f:
                    all_notes.append(f.read())

    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    md_file = os.path.join(os.path.pardir, f"Notes_{date_str}.md")
    with open(md_file, "w") as f:
        f.write(f"# Notes for {date_str}\n\n")
        for note in all_notes:
            f.write(f"---\n{note}\n")
    
    shutdown_lrm_server(containerd)
    

if __name__ == "__main__":
    main()
