config{{(
    materialized="create",
    post_hook="create index idx_sid on {{ this.name }} (spotify_id)"
  )
}}

create table {{ this }} (
    spotify_id varchar primary key,
    artists varchar not null,
    album varchar not null,
    genres varchar not null,
    year_first_released integer not null,
    duration integer not null,
    danceability real,
    acousticness real,
    energy real,
    valence real,
)