with source as (

    select * from {{ source('raw', 'order_items') }}

),

renamed as (

    select
        id                              as order_item_id,
        order_id,
        product_id,
        quantity,
        cast(unit_price as numeric)     as unit_price,
        cast(discount_amount as numeric) as item_discount_amount,
        cast(total_price as numeric)    as item_total,
        cast(created_at as timestamp)   as created_at,
        cast(updated_at as timestamp)   as updated_at

    from source

)

select * from renamed
