import time
from typing import Optional, Union
import requests
import os
from pydantic import BaseModel, PrivateAttr, validator
from pandas import DataFrame
from pathlib import Path
from base64 import b64encode
from dataclasses import dataclass
from miditoolkit import MidiFile
import re
from time import sleep

from synpy3 import WNBD
from synpy3.syncopation import calculate_syncopation


class Link(BaseModel):
    sid: str
    score: float # represents confidence of the link
    md5: str

    def from_df(df: DataFrame) -> list["Link"]:
        """Create a list of Links from a dataframe"""
        return [
            Link(
                sid=row["sid"],
                score=row["score"],
                md5=row["md5"]
            ) for idx, row in df.iterrows()
        ]
    
    @validator("score", "md5", "sid", always=True)
    def check_has_values(cls, v):
        assert v
        return v

    @validator("score", always=True)
    def check_score(cls, v):
        assert v >= 0 and v <= 1
        return v
    
    @validator("md5", always=True)
    def check_md5(cls, v):
        assert len(v) == 32
        assert re.match(r'^[a-fA-F0-9]+$', v) # hexadecimal check
        return v
    
    @validator("sid", always=True)
    def check_sid(cls, v):
        assert len(v) == 22
        assert re.match(r'^[0-9A-Za-z]+$', v) # base62 check
        return v
    

class MIDI(BaseModel):
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
            instruments=MidiFile(path).num_instruments,
            links=links,
            summed_WNBD=wnbd["summed_WNBD"],
            mean_WNBD_per_bar=wnbd["mean_WNBD_per_bar"],
            number_of_bars=wnbd["number_of_bars"],
            number_of_bars_not_measured=wnbd["number_of_bars_not_measured"],
            bars_with_valid_output=wnbd["bars_with_valid_output"],
            bars_without_valid_output=wnbd["bars_without_valid_output"]
        )
    
class SpotifyAPI(BaseModel):
    _client_id: str = PrivateAttr(default=os.environ["SPOTIFY_CLIENT_ID"])
    _client_secret: str = PrivateAttr(default=os.environ["SPOTIFY_CLIENT_SECRET"])
    _api_token: str = PrivateAttr(default="")

    def get_tracks(self, ids: list[str], max_retries = 5) -> list[dict]:
        """ Make a GET request to the Spotify API for a list of tracks and return
            the JSON-formatted response."""
        assert len(ids) <= 50, "Must request less than 50 tracks at a time."

        if self._api_token == "":
            self._send_auth_request()

        ids_comma_separated = ",".join(ids)
        
        endpoint = "https://api.spotify.com/v1/tracks?ids=" + ids_comma_separated
        header = {
            "Authorization": "Bearer " + self._api_token
        }

        for i in range(max_retries):
            try:
                response = requests.get(url=endpoint, headers=header)
                response.raise_for_status()
                return response.json()["tracks"]
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429 or e.response.status_code == 503:
                    print(f"\nTracks request failed with code {e.response.status_code}. Waiting then retrying...\n")
                    time.sleep(5.0)
                elif e.response.status_code == 502:
                    print(f"\nRequest failed with code 502 (bad gateway). Refreshing auth token and retrying...\n")
                    self._send_auth_request()
                else:
                    print(f"\nAn error occured while trying to request tracks: {e}\n")
                    raise e
            except requests.exceptions.RequestException as e:
                print(f"\nAn error occured while trying to request tracks: {e}\n")
                raise e
        else:
            print("\nMax retries exceeded for tracks request\n")
            raise RuntimeError
    
    """ Spotify deprecated their audio-features endpoint :(
        I will keep this function here on the off-chance that
        one day we are able to access audio features from
        Spotify again. In the meantime, there is a Kaggle dataset
        with 1.2 million songs that contains the audio features
        before the endpoint was deprecated.
    """
    # def get_features(self, ids: list[str]) -> list[dict]:
    #     """ Make a GET request to the Spotify API for a list of tracks' audio
    #         features and return the JSON-formatted response. """
    #     assert len(ids) <= 50, "Must request less than 50 tracks at a time."

    #     if self._api_token == "":
    #         self._send_auth_request()

    #     ids_comma_separated = ""
    #     for id in ids:
    #         ids_comma_separated += id + ","
    #     ids_comma_separated = ids_comma_separated[:-1]

    #     endpoint = "https://api.spotify.com/v1/audio-features?ids=" + ids_comma_separated
    #     print(endpoint)
    #     header = {
    #         "Authorization": "Bearer " + self._api_token
    #     }
    #     try:
    #         response = requests.get(url=endpoint, headers=header)
    #         if response.status_code == 200:
    #             return response.json()["tracks"]
    #         else:
    #             print(f"Bad HTTP Code: {response.status_code}")
    #             raise requests.exceptions.HTTPError
    #     except Exception as e:
    #         print(f"An error occurred when making the request: {e}")
    #         raise e
        
    def _send_auth_request(self, max_retries=5):
        """ Sends an authorization request for an access token to the Spotify API and
            stores the access token in api_token if successful."""
        
        auth_string = f"{self._client_id}:{self._client_secret}"
        auth_encoded = b64encode(auth_string.encode("ascii")).decode("ascii")

        endpoint = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": "Basic " + str(auth_encoded),
            "Content-Type": "application/x-www-form-urlencoded"
        }
        body = {"grant_type": "client_credentials"}

        for i in range(max_retries):
            try:
                response = requests.post(url=endpoint, headers=headers, data=body)
                response.raise_for_status()
                self._api_token = response.json()["access_token"]
                return response.json()["access_token"]
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429 or e.response.status_code == 503:
                    print(f"\nToken request failed with code {e.response.status_code}. Waiting then retrying...\n")
                    time.sleep(5.0)
                else:
                    print(f"\nAn error occured making the request to post an id: {e}\n")
                    raise e
            except requests.exceptions.RequestException as e:
                print(f"\nAn error occured while trying to request an auth token: {e}\n")
                raise e
        else:
            print("\nMax retries exceeded for auth token request")
            raise RuntimeError

