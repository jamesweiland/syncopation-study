{{ config(
    materialized="create",
    post_hook="create index idx_spotify_album on {{ this.name }} (spotify_id, album_id)"
  )
}}

create table {{ this }} (
    spotify_id varchar not null,
    album_id varchar not null,
    primary key (spotify_id, album_id),
    foreign key (spotify_id) references {{ ref("spotify_tracks").name }}(spotify_id),
    foreign key (album_id) references {{ ref("albums").name }}(album_id)
)