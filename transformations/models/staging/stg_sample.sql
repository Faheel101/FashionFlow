-- Sample model to verify dbt + BigQuery connection.
-- Delete this file after confirming dbt debug and dbt run work.

select
    1 as id,
    'FashionFlow' as project_name,
    current_timestamp() as verified_at
