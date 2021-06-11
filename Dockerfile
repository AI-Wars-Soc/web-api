# Dockerfile for sandbox in which python 3 code is run
FROM python:3-buster

# Install python
# RUN apt-get update && apt-get -y install python3 python3-pip

# Set up user
RUN useradd --create-home --shell /bin/bash web_user
WORKDIR /home/web_user

# Install python libraries
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy scripts
COPY server /home/web_user/server
COPY server/default_config.yml /home/web_user/default_config.yml
RUN chown -R web_user /home/web_user/server
ENV PYTHONPATH="/home/web_user:/home/web_user/server:${PYTHONPATH}"

# Set up repository permissions
RUN mkdir /home/web_user/repositories && chown -R web_user:web_user /home/web_user
VOLUME /home/web_user/repositories

WORKDIR /home/web_user
USER web_user
EXPOSE 8080
CMD [ "python3",  "server/main.py" ]
