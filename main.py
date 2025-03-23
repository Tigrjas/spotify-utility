import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
import time

# Load API credentials from .env file
load_dotenv()

# Retrieve credentials from environment variables
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
USER_ID = os.getenv("USER_ID")

# Define the required scopes
scope = "user-library-read playlist-read-private user-library-modify"

# Authenticate with Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=scope
))

# Get Only Playlists You Created
def get_my_playlists(user_id):
    playlists = []
    results = sp.user_playlists(user_id)

    while results:
        for playlist in results['items']:
            if playlist['owner']['id'] == user_id:  # Only include playlists YOU own
                playlists.append(playlist)

        results = sp.next(results) if results['next'] else None

    print(f"✅ You own {len(playlists)} playlists. (Skipping others)")
    return playlists

# Get All Tracks from a Playlist 
def get_all_tracks_from_playlist(playlist_id):
    tracks = []
    results = sp.playlist_tracks(playlist_id)

    while results:
        tracks.extend(results['items'])
        results = sp.next(results) if results['next'] else None

    # Filter out None values and ensure track IDs are valid
    valid_track_ids = [track['track']['id'] for track in tracks if track['track'] and track['track'].get('id')]

    return valid_track_ids  # Return only valid track IDs

# Get All Liked Songs (to avoid duplicates)
def get_all_liked_songs():
    liked_tracks = set()
    results = sp.current_user_saved_tracks(limit=50)

    while results:
        liked_tracks.update(track['track']['id'] for track in results['items'] if track['track'] and track['track'].get('id'))
        results = sp.next(results) if results['next'] else None

    print(f"🎵 You currently have {len(liked_tracks)} liked songs.")
    return liked_tracks

# Save Tracks to "Liked Songs" (Skipping Duplicates) 
def save_tracks_to_liked_songs(track_ids):
    liked_songs = get_all_liked_songs()  # Fetch already liked songs
    new_tracks = [track for track in track_ids if track and track not in liked_songs]  # Ensure no None values

    print(f"🔍 Found {len(liked_songs)} already liked songs.")
    print(f"🎶 {len(new_tracks)} new songs will be added.")

    if not new_tracks:
        print("✅ No new songs to add. Exiting.")
        return

    chunk_size = 50  # Spotify allows max 50 tracks per request
    for i in range(0, len(new_tracks), chunk_size):
        chunk = [track for track in new_tracks[i:i + chunk_size] if track]  # Final safety check
        if not chunk:
            continue  # Skip empty chunks

        sp.current_user_saved_tracks_add(chunk)  # Add batch to "Liked Songs"
        print(f"✅ Added {len(chunk)} new songs to Liked Songs")
        time.sleep(1)  # Sleep to avoid rate limits

    # Show updated liked songs count
    updated_liked_songs = get_all_liked_songs()
    print(f"🎵 After this process, you now have {len(updated_liked_songs)} liked songs!")

if __name__ == "__main__":
    print("🔄 Fetching your playlists (excluding shared ones)...")
    my_playlists = get_my_playlists(USER_ID)  # Fetch only **your** playlists
    all_tracks = []  # Store all track IDs

    for playlist in my_playlists:
        playlist_name = playlist['name']
        playlist_id = playlist['id']
        
        print(f"📂 Fetching songs from playlist: {playlist_name}...")
        tracks = get_all_tracks_from_playlist(playlist_id)
        print(f"🎵 Found {len(tracks)} songs in {playlist_name}")
        all_tracks.extend(tracks)

    print(f"🎧 Total unique songs found across your playlists: {len(set(all_tracks))}")

    save_tracks_to_liked_songs(all_tracks)  # Save only new tracks to "Liked Songs"

    print("🎉 All new songs have been added to your Liked Songs!")
