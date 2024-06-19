from flask import Flask, redirect, request, session, render_template, url_for
import requests
import base64
import hashlib
import os
import random
import string
import time
import re

from pprint import pprint
import azapi

app = Flask(__name__)
app.secret_key = 'tofuhermit'

CLIENT_ID = "86f91bfe53ca4b5a8e5032614f59507c"
CLIENT_SECRET = "5ab8b2a948eb47f3a7eebd489ea8b1b3"  # Replace with your client secret
SCOPE = "user-read-private user-read-playback-state user-read-currently-playing"

AZAPI = azapi.AZlyrics('google')

@app.route('/')
def index():
    if 'access_token' in session and 'token_expires' in session:
        if session['token_expires'] > time.time():
            return handle_currently_playing(session['access_token'])
        else:
            return redirect_to_auth_code_flow()
    else:
        return redirect_to_auth_code_flow()

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if code:
        access_token, expires_in = get_access_token(code)
        if access_token:
            session['access_token'] = access_token
            session['token_expires'] = time.time() + expires_in
            return handle_currently_playing(access_token)
        else:
            return redirect(url_for('index'))
            
    return "Error: Authorization code not provided."

def handle_currently_playing(access_token):
    artist = '' 
    title = ''
    lyrics = ''
    currently_playing = fetch_currently_playing(access_token)
    if currently_playing["currently_playing_type"] == 'track':
        pprint(currently_playing)
        
        artist = currently_playing["item"]["artists"][0]["name"]
        title = remove_brackets(currently_playing["item"]["name"])
        
        pass_artist_to_api(artist)
        pass_title_to_api(title)
        for i in range(3):
            lyrics = get_lyrics(i)
            if isinstance(lyrics, str):
                print("Lyrics found")
                break
    
    else:
        artist = "Spotify"
        title = "Ad"

    return render_index(artist, title, lyrics)

def pass_artist_to_api(artist):
    AZAPI.artist = artist
    print("Artist:", AZAPI.artist)

def pass_title_to_api(title):
    AZAPI.title = title
    print("Title:", AZAPI.title)

def get_lyrics(try_index):
    if try_index == 0:
        lyrics = AZAPI.getLyrics()
    elif try_index == 1:
        pass_title_to_api(AZAPI.title.lower())
        lyrics = AZAPI.getLyrics()
    elif try_index == 2:
        pass_title_to_api(AZAPI.title.title())
        lyrics = AZAPI.getLyrics()
    else:
        return "No lyrics found"
    print(lyrics)
    return lyrics

def render_index(artist, title, lyrics):
    return render_template('index.html', artist=artist, title=title, lyrics=lyrics)

def fetch_currently_playing(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)
    return response.json()

def redirect_to_auth_code_flow():
    verifier = generate_code_verifier(128)
    challenge = generate_code_challenge(verifier)

    session['verifier'] = verifier

    redirect_uri = url_for('callback', _external=True)

    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": SCOPE,
        "code_challenge_method": "S256",
        "code_challenge": challenge
    }

    url = f"https://accounts.spotify.com/authorize?{requests.compat.urlencode(params)}"
    return redirect(url)

def generate_code_verifier(length):
    possible = string.ascii_letters + string.digits
    return ''.join(random.choice(possible) for _ in range(length))

def generate_code_challenge(verifier):
    verifier_bytes = verifier.encode('utf-8')
    digest = hashlib.sha256(verifier_bytes).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode('utf-8')
    return challenge

def get_access_token(code):
    verifier = session.get('verifier')
    if not verifier:
        return None, None

    redirect_uri = url_for('callback', _external=True)

    params = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "code_verifier": verifier
    }
    
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post("https://accounts.spotify.com/api/token", data=params, headers=headers)
    response_data = response.json()
    
    if 'access_token' in response_data and 'expires_in' in response_data:
        return response_data['access_token'], response_data['expires_in']
    else:
        print(response_data)  # Log the error response
        return None, None

def remove_brackets(text):
    cleaned_text = re.sub(r'\[.*?\]', '', text)
    return cleaned_text.strip()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5173)
