# Dockerfile for sandbox in which python 3 code is run
FROM python:3-buster

# Install python libraries
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# Set up user
RUN useradd --create-home --shell /bin/bash web_user --uid 1920
WORKDIR /home/web_user
USER web_user

# Copy scripts
COPY server /home/web_user/server
ENV PYTHONPATH="/home/web_user/server:${PYTHONPATH}"

CMD [ "python3",  "server/main.py" ]