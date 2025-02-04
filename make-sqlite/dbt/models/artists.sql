{{ config(
    materialized="create",
    post_hook="create index idx_artist_id on {{ this.name }} (artist_id)"
    ) 
}}

create table {{ this }} (
    artist_id varchar primary key,
    title varchar not null
)