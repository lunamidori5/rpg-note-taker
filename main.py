from __future__ import annotations

import os
import datetime

import stt

from elroy.api import Elroy

from typing import Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1096 * 2,
    chunk_overlap=0,
    length_function=len,
)

class Character:
    def __init__(self, player_name: str, assistant_name: str, persona: str, text_color: str):
        self.text_color = text_color
        self.name = assistant_name
        self.ai = Elroy(token=f"{player_name}_{assistant_name}", config_path="elroy_config.yaml", persona=persona, assistant_name=assistant_name, database_url=f"sqlite:///{os.path.join(os.getcwd(), "databases", f"{assistant_name}.db")}")

    def message(self, input: str) -> str:
        return self.ai.message(input)

    def remember(self, message: str, name: Optional[str]):
        self.ai.remember(message, name)

def load_file():
    with open("persona_prompt", "r") as f:
        prompt_data = f.read()
    
    return f"{prompt_data}"

def main():
    notes = stt.stt()

    texts = text_splitter.create_documents([notes])

    persona_folder = os.path.join(os.path.pardir)
    
    files = os.listdir(persona_folder); files.sort()

    ## ['Notes', 'Notetaker', 'Persona Darkness', 'Persona Fire', 'Persona Fire and Ice', 'Persona Ice', 'Persona Light', 'Persona Light and Dark', 'Persona Lightning', 'Persona Storm', 'Persona Wind']

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
    

if __name__ == "__main__":
    main()
