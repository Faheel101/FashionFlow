with source as (

    select * from {{ source('raw', 'orders') }}

),

renamed as (

    select
        id                                  as order_id,
        trim(order_number)                  as order_number,
        customer_id,
        lower(trim(status))                 as order_status,
        cast(subtotal as numeric)           as subtotal,
        cast(discount_amount as numeric)    as discount_amount,
        cast(tax_amount as numeric)         as tax_amount,
        cast(shipping_amount as numeric)    as shipping_amount,
        cast(total_amount as numeric)       as total_amount,
        trim(shipping_address_line1)        as shipping_address_line1,
        trim(shipping_address_line2)        as shipping_address_line2,
        trim(shipping_city)                 as shipping_city,
        upper(trim(shipping_state))         as shipping_state,
        trim(shipping_postal_code)          as shipping_postal_code,
        upper(trim(shipping_country))       as shipping_country,
        notes,
        cast(created_at as timestamp)       as ordered_at,
        cast(updated_at as timestamp)       as updated_at

    from source

)

select * from renamed
