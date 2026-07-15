-- Order totals must equal subtotal - discount + tax + shipping
-- This test returns rows where the math doesn't add up (within $0.02 tolerance)

select
    order_id,
    subtotal,
    order_discount_amount,
    tax_amount,
    shipping_amount,
    order_total,
    round(subtotal - order_discount_amount + tax_amount + shipping_amount, 2) as expected_total,
    abs(order_total - round(subtotal - order_discount_amount + tax_amount + shipping_amount, 2)) as diff
from {{ ref('fct_orders') }}
where abs(order_total - round(subtotal - order_discount_amount + tax_amount + shipping_amount, 2)) > 0.02
