with source as (
    select * from {{ source('raw_inventory', 'inventory_movements') }}
),

renamed as (
    select
        id                                  as movement_id,
        product_id,
        lower(trim(movement_type))          as movement_type,
        quantity,
        cast(unit_cost as numeric)          as unit_cost,
        cast(total_cost as numeric)         as total_cost,
        trim(reference_id)                  as reference_id,
        upper(trim(warehouse_location))     as warehouse_location,
        notes,
        cast(movement_date as date)         as movement_date,
        cast(created_at as timestamp)       as created_at,
        cast(updated_at as timestamp)       as updated_at
    from source
)

select * from renamed
