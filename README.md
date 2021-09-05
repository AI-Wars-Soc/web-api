# Web API
The api for the website, written in FastAPI

# Documentation

Host the server locally (see [here](https://github.com/AI-Wars-Soc/server)) and go to to http://lvh.me/api/redoc for all of the endpoints


# Adding a default AI

A 'default AI' is an implementation of an AI for a given game which is either:
 - given to the user as a starting point for their AI
 - used as the code for a bot

Each default AI has two parts: a base and an extension.
The base should contain the files that every AI should have as-is, e.g. README's, `__init__.py` files, etc.
The extension should contain the files specific to the default AI, e.g. the `ai.py` implementation

Before you add a base AI, you need to implement your AI within [AI-Wars-Soc/common](https://github.com/AI-Wars-Soc/common)

You should then place your base and extension AIs that you would like to add to the system into the `default_submissions` folder in this repository.

You then need to add your base and/or extension AIs into the `SUBMISSIONS` dictionary in `app/default_submissions.py`.
The keys within this dictionary are the IDs of the game that submissions belong to. The values are the names of the folders within `default_submissions`
