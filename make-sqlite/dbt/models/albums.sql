{{ config(
    materialized="create",
    post_hook="create index idx_album on {{ this.name }} (album_id)"
    ) 
}}

create table {{ this }} (
    album_id varchar primary key,
    title varchar not null
)