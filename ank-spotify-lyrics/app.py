from flask import Flask, redirect, request, session, render_template, url_for
import requests
import os
import time
import re

from pprint import pprint

import azapi
from spotify import *

app = Flask(__name__)
app.secret_key = 'tofuhermit'


proxies = {
   'http': 'http://103.168.38.246:80',
   'socks4': 'https://103.105.41.209:4145'
}

se = ["google", "duckduckgo"]

AZAPI = azapi.AZlyrics(se[0], accuracy=0.5, proxies=proxies)

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
    # print(currently_playing["currently_playing_type"])
    if currently_playing["currently_playing_type"] == 'track':
        print("Artist")
        print(currently_playing["item"]["artists"])
        artist = currently_playing["item"]["artists"][0]["name"]
        title = remove_brackets(currently_playing["item"]["name"])
        
        pass_artist_to_api(artist)
        pass_title_to_api(title)
        for i in range(3):
            print("Trying to find lyrics: ", i)
            lyrics = get_lyrics(i)
            if isinstance(lyrics, str):
                print("Lyrics found")
                break
        else:  # This else clause corresponds to the for-loop, not the if statement.
            swap_search_engine()
            for i in range(3):
                lyrics = get_lyrics(i)
                if isinstance(lyrics, str) and lyrics != 'No lyrics found :(':
                    print("Lyrics found with swapped search engine")
                    break
    
    elif currently_playing["currently_playing_type"] == 'ad':
        artist = "Spotify"
        title = "It's a stupid ad..."

    print(lyrics)
    return render_index(artist, title, lyrics)

def pass_artist_to_api(artist):
    AZAPI.artist = artist
    print("Artist:", AZAPI.artist)

def pass_title_to_api(title):
    AZAPI.title = title
    print("Title:", AZAPI.title)

def get_lyrics(try_index):
    lyrics = 0  
    if try_index == 0:
        lyrics = AZAPI.getLyrics()
    elif try_index == 1:
        pass_title_to_api(AZAPI.title.lower())
        lyrics = AZAPI.getLyrics()
    # elif try_index == 2:
    #     pass_title_to_api(AZAPI.title.title())
    #     lyrics = AZAPI.getLyrics()
    elif try_index > 2:
        return "No lyrics found"
    return lyrics

def render_index(artist, title, lyrics):
    return render_template('index.html', artist=artist, title=title, lyrics=lyrics)

def swap_search_engine():
    current_engine = AZAPI.search_engine
    new_engine = se[1] if current_engine == se[0] else se[0]
    AZAPI.search_engine = new_engine
    print(f"Swapped search engine to: {AZAPI.search_engine}")

def remove_brackets(text):
    cleaned_text = re.sub(r'\[.*?\]', '', text)
    return cleaned_text.strip()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5173)
