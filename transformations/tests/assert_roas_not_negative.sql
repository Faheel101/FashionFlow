-- ROAS should not be negative when both spend and revenue are present

select
    performance_id,
    spend,
    revenue,
    roas
from {{ ref('fct_daily_marketing_performance') }}
where spend > 0 and revenue > 0 and roas < 0
