{{ config(materialized="view") }}

select
    -- midi file data
    flat.md5,
    flat.wnbd,
    flat.instruments,
    -- spotify data
    flat.spotify_id,
    flat.artists,
    flat.album,
    flat.genres,
    flat.year_first_released,
    flat.duration_ms,
    flat.popularity,
    flat.has_features,
    -- features
    features.danceability,
    features.acousticness,
    features.energy,
    features.valence,
    features.speechiness,
    features.instrumentalness,
    -- score
    flat.score as relationship_score
from {{ ref("best_midi_to_spotify_flat") }} flat
join {{ ref("audio_features") }} features on flat.spotify_id = features.spotify_id and flat.has_features = true