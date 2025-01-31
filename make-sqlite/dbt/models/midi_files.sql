{{ config(
    materialized="create",
    post_hook="create index idx_md5 on {{ this.name }} (md5)"
  )
}}

create table {{ this }} (
    md5 varchar primary key,
    instruments integer not null,
    summed_WNBD real,
    mean_WNBD_per_bar real,
    number_of_bars integer,
    number_of_bars_not_measured integer,
    bars_with_valid_output integer,
    bars_without_valid_output integer
)