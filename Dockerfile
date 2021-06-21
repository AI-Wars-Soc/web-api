# Dockerfile for sandbox in which python 3 code is run
FROM python:3-buster

# Set up user
RUN useradd --create-home --shell /bin/bash web_user
WORKDIR /home/web_user

# Install python libraries as user
USER web_user
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt
USER root

# Copy scripts
COPY app /home/web_user/app
COPY app/default_config.yml /home/web_user/default_config.yml
RUN chown -R web_user /home/web_user/app
ENV PYTHONPATH="/home/web_user:/home/web_user/app:${PYTHONPATH}"

# Set up env
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set up repository permissions
USER web_user
RUN mkdir /home/web_user/repositories
VOLUME /home/web_user/repositories

WORKDIR /home/web_user
EXPOSE 8080
CMD [ "bash",  "app/run.sh" ]
