with source as (
    select * from {{ source('raw_inventory', 'inventory_snapshots') }}
),

renamed as (
    select
        id                                  as snapshot_id,
        product_id,
        cast(snapshot_date as date)         as snapshot_date,
        quantity_on_hand,
        quantity_reserved,
        quantity_available,
        cast(unit_cost as numeric)          as unit_cost,
        cast(total_value as numeric)        as total_value,
        upper(trim(warehouse_location))     as warehouse_location,
        cast(created_at as timestamp)       as created_at,
        cast(updated_at as timestamp)       as updated_at
    from source
)

select * from renamed
