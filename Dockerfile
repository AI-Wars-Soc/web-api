# Dockerfile for sandbox in which python 3 code is run
FROM debian

# Install python
RUN apt-get update && apt-get -y install python3 python3-pip

# Install npm
RUN apt-get update && apt-get -y install curl nodejs npm
# Update npm
RUN npm install -g npm
# Update nodeJS
RUN npm cache clean -f && npm install -g n && n stable

# Set up user
RUN useradd --create-home --shell /bin/bash web_user --uid 1920

# Copy scripts
COPY server /home/web_user/server
ENV PYTHONPATH="/home/web_user/server:${PYTHONPATH}"

# Install python libraries
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# Install npm libraries
WORKDIR /home/web_user/server/static
RUN npm install && npm run build

WORKDIR /home/web_user
# USER web_user
CMD [ "python3",  "server/main.py" ]