config{{(
    materialized="create",
    post_hook="create index idx_sid on {{ this.name }} (spotify_id)"
  )
}}

create table {{ this }} (
    spotify_id varchar primary key,
    title varchar not null,
    album varchar not null,
    artists varchar not null,
    year_first_released integer not null,
    duration_ms integer not null,
    popularity integer,
    danceability real,
    acousticness real,
    energy real,
    valence real,
)