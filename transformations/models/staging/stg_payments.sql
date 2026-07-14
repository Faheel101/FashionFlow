with source as (

    select * from {{ source('raw', 'payments') }}

),

renamed as (

    select
        id                              as payment_id,
        order_id,
        lower(trim(payment_method))     as payment_method,
        lower(trim(payment_status))     as payment_status,
        cast(amount as numeric)         as payment_amount,
        trim(transaction_id)            as transaction_id,
        cast(created_at as timestamp)   as paid_at,
        cast(updated_at as timestamp)   as updated_at

    from source

)

select * from renamed
