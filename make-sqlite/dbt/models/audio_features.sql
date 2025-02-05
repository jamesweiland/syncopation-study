{{ config(
    materialized="create",
    post_hook="create index idx_audio_feature on {{ this.name }} (spotify_id)"
  )
}}

create table {{ this }} (
    spotify_id varchar primary key,
    danceability real,
    acousticness real,
    energy real,
    valence real,
    speechiness real,
    instrumentalness real
)