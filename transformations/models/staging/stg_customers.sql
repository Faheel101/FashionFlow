with source as (

    select * from {{ source('raw', 'customers') }}

),

renamed as (

    select
        id                              as customer_id,
        lower(trim(email))              as email,
        trim(first_name)                as first_name,
        trim(last_name)                 as last_name,
        trim(first_name) || ' ' || trim(last_name) as full_name,
        phone,
        date_of_birth,
        gender,
        trim(address_line1)             as address_line1,
        trim(address_line2)             as address_line2,
        trim(city)                      as city,
        upper(trim(state))              as state,
        trim(postal_code)               as postal_code,
        upper(trim(country))            as country,
        is_active,
        cast(created_at as timestamp)   as created_at,
        cast(updated_at as timestamp)   as updated_at

    from source

)

select * from renamed
