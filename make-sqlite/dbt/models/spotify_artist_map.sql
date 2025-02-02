{{ config(
    materialized="create",
    post_hook="create index idx_spotify_artist on {{ this.name }} (spotify_id, artist_id)"
  )
}}

create table {{ this }} (
    spotify_id varchar not null,
    artist_id varchar not null,
    primary key (spotify_id, artist_id),
    foreign key (spotify_id) references {{ ref("spotify_tracks").name }}(spotify_id),
    foreign key (artist_id) references {{ ref("artists").name }}(artist_id)
)