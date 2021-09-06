# Dockerfile for sandbox in which python 3 code is run
FROM python:3.8-buster

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Europe/London \
    PYTHONPATH="/home/web_user:/home/web_user/app:${PYTHONPATH}" \
    PATH="/home/web_user/.local/bin:${PATH}"

# Set up user
RUN useradd --create-home --shell /bin/bash web_user
WORKDIR /home/web_user

# Install python libraries as user
USER web_user
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy default submissions
COPY default_submissions /home/web_user/default_submissions

# Copy scripts
COPY --chown=web_user app /home/web_user/app
ADD --chown=web_user https://raw.githubusercontent.com/AI-Wars-Soc/common/main/default_config.yml /home/web_user/default_config.yml

# Set up env
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set up repository permissions
RUN mkdir /home/web_user/repositories
VOLUME /home/web_user/repositories

WORKDIR /home/web_user
EXPOSE 8080
CMD [ "bash",  "app/run.sh" ]
