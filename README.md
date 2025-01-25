Let’s be real—concerts are way more fun when you know the lyrics to every song. With ConcertPlaybook, just enter the concert and artist, and we’ll make you a playlist of all the songs you don't know yet. It's like a study playlist, but way cooler (no rain sounds, promise). Get ready to sing your heart out!

Installation 📥

Follow these steps to set up and run the app:

1. Clone this repository:

git clone https://github.com/yourusername/spotify-concert-prep.git
cd spotify-concert-prep

2. Set up a virtual environment:

python -m venv env
source env/bin/activate  # For Linux/Mac
env\Scripts\activate     # For Windows

Install dependencies:

pip install -r requirements.txt

3. Set up your Spotify credentials:

Create a .env file in the project directory.
Add the following keys and replace the placeholders with your Spotify Developer Dashboard app credentials:
makefile
Copy code
CLIENT_ID=<your_client_id>
CLIENT_SECRET=<your_client_secret>
REDIRECT_URI=<your_redirect_uri>

Note: The REDIRECT_URI should match what you set in your Spotify app settings. Example: http://127.0.0.1:5000/redirect.

Requirements 🛠

Python 3.7+
Flask
Spotify Developer Account

Notes 📝

Your Spotify app credentials (client ID and client secret) should not be shared publicly. Make sure your .env file is listed in .gitignore to prevent accidental uploads.
The app fetches only publicly available playlists matching the concert name and setlist criteria.

Contributing 🤝

Contributions are welcome! Feel free to open an issue or submit a pull request.
