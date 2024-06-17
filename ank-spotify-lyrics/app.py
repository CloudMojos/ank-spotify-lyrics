from flask import Flask, redirect, request, session, render_template
import requests
import base64
import hashlib
import os
import random
import string
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)

CLIENT_ID = "86f91bfe53ca4b5a8e5032614f59507c"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"  # Replace with your client secret
REDIRECT_URI = "http://localhost:5173/callback"
SCOPE = "user-read-private user-read-email user-read-playback-state user-read-currently-playing"

@app.route('/')
def index():
    return redirect_to_auth_code_flow()

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if code:
        access_token = get_access_token(code)
        profile = fetch_profile(access_token)
        currently_playing = fetch_currently_playing(access_token)
        return render_template('index.html', profile=profile, currently_playing=currently_playing)
    return "Error: Authorization code not provided."

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
    params = {
        "client_id": CLIENT_ID,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": verifier,
        "client_secret": CLIENT_SECRET
    }
    
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post("https://accounts.spotify.com/api/token", data=params, headers=headers)
    response_data = response.json()
    return response_data.get('access_token')

def fetch_currently_playing(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)
    return response.json()

def fetch_profile(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://api.spotify.com/v1/me", headers=headers)
    return response.json()

if __name__ == "__main__":
    app.run(debug=True, port=5173)
