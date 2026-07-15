{{
    config(
        materialized='table',
        tags=['mart', 'fact']
    )
}}

with daily_perf as (
    select * from {{ ref('stg_daily_performance') }}
),

ads as (
    select * from {{ ref('stg_ads') }}
),

ad_sets as (
    select * from {{ ref('stg_ad_sets') }}
),

campaigns as (
    select * from {{ ref('stg_campaigns') }}
),

final as (

    select
        -- Identifiers
        dp.performance_id,
        dp.performance_date,

        -- Campaign hierarchy
        c.campaign_id,
        c.campaign_name,
        c.platform,
        c.objective,
        c.campaign_status,

        -- Ad set
        ast.ad_set_id,
        ast.ad_set_name,
        ast.bid_strategy,
        ast.targeting_gender,
        ast.targeting_age_min,
        ast.targeting_age_max,

        -- Ad
        a.ad_id,
        a.ad_name,
        a.ad_type,
        a.call_to_action,
        a.ad_status,

        -- Metrics
        dp.impressions,
        dp.clicks,
        dp.spend,
        dp.ctr,
        dp.cpc,
        dp.purchases,
        dp.revenue,

        -- Calculated metrics
        safe_divide(dp.revenue, dp.spend) as roas,
        safe_divide(dp.spend, nullif(dp.purchases, 0)) as cost_per_acquisition,
        safe_divide(dp.purchases, nullif(dp.clicks, 0)) as conversion_rate,

        -- Time dimensions
        extract(year from dp.performance_date) as year,
        extract(month from dp.performance_date) as month,
        extract(dayofweek from dp.performance_date) as day_of_week

    from daily_perf dp

    left join ads a
        on dp.ad_id = a.ad_id

    left join ad_sets ast
        on a.ad_set_id = ast.ad_set_id

    left join campaigns c
        on ast.campaign_id = c.campaign_id

)

select * from final
