{% test value_in_range(model, column_name, min_value=0, max_value=1) %}

select {{ column_name }}
from {{ model }}
where {{ column_name }} < {{ min_value }}
   or {{ column_name }} > {{ max_value }}

{% endtest %}
