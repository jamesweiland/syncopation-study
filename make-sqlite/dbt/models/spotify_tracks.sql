{{ config(
    materialized="create",
    post_hook="create index idx_sid on {{ this.name }} (spotify_id)"
  )
}}

create table {{ this }} (
    spotify_id varchar primary key,
    title varchar not null,
    album_id varchar not null,
    artist_ids varchar not null,
    year_first_released integer not null,
    duration_ms integer not null,
    popularity integer,
    has_features boolean not null,
)