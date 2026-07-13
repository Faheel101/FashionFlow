{#
    Override dbt's default schema generation.

    By default dbt concatenates: <target_schema>_<custom_schema>
    which gives us "fashionflow_staging_staging" — not what we want.

    This macro uses the custom_schema_name directly:
      - staging models  → fashionflow_staging
      - mart models     → fashionflow_mart
      - no custom schema → target.dataset (fashionflow_staging)
#}

{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.dataset }}
    {%- else -%}
        fashionflow_{{ custom_schema_name }}
    {%- endif -%}
{%- endmacro %}