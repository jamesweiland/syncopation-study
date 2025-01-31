import requests
import os
from pydantic import BaseModel
from pandas import DataFrame
from pathlib import Path
from base64 import b64encode
from dataclasses import dataclass

from miditoolkit import MidiFile
from synpy3 import WNBD
from synpy3.syncopation import calculate_syncopation


class Link:
    sid: str
    score: float # represents confidence of the link
    md5: str

    def from_df(df: DataFrame) -> list["Link"]:
        """Create a list of Links from a dataframe"""
        return [
            Link(
                sid=df[idx]["sid"],
                score=df[idx]["score"],
                md5=df[idx]["md5"]
            ) for idx, row in df.iterrows()
        ]

class MIDI:
    md5: str
    instruments: int
    links: list[Link] # note that one md5 can be linked to multiple spotify tracks
    summed_WNBD: float
    mean_WNBD_per_bar: float
    number_of_bars: int
    number_of_bars_not_measured: int
    bars_with_valid_output: int
    bars_without_valid_output: int

    def from_path(path: Path, df: DataFrame) -> "MIDI":
        """Create a MIDI object from a path to a .mid file."""
        assert path[-4] == ".mid"
        md5 = path[:-4]
        links = Link.from_df(df[df["md5"] == md5])
        wnbd = calculate_syncopation(
            model=WNBD,
            source=path
        )
        return MIDI(
            md5=md5,
            instruments=MidiFile(path).num_instruments
            links=links,
            summed_WNBD=wnbd["summed_WNBD"],
            mean_WNBD_per_bar=wnbd["mean_WNBD_per_bar"],
            number_of_bars=wnbd["number_of_bars"],
            number_of_bars_not_measured=wnbd["number_of_bars_not_measured"],
            bars_with_valid_output=wnbd["bars_with_valid_output"],
            bars_without_valid_output=wnbd["bars_without_valid_output"]
        )
    
class SpotifyAPI(BaseModel):
    client_id: str = os.environ["SPOTIFY_CLIENT_ID"]
    client_secret: str = os.environ["SPOTIFY_CLIENT_SECRET"]
    api_token: str = ""

    def get_tracks(self, ids: list[str]) -> list[dict]:
        """ Make a GET request to the Spotify API for a list of tracks and return
            the JSON-formatted response."""
        assert len(ids) <= 50, "Must request less than 50 tracks at a time."

        if self.api_token == "":
            self._send_auth_request()

        ids_comma_separated = ""
        for id in ids:
            ids_comma_separated += id + ","
        ids_comma_separated = ids_comma_separated[:-1]
        
        endpoint = "https://api.spotify.com/v1/tracks?ids=" + ids_comma_separated
        header = {
            "Authorization": "Bearer " + self.api_token
        }
        try:
            response = requests.get(url=endpoint, headers=header)
            if response.status_code == 200:
                return response.json()["tracks"]
            else:
                print(f"Bad HTTP Code: {response.status_code}")
                raise requests.exceptions.HTTPError
        except Exception as e:
            print(f"An error occurred when making the request: {e}")
            raise e
    
    def get_features(self, ids: list[str]) -> list[dict]:
        """ Make a GET request to the Spotify API for a list of tracks' audio
            features and return the JSON-formatted response. """
        assert len(ids) <= 50, "Must request less than 50 tracks at a time."

        if self.api_token == "":
            self._send_auth_request()

        ids_comma_separated = ""
        for id in ids:
            ids_comma_separated += id + ","
        ids_comma_separated = ids_comma_separated[:-1]

        endpoint = "https://api.spotify.com/v1/audio-features?ids=" + ids_comma_separated
        header = {
            "Authorization": "Bearer" + self.api_token
        }
        try:
            response = requests.get(url=endpoint, headers=header)
            if response.status_code == 200:
                return response.json()["tracks"]
            else:
                print(f"Bad HTTP Code: {response.status_code}")
                raise requests.exceptions.HTTPError
        except Exception as e:
            print(f"An error occurred when making the request: {e}")
            raise e
        
    def _send_auth_request(self):
        """ Sends an authorization request for an access token to the Spotify API and
            stores the access token in SPOTIFY_API_TOKEN if successful."""
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_encoded = b64encode(auth_string.encode("utf-8"))

        endpoint = "https://accounts/spotify/api/token"
        headers = {
            "Authorization": "Basic" + auth_encoded,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        body = {"grant_type": "client_credentials"}
        try:
            response = requests.post(url=endpoint, headers=headers, data=body)
            if response.status_code == 200:
                response = response.json()
                global SPOTIFY_API_TOKEN
                SPOTIFY_API_TOKEN = response["access_token"]
                return response["access_token"]
            else:
                print(f"Bad HTTP Code: {response.status_code}")
                raise requests.exceptions.HTTPError
        except Exception as e:
            print(f"An error occured making the request: {e}")
            raise e

# For now, we don't need anything from these objects except the name
# But this might be useful in the future

@dataclass
class Album:
    id: str
    name: str

@dataclass
class Artist:
    id: str
    name: str

class SpotifyTrack(BaseModel):
    id: str
    links: list[Link]
    title: str
    album: Album
    artists: list[Artist]
    year_first_released: int
    duration_ms: int
    popularity: int
    danceability: float
    acousticness: float
    energy: float
    valence: float

    @classmethod
    def from_ids(ids: list[str], df: DataFrame) -> list["SpotifyTrack"]:
        """ Make an API call to the Spotify API for the given Spotify ID and make a SpotifyTrack object out of what the API returns.
            df is a DataFrame that represents the matches found in the TSV file."""

        api = SpotifyAPI()
        track_results = api.get_tracks(ids)
        features_results = api.get_features(ids)
        assert len(track_results) == len(feature_results)
        id_to_track = {track["id"]: track for track in track_results}
        id_to_features = {features["id"]: features for features in features_results}
        spotify_tracks = []
        for id, track in id_to_track:
            # get data from call to tracks endpoint
            links = Link.from_df(df["sid" == id])
            title = track["name"]
            year_first_released = int(track["album"]["release_date"][:3])
            duration_ms = track["duration_ms"]
            popularity = track["popularity"]
            album = Album(
                id=track["album"]["id"],
                name=track["album"]["name"]
            )
            artists = [
                Artist(
                    id=artist["id"],
                    name=artist["name"]
                ) for artist in track["artists"]
            ]

            # get data from call to features endpoint
            features = id_to_features["id"]
            danceability = features["danceability"]
            acousticness = features["acousticness"]
            energy = features["energy"]
            valence = features["valence"]
            spotify_tracks.append(
                SpotifyTrack(
                    id=id,
                    links=links,
                    title=title,
                    album=album,
                    artists=artists,
                    year_first_released=year_first_released,
                    duration_ms=duration_ms,
                    popularity=popularity,
                    danceability=danceability,
                    acousticness=acousticness,
                    energy=energy,
                    valence=valence
                )
            )
        return spotify_tracks





           


    

