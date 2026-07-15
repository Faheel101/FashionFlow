{{
    config(
        materialized='table',
        tags=['reconciliation']
    )
}}

-- Monthly marketing spend vs attributed revenue by platform.

with monthly_metrics as (
    select
        platform,
        extract(year from performance_date) as year,
        extract(month from performance_date) as month,
        sum(spend) as total_spend,
        sum(revenue) as total_revenue,
        sum(impressions) as total_impressions,
        sum(clicks) as total_clicks,
        sum(purchases) as total_purchases
    from {{ ref('fct_daily_marketing_performance') }}
    group by platform, year, month
)

select
    *,
    safe_divide(total_revenue, total_spend) as roas,
    safe_divide(total_spend, nullif(total_purchases, 0)) as cpa,
    safe_divide(total_clicks, nullif(total_impressions, 0)) as avg_ctr,
    case
        when safe_divide(total_revenue, total_spend) >= 3.0 then 'profitable'
        when safe_divide(total_revenue, total_spend) >= 1.0 then 'break_even'
        else 'unprofitable'
    end as profitability_status,
    current_timestamp() as reconciled_at
from monthly_metrics