# For now, we don't need anything from these objects except the name
# But this might be useful in the future

@dataclass
class Album:
    album_id: str
    title: str

@dataclass
class Artist:
    artist_id: str
    title: str

class Features(BaseModel):
    id: str
    danceability: float
    acousticness: float
    energy: float
    valence: float
    speechiness: float
    instrumentalness: float

    @classmethod
    def from_df(cls, id: str, audio_features: DataFrame) -> "Features":
        """ Creates a Features object from the Kaggle CSV of audio features as a dataframe"""
        if id in audio_features["id"]:
            row = audio_features[audio_features["id"] == id]
            return Features(
                id=id,
                danceability=row["danceability"],
                acousticness=row["acousticness"],
                energy=row["energy"],
                valence=row["valence"],
                speechiness=row["speechiness"],
                instrumentalness=row["instrumentalness"]
            )
        else:
            return None

class SpotifyTrack(BaseModel):
    id: str
    links: list[Link]
    title: str
    album: Album
    artists: list[Artist]
    year_first_released: int
    duration_ms: int
    popularity: int
    has_features: bool
    features: Optional[Features]

    @classmethod
    def from_ids(cls, ids: list[str], matches: DataFrame, audio_features: DataFrame) -> list["SpotifyTrack"]:
        """ Make an API call to the Spotify API for the given Spotify ID and make a SpotifyTrack object out of what the API returns.
            df is a DataFrame that represents the matches found in the TSV file."""

        api = SpotifyAPI()
        track_results = api.get_tracks(ids)

        features_results = [Features.from_df(id=id, audio_features=audio_features) for id in ids]

        # keep this in case Spotify un-deprecates the audio-features endpoint
        # features_results = api.get_features(ids)
        # assert len(track_results) == len(feature_results)

        id_to_track = {track["id"]: track for track in track_results}
        id_to_features = {features.id: features for features in features_results if features is not None}
        spotify_tracks = []
        for id in id_to_track.keys():
            # get data from call to tracks endpoint
            track = id_to_track[id]
            links = Link.from_df(matches[matches["sid"] == id])
            title = track["name"]
            year_first_released = int(track["album"]["release_date"][:3])
            duration_ms = track["duration_ms"]
            popularity = track["popularity"]
            album = Album(
                album_id=track["album"]["id"],
                title=track["album"]["name"]
            )
            artists = [
                Artist(
                    artist_id=artist["id"],
                    title=artist["name"]
                ) for artist in track["artists"]
            ]

            # feature data
            if id_to_features.get("id") is not None:
                has_features = True
                features = id_to_features["id"]
            else:
                has_features = False
                features = None
            
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
                    has_features=has_features,
                    features=features
                )
            )
        return spotify_tracks
    





           


    

