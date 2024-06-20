from flask import session, url_for, redirect
import string
import random
import hashlib
import base64
import requests


CLIENT_ID = "86f91bfe53ca4b5a8e5032614f59507c"
CLIENT_SECRET = "5ab8b2a948eb47f3a7eebd489ea8b1b3"  # Replace with your client secret
SCOPE = "user-read-private user-read-playback-state user-read-currently-playing"


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