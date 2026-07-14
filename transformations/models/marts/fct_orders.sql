{{
    config(
        materialized='table',
        tags=['mart', 'fact']
    )
}}

with orders as (

    select * from {{ ref('stg_orders') }}

),

customers as (

    select * from {{ ref('stg_customers') }}

),

order_items as (

    select
        order_id,
        count(*)                        as item_count,
        sum(quantity)                   as total_quantity,
        sum(item_total)                 as items_subtotal,
        sum(item_discount_amount)       as items_discount_total
    from {{ ref('stg_order_items') }}
    group by order_id

),

payments as (

    select
        order_id,
        payment_method,
        payment_status,
        payment_amount,
        paid_at
    from {{ ref('stg_payments') }}

),

refunds as (

    select
        order_id,
        count(*)                        as refund_count,
        sum(refund_amount)              as total_refund_amount
    from {{ ref('stg_refunds') }}
    group by order_id

),

final as (

    select
        -- Order identifiers
        o.order_id,
        o.order_number,
        o.ordered_at,
        o.updated_at                    as order_updated_at,

        -- Customer
        o.customer_id,
        c.full_name                     as customer_name,
        c.email                         as customer_email,
        c.city                          as customer_city,
        c.state                         as customer_state,
        c.country                       as customer_country,

        -- Order status
        o.order_status,
        case
            when o.order_status = 'delivered' then 'completed'
            when o.order_status in ('cancelled', 'returned') then 'closed'
            when o.order_status = 'pending' then 'open'
            else 'in_progress'
        end                             as order_status_category,

        -- Line items
        coalesce(oi.item_count, 0)      as item_count,
        coalesce(oi.total_quantity, 0)  as total_quantity,

        -- Financials
        o.subtotal,
        o.discount_amount               as order_discount_amount,
        coalesce(oi.items_discount_total, 0) as item_discount_amount,
        o.discount_amount + coalesce(oi.items_discount_total, 0) as total_discount_amount,
        o.tax_amount,
        o.shipping_amount,
        o.total_amount                  as order_total,

        -- Payment
        p.payment_method,
        p.payment_status,
        p.payment_amount,
        p.paid_at,

        -- Refunds
        coalesce(r.refund_count, 0)     as refund_count,
        coalesce(r.total_refund_amount, 0) as refund_amount,
        case
            when r.refund_count > 0 then true
            else false
        end                             as has_refund,

        -- Net revenue
        o.total_amount - coalesce(r.total_refund_amount, 0) as net_revenue,

        -- Shipping
        o.shipping_city,
        o.shipping_state,
        o.shipping_country,

        -- Timestamps
        date(o.ordered_at)              as order_date,
        extract(year from o.ordered_at) as order_year,
        extract(month from o.ordered_at) as order_month,
        extract(dayofweek from o.ordered_at) as order_day_of_week

    from orders o

    left join customers c
        on o.customer_id = c.customer_id

    left join order_items oi
        on o.order_id = oi.order_id

    left join payments p
        on o.order_id = p.order_id

    left join refunds r
        on o.order_id = r.order_id

)

select * from final
