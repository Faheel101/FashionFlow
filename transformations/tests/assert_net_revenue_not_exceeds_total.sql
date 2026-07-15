-- Net revenue should never exceed order total

select
    order_id,
    order_total,
    net_revenue,
    refund_amount
from {{ ref('fct_orders') }}
where net_revenue > order_total + 0.01
