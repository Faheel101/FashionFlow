with source as (
    select * from {{ source('raw_marketing', 'ad_sets') }}
),

renamed as (
    select
        id                              as ad_set_id,
        campaign_id,
        trim(name)                      as ad_set_name,
        targeting_gender,
        targeting_age_min,
        targeting_age_max,
        targeting_interests,
        cast(daily_budget as numeric)   as daily_budget,
        lower(trim(bid_strategy))       as bid_strategy,
        lower(trim(status))             as ad_set_status,
        cast(created_at as timestamp)   as created_at,
        cast(updated_at as timestamp)   as updated_at
    from source
)

select * from renamed
