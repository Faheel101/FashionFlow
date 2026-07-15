{{
    config(
        materialized='table',
        tags=['reconciliation']
    )
}}

-- Compare payment amounts against refund amounts per order.

with payments as (
    select
        order_id,
        sum(payment_amount) as total_paid
    from {{ ref('stg_payments') }}
    where payment_status = 'completed' or payment_status = 'refunded'
    group by order_id
),

refunds as (
    select
        order_id,
        sum(refund_amount) as total_refunded
    from {{ ref('stg_refunds') }}
    where refund_status = 'processed'
    group by order_id
),

reconciliation as (
    select
        p.order_id,
        p.total_paid,
        coalesce(r.total_refunded, 0) as total_refunded,
        p.total_paid - coalesce(r.total_refunded, 0) as net_collected,
        case
            when coalesce(r.total_refunded, 0) > p.total_paid then 'over_refunded'
            when coalesce(r.total_refunded, 0) > 0 then 'partially_refunded'
            else 'no_refund'
        end as refund_status
    from payments p
    left join refunds r on p.order_id = r.order_id
)

select
    *,
    current_timestamp() as reconciled_at
from reconciliation
