with source as (

    select * from {{ source('raw', 'products') }}

),

renamed as (

    select
        id                              as product_id,
        upper(trim(sku))                as sku,
        trim(name)                      as product_name,
        description                     as product_description,
        category_id,
        trim(brand)                     as brand,
        cast(price as numeric)          as price,
        cast(cost_price as numeric)     as cost_price,
        round(
            safe_divide(
                cast(price as numeric) - cast(cost_price as numeric),
                cast(price as numeric)
            ), 4
        )                               as gross_margin,
        trim(size)                      as size,
        trim(color)                     as color,
        trim(material)                  as material,
        stock_quantity,
        is_active,
        cast(created_at as timestamp)   as created_at,
        cast(updated_at as timestamp)   as updated_at

    from source

)

select * from renamed
