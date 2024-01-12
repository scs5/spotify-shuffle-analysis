import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import pandas as pd

PLAYLIST_NAME = 'sma'
PERCENTAGE_PLAYLIST_TO_PLAY = 0.1
SECONDS_BETWEEN_SONGS = 1


def load_authorization_keys():
    # Load environment variables (client keys) from .env file
    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    user_id = os.getenv("SPOTIFY_USER_ID")
    return client_id, client_secret, user_id


def create_spotipy_instance(client_id, client_secret):
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri="http://localhost:3000/",
        scope=['user-library-read', 'user-read-currently-playing', 'user-read-playback-state', 'app-remote-control', 'user-modify-playback-state']
    ))
    return sp


def get_playlist_track_names(sp, user_id, playlist_id):
    # Get playlist track names
    results = sp.user_playlist_tracks(user_id, playlist_id, limit=None)
    tracks = results['items']
    track_names = []
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    for t in tracks:
        track_names.append(t['track']['name'])
    return track_names


def log_playthrough_data():
    client_id, client_secret, user_id = load_authorization_keys()
    sp = create_spotipy_instance(client_id, client_secret)

    # Get playlist ID
    playlist_id = None
    playlists = sp.user_playlists(user_id)
    for playlist in playlists['items']:
        if playlist['name'] == PLAYLIST_NAME:
            playlist_id = playlist['id']
            break

    if not playlist_id:
        print(f"Playlist '{PLAYLIST_NAME}' not found.")
    else:
        track_names = get_playlist_track_names(sp, user_id, playlist_id)

        # Play songs in the shuffled playlist
        sp.shuffle(state=True)
        df = pd.DataFrame(columns=['track_name', 'playlist_pos'])
        num_tracks_to_play = int(PERCENTAGE_PLAYLIST_TO_PLAY * len(track_names))
        sp.start_playback(context_uri=f"spotify:playlist:{playlist_id}")
        time.sleep(1)
        for _ in range(num_tracks_to_play):
            # Log the track name and playlist positions
            current_track = sp.current_playback()
            track_name = current_track['item']['name']
            playlist_pos = track_names.index(track_name) + 1
            new_row = {'track_name': 'New Track', 'playlist_pos': 1}
            new_row = {'track_name': track_name, 'playlist_pos': playlist_pos}
            df.loc[len(df)] = new_row

            # Go to next track and wait for backend to update
            sp.next_track()
            time.sleep(SECONDS_BETWEEN_SONGS)

        df.to_csv('./data/playthrough.csv')


if __name__ == '__main__':
    log_playthrough_data()