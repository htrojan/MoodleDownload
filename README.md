# MoodleDownload
A simple moodle download script for TU Dortmund university

## Installation
Required packages: -mechanize (pip install mechanize)

## Usage
python main.py

Then enter username and password (the password input does not print to your console).
Your 10 recently visited courses will be downloaded immediately

## Command line arguments (Advanced)
"save": Logs you in and then saves your current session (including session cookies and a moodle specific key) to your disk.
"load": Skips the login prompt and tries to load a previously stored session

These options are primarily for development, as a new login for every testrun of the script is unnecessary
