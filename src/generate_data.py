import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import pandas as pd


def load_authorization_keys():
    """ Load environment variables (client keys) from .env file.

    Returns:
        Spotify developer client ID, Spotify developer secret key, Spotify user ID.
    """
    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    user_id = os.getenv("SPOTIFY_USER_ID")
    return client_id, client_secret, user_id


def create_spotipy_instance(client_id, client_secret):
    """ Create instance of spotipy to access Spotify API.

    Args:
        client_id (str): Spotify developer client ID.
        client_secret (str): Spotify developer secret key.

    Returns:
        A Spotify API instance.
    """
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri="http://localhost:3000/",
        scope=['user-library-read', 'user-read-currently-playing', 'user-read-playback-state', 'app-remote-control', 'user-modify-playback-state']
    ))
    print(type(sp))
    return sp


def get_playlist_id(sp, user_id, playlist_name):
    """ Fetch ID of a Spotify playlist.

    Args:
        sp (spotipy.client.Spotify): Spotify API instance.
        user_id (str): Spotify user ID.
        playlist_name (str): Name of the Spotify playlist.

    Returns:
        Spotify playlist ID.
    """
    # Get playlist ID
    playlist_id = None
    playlists = sp.user_playlists(user_id)
    for playlist in playlists['items']:
        if playlist['name'] == playlist_name:
            playlist_id = playlist['id']
            break
    return playlist_id


def get_playlist_track_names(sp, user_id, playlist_id):
    """ Retrieve all track names in a playlist.

    Args:
        sp (spotipy.client.Spotify): Spotify API instance
        user_id (string): Spotify user ID
        playlist_id (string): Spotify playlist ID

    Returns:
        List of track names in the playlist.
    """
    results = sp.user_playlist_tracks(user_id, playlist_id, limit=None)
    tracks = results['items']
    track_names = []
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    for t in tracks:
        track_names.append(t['track']['name'])
    return track_names


def log_playthrough_data(playlist_name, percentage_to_play, seconds_delay, save_fn='./data/playthrough.csv'):
    """
    Play through a Spotify playlist and log the songs and their indices in the playlist to a csv file.

    Args:
        playlist_name (str): Name of the Spotify playlist
        percentage_to_play (float): Percentage of the playlist to play through
        seconds_delay (float): Delay between skipping songs (in seconds)
    """
    # Set up Spotify API
    client_id, client_secret, user_id = load_authorization_keys()
    sp = create_spotipy_instance(client_id, client_secret)

    playlist_id = get_playlist_id(sp, user_id, playlist_name)

    # Check if playlist exists
    if not playlist_id:
        print(f"Playlist '{playlist_name}' not found.")
    else:
        track_names = get_playlist_track_names(sp, user_id, playlist_id)

        # Play songs in the shuffled playlist
        sp.shuffle(state=True)
        df = pd.DataFrame(columns=['track_name', 'playlist_pos'])
        num_tracks_to_play = int(percentage_to_play * len(track_names))
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
            time.sleep(seconds_delay)

        # Log output to csv
        df.drop_duplicates(inplace=True)
        df.to_csv(save_fn)


def add_playlist_positions(fn, playlist_name):
    """ Given the name of a file containing track names, add their indices in the playlist.

    Args:
        fn (str): Name of the csv file containing track names.
        playlist_name (str): Name of the Spotify playlist.
    """
    # Load data
    df = pd.read_csv(fn)
    client_id, client_secret, user_id = load_authorization_keys()
    sp = create_spotipy_instance(client_id, client_secret)
    playlist_id = get_playlist_id(sp, user_id, playlist_name)
    track_names = get_playlist_track_names(sp, user_id, playlist_id)
    
    # Add playlist indices
    df['playlist_pos'] = None
    for i, row in df.iterrows():
        track_name = row['track_name']
        playlist_pos = track_names.index(track_name) + 1 

        df.at[i, 'playlist_pos'] = playlist_pos

    # Output to csv file
    df.to_csv(fn)


def log_multiple_playthroughs(playlist_name, percentage_to_play, seconds_delay, num_playthroughs, save_name='./data/playthrough'):
    for i in range(num_playthroughs):
        save_fn = save_name + '_' + str(i+1) + '.csv'
        log_playthrough_data(playlist_name, percentage_to_play, seconds_delay, save_fn)


if __name__ == '__main__':
    log_playthrough_data(playlist_name='sma', percentage_to_play=0.1, seconds_delay=0.5)
    add_playlist_positions('./data/smart_shuffle_playthrough.csv', PLAYLIST_NAME)
    log_multiple_playthroughs(playlist_name='weeb', percentage_to_play=0.2, seconds_delay=0.5, num_playthroughs=50)