with source as (

    select * from {{ source('raw', 'refunds') }}

),

renamed as (

    select
        id                              as refund_id,
        order_id,
        payment_id,
        order_item_id,
        lower(trim(reason))            as refund_reason,
        lower(trim(status))            as refund_status,
        cast(amount as numeric)        as refund_amount,
        notes                          as refund_notes,
        cast(created_at as timestamp)  as refunded_at,
        cast(updated_at as timestamp)  as updated_at

    from source

)

select * from renamed
