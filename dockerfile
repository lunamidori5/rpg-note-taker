FROM lunamidori5/pixelarch:topaz

RUN sudo sed -i 's/Topaz/NoteTaker/g' /etc/os-release

ARG USERNAME=midori-ai
USER $USERNAME
WORKDIR /home/$USERNAME

COPY pyproject.toml pyproject.toml
COPY llama_config.yaml llama_config.yaml

RUN uv sync --python python3.12

CMD .venv/bin/python -m llama_cpp.server --config_file llama_config.yaml