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

def user_liked_songs(access_token):
    url = "https://api.spotify.com/v1/me/tracks"
    headers = {"Authorization": f"Bearer {access_token}"}

    all_tracks = []

    #while loop to retrieve all of the user's liked songs
    while url:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            tracks = data.get("items", [])
            
            for item in tracks:
                track = item.get("track")
                if track:  # Ensure the "track" object exists
                    all_tracks.append(track)
            
            # Check if there is another page of results (i.e. more liked songs)
            url = data.get("next")
        else:
            print(f"Error fetching user's liked tracks: {response.status_code}, {response.text}")
            return None

    return all_tracks
 

############################## RETRIEVE ARTIST'S TOP TRACKS FROM PAST 6 MONTHS ##############################

def get_artist_id(access_token):
    url = "https://api.spotify.com/v1/search"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "q": ARTIST_NAME,
        "type": "artist",
        "limit": 50
    }
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        # Try to match exactly with ARTIST_NAME (ignoring case)
        for artist in data["artists"]["items"]:
            if ARTIST_NAME.strip().lower() == artist["name"].strip().lower():
                return artist["id"], artist["name"]
        
        print(f"Warning: No exact match found for '{ARTIST_NAME}', showing first result.")
        # Return the first available result as fallback
        artist = data["artists"]["items"][0]
        return artist["id"], artist["name"]
    else:
        print(f"Error searching for artist: {response.status_code}, {response.text}")
        return None, None

def artist_top_tracks(access_token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks"
    headers = {"Authorization": f"Bearer {access_token}"}

    params = {"time_range":"medium_term"} 

    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()["tracks"]
    else:
        print(f"Error fetching {ARTIST_NAME}'s top tracks: {response.status_code}, {response.text}")
        return None

############################## RETRIEVE SETLIST ##############################

def find_setlist(access_token):
    # API endpoint
    search_url = "https://api.spotify.com/v1/search"

    params = {
        "q": f"{ARTIST_NAME} Setlist",
        "type": "playlist",
        "limit": 50
    }

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(search_url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        playlists = data.get('playlists', {}).get('items', [])

        if not playlists:
            print("No playlists found.")
            return None

    # Filter playlists that contain both artist name and 'setlist' in the title
        filtered_playlists = [
            playlist for playlist in playlists
            if playlist and playlist['name'] and ARTIST_NAME.lower() in playlist['name'].lower() and 'setlist' in playlist['name'].lower()
            and (CONCERT_NAME in playlist['name'] or YEAR in playlist['name'])
        ]

        if not filtered_playlists:
            print("No playlists match the criteria.")
            return None

        # Find the playlist with the most followers
        most_followed_playlist = None
        max_followers = 0

        for playlist in filtered_playlists:
            playlist_id = playlist['id']
            details_url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
            details_response = requests.get(details_url, headers=headers)

            if details_response.status_code == 200:
                details = details_response.json()
                followers = details['followers']['total']
                if followers > max_followers:
                    max_followers = followers
                    most_followed_playlist = {
                        "name": details['name'],
                        "followers": followers,
                        "url": details['external_urls']['spotify']
                    }

        if most_followed_playlist:
            print(f"Most followed playlist: {most_followed_playlist['name']}")
            print(f"Followers: {most_followed_playlist['followers']}")
            print(f"URL: {most_followed_playlist['url']}")
        else:
            print("No playlists found.")
        return most_followed_playlist
    else:
        print(f"Error: {response.status_code}, {response.text}")


############################## COMPARE USER'S LISTENED TRACKS TO ARTIST TRACKS + SETLIST ##############################

def heard_artist_tracks(tracks):
    tracks_by_artist = []
    for track in tracks:
        if ARTIST_NAME in [a["name"] for a in track["artists"]]:
            tracks_by_artist.append(track)
    return tracks_by_artist


# Route to handle logging in
@app.route('/')
def login():
    info = request.args.get("info", "")
    if not info:
        return "Please provide an artist name, concert name, and concert year in the query string (in the format ?info=artist_name/concert_name/year)", 400

    info = info.split("/")
    
    if len(info) != 3:
        return "The query string must contain artist_name, concert_name, and year separated by slashes.", 400

    
    global ARTIST_NAME
    global CONCERT_NAME
    global YEAR

    ARTIST_NAME = info[0]  # Set the global artist name dynamically
    CONCERT_NAME = info[1]
    YEAR = info[2]

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
    liked_songs = user_liked_songs(access_token)
    if not liked_songs:
        return "Error retrieving user's top tracks.", 500
   
    artist_id = get_artist_id(access_token)
    if not artist_id:
        return "Error retrieving artist's ID.", 500
    artist_id = artist_id[0]
    
    top_artist_tracks = artist_top_tracks(access_token, artist_id)
    if not top_artist_tracks:
        return "Error retrieving artist's top tracks.", 500
   
    print("User's Top Tracks:")
    for idx, track in enumerate(liked_songs):
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
        "liked_songs": liked_songs,
    }
    find_setlist(access_token)
    return json.dumps(result, indent=4)


# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True, host="127.0.0.1", port=5000, use_reloader=False)
