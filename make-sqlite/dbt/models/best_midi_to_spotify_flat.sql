{{ config(materialized="view") }}

/* A flat model of all MIDI files linked to a Spotify track
   with their highest-confidence Spotify track. 
*/

with ranked_relationships as (
    select
        midi_spotify_map.md5,
        midi_spotify_map.spotify_id,
        midi_spotify_map.score,
        row_number() over (partition by midi_spotify_map.md5 order by midi_spotify_map.score desc)
    as rank
        from {{ ref("midi_spotify_map") }} as midi_spotify_map
)
select
    -- midi file data
    midi_files.md5,
    midi_files.wnbd,
    midi_files.instruments,
    -- spotify data
    spotify_tracks.spotify_id,
    spotify_tracks.artists,
    spotify_tracks.album,
    spotify_tracks.genres,
    spotify_tracks.year_first_released,
    spotify_tracks.duration,
    spotify_tracks.danceability,
    spotify_tracks.acousticness,
    spotify_tracks.energy,
    spotify_tracks.valence,
    -- score
    ranked_relationships.score as relationship_score
from {{ ref("midi_files") }} midi_files
join ranked_relationships on midi_files.md5 = ranked_relationships.md5 and ranked_relationships.rank = 1
join {{ ref("spotify_tracks") }} spotify_tracks on ranked_relationships.spotify_id = spotify_tracks.spotify_id