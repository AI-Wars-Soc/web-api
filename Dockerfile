# Dockerfile for sandbox in which python 3 code is run
FROM python:3-buster

# Install python
# RUN apt-get update && apt-get -y install python3 python3-pip

# Set up user
RUN useradd --create-home --shell /bin/bash web_user --uid 1920

# Install python libraries
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy scripts
COPY server /home/web_user/server
RUN chown -R 1920 /home/web_user/server
ENV PYTHONPATH="/home/web_user/server:${PYTHONPATH}"

# Set up repository permissions
RUN mkdir /repositories
RUN chown -R 1920 /repositories
RUN chmod 777 /repositories

WORKDIR /home/web_user
USER web_user
CMD [ "python3",  "server/main.py" ]
