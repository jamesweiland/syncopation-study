{{ config(materialized="view") }}

/* A flat model of all Spotify tracks linked to a MIDI file
   with their highest-confidence MIDI file. 
*/

with ranked_relationships as (
    select
        midi_spotify_map.md5,
        midi_spotify_map.spotify_id,
        midi_spotify_map.score,
        row_number() over (partition by midi_spotify_map.spotify_id order by midi_spotify_map.score desc)
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
from {{ ref("spotify_tracks") }} as spotify_tracks
join ranked_relationships on spotify_tracks.spotify_id = ranked_relationships.spotify_id and ranked_relationship.rank = 1
join {{ ref("midi_files") }} as midi_files on ranked_relationships.md5 = midi_files.md5