# Cricbuzz Updates

Cricbuzz Updates provides ways to store cricket updates to a DB and notify users about the updates using an interactive menu to choose their preferences.

## Description

This project is made up of two services. Fetch service, which fetches the data using the Cricbuzz API and pushes it to MongoDB. Notification service which fetches data from a MongoDB and pushes notifications to console and file.

## Features

- Fetch old match data
- Fetch live events for a match
- Fetch multiple matches together
- Data persistence using MongoDB

## Installation

Before using this project, ensure you have Python installed on your system by following the appropriate method for your operating system.

Clone this repo

```
git clone https://github.com/fadedead/cricbuzz-updates
```

Create a .env file in both the _notification-service_ and _fetch-service_, which will hold the credentials to your MongoDB.

```
MONGO_PROTOCOL=""
MONGO_USER=""
MONGO_PWD=""
MONGO_HOST=""
MONGO_OPTIONS=""
```

Create a Python venv in both folders

```
python -m venv ve
```

Install the required packages in both folders.

```
pip install -r requirements.txt
```

Activate the venv in both folders

```
source ve/bin/activate
```

Now you can run the main.py for both services

```
python main.py
```

## Usage

- It is expected that you treat these as different services and run them separately.
- Once Fetcher starts working it could take a few minutes for the data to be available for notification.
- When you run Notification Service, you will given a prompt to pick the matches.
