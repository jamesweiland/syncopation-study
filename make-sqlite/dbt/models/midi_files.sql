{{ config(
    materialized="create",
    post_hook="create index idx_md5 on {{ this.name }} (md5)"
  )
}}

create table {{ this }} (
    md5 varchar primary key,
    wnbd real not null,
    instruments integer not null,
)