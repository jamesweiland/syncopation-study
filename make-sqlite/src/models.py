from pydantic import BaseModel
from pandas import DataFrame
import requests
import os
from base64 import b64encode
from dataclasses import dataclass

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
    path_to_midi: str
    links: list[Link] # note that one md5 can be linked to multiple spotify tracks
    WNBD_score: dict

    def from_path(path: str, df: DataFrame) -> "MIDI":
        """Create a MIDI object from a path to a .mid file."""
        assert path[-4] == ".mid"
        md5 = path[:-4]
        links = df[df["md5"] == md5]
        WNBD_score = calculate_syncopation(
            model=WNBD,
            source=path
        )
        return MIDI(
            md5=md5,
            path_to_midi=path,
            links=links,
            WNBD_score=WNBD_score
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
    name: str
    album: Album
    artists: list[Artist]
    genres: list[str] # we don't need any data other than the genre name right now
    year_first_released: int
    duration_ms: int
    danceability: float
    acousticness: float
    energy: float
    valence: float

    @classmethod
    def from_ids(ids: list[str], df: DataFrame) -> list["SpotifyTrack"]:
        """ Make an API call to the Spotify API for the given Spotify ID and make a SpotifyTrack object out of what the API returns.
            df is a DataFrame that represents the matches found in the TSV file."""
        
        # method 1
        api = SpotifyAPI()
        track_results = api.get_tracks(ids)
        feature_results = api.get_features(ids)
        assert len(track_results) == len(feature_results)
        for result in track_results:
            links = Link.from_df(df["sid" == result["id"]])
            name = result["name"]
            id = result["id"]
            year_first_release = int(result["album"]["release_date"][:3])
            duration_ms = result["duration_ms"]
            popularity = result["popularity"]
            album = Album(
                id=result["album"]["name"],
                name=result["album"]["name"]
            )
            artists = [
                Artist(
                    id=artist["id"],
                    name=artist["name"]
                ) for artist in result["artists"]
            ]
            features = next((track for track in feature_results if track["id"] == id), None)

        # method 2 - will probably go with this one
        api = SpotifyAPI()
        track_results = api.get_tracks(ids)
        feature_results = api.get_features(ids)
        assert len(track_results) == len(feature_results)
        reorganized_result_dict = {track["id"]: track for track in track_results}
        merged_results = []
        for feature_result in feature_results:
            merged_result = {**feature_result, **reorganized_result_dict["id"]}
            merged_results.append(merged_result)
        for result in track_results:
            links = Link.from_df(df["sid" == result["id"]])
            name = result["name"]
            id = result["id"]
            year_first_release = int(result["album"]["release_date"][:3])
            duration_ms = result["duration_ms"]
            popularity = result["popularity"]
            album = Album(
                id=result["album"]["id"],
                name=result["album"]["name"]
            )
            artists = [
                Artist(
                    id=artist["id"],
                    name=artist["name"]
                ) for artist in result["artists"]
            ]
            features = next((track for track in feature_results if track["id"] == id), None)






           


    

