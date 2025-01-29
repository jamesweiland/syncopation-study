{{ config(
    materialized="create",
    post_hook="create index idx_midi_spotify on {{ this.name }} (md5, spotify_id)"
  )
}}

create table {{ this }} (
  md5 varchar not null,
  spotify_id varchar not null,
  primary key (md5, spotify_id),
  foreign key (md5) references {{ ref("midi_files").name }}(md5),
  foreign key (spotify_id) references {{ ref("spotify_tracks").name }}(spotify_id)
)