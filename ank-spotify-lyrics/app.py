from flask import Flask, redirect, request, session, render_template, url_for
import requests
import base64
import hashlib
import os
import random
import string
import time

from pprint import pprint
import azapi


app = Flask(__name__)
app.secret_key = os.urandom(24)

CLIENT_ID = "86f91bfe53ca4b5a8e5032614f59507c"
CLIENT_SECRET = "5ab8b2a948eb47f3a7eebd489ea8b1b3"  # Replace with your client secret
REDIRECT_URI = "http://localhost:5173/callback"
SCOPE = "user-read-private user-read-email user-read-playback-state user-read-currently-playing"

AZAPI = azapi.AZlyrics('google', accuracy=0.5)

@app.route('/')
def index():
    if 'access_token' in session and 'token_expires' in session:
        if session['token_expires'] > time.time():
            profile = fetch_profile(session['access_token'])
            currently_playing = fetch_currently_playing(session['access_token'])
            # pprint(profile)
            pprint(currently_playing)
            AZAPI.title = currently_playing["item"]["name"]
            AZAPI.artist = currently_playing["item"]["artists"][0]["name"]
            AZAPI.getLyrics()
            return render_template('index.html', profile=profile, currently_playing=currently_playing, lyrics=AZAPI.lyrics)
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
            profile = fetch_profile(access_token)
            currently_playing = fetch_currently_playing(access_token)
            # pprint(profile)
            # pprint(currently_playing)
            AZAPI.title = currently_playing["item"]["name"]
            AZAPI.artist = currently_playing["item"]["artists"][0]["name"]
            AZAPI.getLyrics()
            return render_template('index.html', profile=profile, currently_playing=currently_playing, lyrics=AZAPI.lyrics)
        else:
            return redirect(url_for('index'))
            
    return "Error: Authorization code not provided."

def fetch_currently_playing(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)
    return response.json()

def fetch_profile(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://api.spotify.com/v1/me", headers=headers)
    return response.json()

def redirect_to_auth_code_flow():
    verifier = generate_code_verifier(128)
    challenge = generate_code_challenge(verifier)

    session['verifier'] = verifier

    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
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

    params = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
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

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=port)
