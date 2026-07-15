{% snapshot product_snapshot %}

{{
    config(
        target_database=var('source_database'),
        target_schema='fashionflow_snapshots',
        unique_key='product_id',
        strategy='check',
        check_cols=['price', 'cost_price', 'category_id', 'is_active', 'stock_quantity'],
    )
}}

select
    product_id,
    sku,
    product_name,
    category_id,
    brand,
    price,
    cost_price,
    gross_margin,
    size,
    color,
    material,
    stock_quantity,
    is_active,
    updated_at
from {{ ref('stg_products') }}

{% endsnapshot %}
