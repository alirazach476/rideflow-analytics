{% macro apply_user_scd_type2() %}
  {#
    SCD Type 2 helper for dim_user.
    Detects city_id / user_type / status changes vs current rows and expires old versions.
    Intended for incremental user attribute updates after initial load.
  #}
{% endmacro %}
