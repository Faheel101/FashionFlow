with source as (
    select * from {{ source('raw_marketing', 'ads') }}
),

renamed as (
    select
        id                              as ad_id,
        ad_set_id,
        trim(name)                      as ad_name,
        lower(trim(ad_type))            as ad_type,
        trim(headline)                  as headline,
        description                     as ad_description,
        lower(trim(call_to_action))     as call_to_action,
        trim(destination_url)           as destination_url,
        lower(trim(status))             as ad_status,
        cast(created_at as timestamp)   as created_at,
        cast(updated_at as timestamp)   as updated_at
    from source
)

select * from renamed
