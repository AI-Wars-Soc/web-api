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

# Install python libraries
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy scripts
COPY server /home/web_user/server
ENV PYTHONPATH="/home/web_user/server:${PYTHONPATH}"

# Install npm libraries & build
WORKDIR /home/web_user/server/static
RUN npm install && npm run build

# Remove npm & libraries
# RUN rm -rf node_modules
# RUN rm package.json package-lock.json webpack.config.js
# RUN apt-get update && apt-get -y remove curl nodejs npm

WORKDIR /home/web_user
USER web_user
CMD [ "python3",  "server/main.py" ]