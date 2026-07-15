with source as (
    select * from {{ source('raw_marketing', 'campaigns') }}
),

renamed as (
    select
        id                              as campaign_id,
        trim(name)                      as campaign_name,
        lower(trim(platform))           as platform,
        lower(trim(objective))          as objective,
        lower(trim(status))             as campaign_status,
        cast(daily_budget as numeric)   as daily_budget,
        cast(total_budget as numeric)   as total_budget,
        cast(start_date as date)        as start_date,
        cast(end_date as date)          as end_date,
        cast(created_at as timestamp)   as created_at,
        cast(updated_at as timestamp)   as updated_at
    from source
)

select * from renamed
