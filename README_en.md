# A Visualization webpage for video detection based on Python Flask server architecture and HTML webpage rendering

This project is a Web application based on Flask, used for real-time monitoring of the new files in pre-determined directories (especially video files). The logic is more or less similar to FIFO mechanism.

## Features

- Real-time monitoring of new files in specified directories
- Supports detection and display of MP4 video files
- Displays detected files in real-time on the Webpage
- Provides the deletion button for manipulating the files
- Allows users to play the videos acquired
- Pauses and resumes the file detection

## Tech Stack
- Backend: Python Flask
- Frontend: HTML, JavaScript, CSS
- File system monitoring: Watchdog
- File storage: Redis key-value pair database (single instance, no clustering)
- Persistent file storage: Redis RDB/AOF mechanism

## Installation Requirements
- Python 3.9 - 3.10 (recommended for this version range, higher versions may cause some libraries incompatibility)
- Flask
- Watchdog
- Redis-server

## Installation Steps
1. Clone this repository to your local machine
2. Create and activate a virtual environment (recommended, author's test environment is python3.9 venv)
3. Install the required Python packages:
```bash
pip install flask watchdog
```
4. Install Redis server (if not installed on your machine)
``` bash
brew instal redis  # On Mac
```
or
``` bash
apt install redis  # On Windows
```

## Usage
1. Set the monitored directory: Modify the WATCH_DIRECTORY macro in Server.py to the local path of the directory you want to monitor.
2. Run redis-server executable with the redis.conf configuration file provided in this repository.
``` bash
sudo redis-server./redis.conf
```

or 

- If interested, you may try use some more advanced configurations for Redis-server. Just modify the redis.conf file if you like.

3. Run the Flask application:
```bash
python Server.py # If you use a different Python interpreter, please switch to the name of your interpreter here.
```

4. Open ip_addr:port of http://127.0.0.1:5000 or http://localhost:5000 in your browser.
5. When new files are detected, they will be displayed on the webpage automatically. (Pop-up windows will tell the user that there are new files detected, and the detection cycle will be paused)
6. Use the control buttons on the webpage to play or delete the videos.
7. If the detection cycle is paused, click on "Continue Detection" button to resume it. 
8. "Pause Detection" button is provided for pausing the detection cycle manually.

### Some additional modules implemented for the specific project:
- Data analysis module for the detection results
- Data parsing module for collecting the falling data:
``` Python
date = datetime.strptime(date_str, '%Y:%m:%d').date()
time = datetime.strptime(time_str, '%H:%M:%S').time()
```

- The falling count in hour will be recorded in <key, value> pair in the Redis database. Visualization buttons are provided on the webpage.

# TO DO:
- <u>Remember to delete the appendonlydir file in the source directory to avoid redis initialiation failure.</u>
- Remember to interact first with the webpage before actually running the AI model for generating results.

