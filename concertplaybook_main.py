import os
import base64
import json
from dotenv import load_dotenv
import requests
from flask import Flask, request, redirect, url_for

load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Spotify credentials from .env file
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET") #make this dynamic
redirect_uri = os.getenv("REDIRECT_URI", "http://127.0.0.1:5000/redirect")  # Default to localhost

############################## RETRIEVE USER'S TOP TRACKS FROM PAST 6 MONTHS ##############################

def get_authorization_url():
    auth_url = "https://accounts.spotify.com/authorize"
    scope = "user-library-read user-read-private user-top-read user-read-recently-played"  # Updated scope
    auth_params = {
        "response_type": "code",
        "client_id": client_id,
        "scope": scope,
        "redirect_uri": redirect_uri,
    }
    return f"{auth_url}?{requests.compat.urlencode(auth_params)}"

def get_token(authorization_code):
    url = "https://accounts.spotify.com/api/token"
    client_creds = f"{client_id}:{client_secret}"
    client_creds_b64 = base64.b64encode(client_creds.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {client_creds_b64}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": redirect_uri,
    }
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"Error exchanging token: {response.status_code}, {response.text}")
        return None

def user_profile(access_token):
    url = "https://api.spotify.com/v1/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching user profile: {response.status_code}, {response.text}")
        return None

def user_top_tracks(access_token):
    url = "https://api.spotify.com/v1/me/top/tracks"
    headers = {"Authorization": f"Bearer {access_token}"}

    params = {"time_range":"medium_term", "limit": 50} #Spotify's recently-played endpoint has a default limit of 50 tracks per request
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()["items"]  #Returns a list of recently played tracks
    else:
        print(f"Error fetching user's top tracks: {response.status_code}, {response.text}")
        return None
    

############################## RETRIEVE ARTIST'S TOP TRACKS FROM PAST 6 MONTHS ##############################

def get_artist_id(access_token):
    url = "https://api.spotify.com/v1/search"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "q": ARTIST_NAME,
        "type": "artist",
        "limit": 1  # Only fetch the top result
    }
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if data["artists"]["items"]:
            artist = data["artists"]["items"][0]  # Get the first result
            return artist["id"], artist["name"]  # Return artist ID and name
        else:
            print("No artist found with the given name.")
            return None, None
    else:
        print(f"Error searching for artist: {response.status_code}, {response.text}")
        return None, None

def artist_top_tracks(access_token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks"
    headers = {"Authorization": f"Bearer {access_token}"}

    params = {"time_range":"medium_term"} #Spotify's recently-played endpoint has a default limit of 50 tracks per request
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()["tracks"]  # Returns a list of recently played tracks
    else:
        print(f"Error fetching {ARTIST_NAME}'s top tracks: {response.status_code}, {response.text}")
        return None

# Route to handle logging in
@app.route('/')
def login():
    artist_name = request.args.get("artist_name", "")
    if not artist_name:
        return "Please provide an artist name in the query string (in the format ?artist_name=(your artist's name))", 400

    global ARTIST_NAME
    ARTIST_NAME = artist_name  # Set the global artist name dynamically
    auth_url = get_authorization_url()
    return redirect(auth_url)

    

# Route to handle the redirect URI after user authorizes
@app.route('/redirect')
def redirect_page():
    authorization_code = request.args.get('code')
    if not authorization_code:
        return "Authorization code missing.", 400

    access_token = get_token(authorization_code)
    if not access_token:
        return "Error retrieving access token.", 500

    user_prof = user_profile(access_token)
    if not user_prof:
        return "Error retrieving user profile.", 500

    # Fetch user's top tracks
    top_user_tracks = user_top_tracks(access_token)
    if not top_user_tracks:
        return "Error retrieving user's top tracks.", 500
   
    artist_id = get_artist_id(access_token)
    if not artist_id:
        return "Error retrieving artist's ID.", 500
    artist_id = artist_id[0]
    
    top_artist_tracks = artist_top_tracks(access_token, artist_id)
    if not top_artist_tracks:
        return "Error retrieving artist's top tracks.", 500
   
    print("User's Top Tracks:")
    for idx, track in enumerate(top_user_tracks):
        track_name = track["name"]
        artist_name = ", ".join(artist["name"] for artist in track["artists"])
        print(f"{idx + 1}. {track_name} by {artist_name}")


    print("Artist's Top Tracks:")
    for idx, track in enumerate(top_artist_tracks):
        track_name = track["name"]
        artist_name = ", ".join(artist["name"] for artist in track["artists"])
        print(f"{idx + 1}. {track_name} by {artist_name}")

    # Combine user profile and top tracks into a single response
    result = {
        "user_profile": user_prof,
        "top_tracks": top_user_tracks
    }
    return json.dumps(result, indent=4)


# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True, host="127.0.0.1", port=5000, use_reloader=False)
