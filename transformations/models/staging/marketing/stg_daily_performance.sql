with source as (
    select * from {{ source('raw_marketing', 'daily_performance') }}
),

renamed as (
    select
        id                              as performance_id,
        ad_id,
        cast(date as date)              as performance_date,
        impressions,
        clicks,
        cast(spend as numeric)          as spend,
        cast(ctr as numeric)            as ctr,
        cast(cpc as numeric)            as cpc,
        purchases,
        cast(revenue as numeric)        as revenue,
        cast(created_at as timestamp)   as created_at,
        cast(updated_at as timestamp)   as updated_at
    from source
)

select * from renamed
