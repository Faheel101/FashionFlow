{{
    config(
        materialized='table',
        tags=['reconciliation']
    )
}}

-- Compare order-level subtotal against sum of order item totals.
-- Discrepancies indicate data integrity issues.

with order_totals as (
    select
        order_id,
        subtotal as order_subtotal
    from {{ ref('stg_orders') }}
),

item_totals as (
    select
        order_id,
        sum(item_total) as items_subtotal
    from {{ ref('stg_order_items') }}
    group by order_id
),

reconciliation as (
    select
        o.order_id,
        o.order_subtotal,
        coalesce(i.items_subtotal, 0) as items_subtotal,
        round(o.order_subtotal - coalesce(i.items_subtotal, 0), 2) as discrepancy,
        case
            when abs(o.order_subtotal - coalesce(i.items_subtotal, 0)) <= 0.02 then 'matched'
            else 'discrepancy'
        end as status
    from order_totals o
    left join item_totals i on o.order_id = i.order_id
)

select
    *,
    current_timestamp() as reconciled_at
from reconciliation
