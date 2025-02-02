{% materialization create, adapter='sqlite' %}
  {# A materialization in which to run create table statenments as-is. #}
  
  {%- set target_relation = api.Relation.create(identifier=model['alias'], schema=schema, database=database, type='table') -%}
  {{ drop_relation_if_exists(target_relation) }}

  {{ run_hooks(pre_hooks, inside_transaction=False) }}
  
  {{ run_hooks(pre_hooks, inside_transaction=True) }}
  {% call statement('main') -%}
    {{sql}}
  {%- endcall %}
  {{ run_hooks(post_hooks, inside_transaction=True) }}

  {{ adapter.commit() }}

  {{ run_hooks(post_hooks, inside_transaction=False) }}


  {{ return({'relations': [target_relation]}) }}

{% endmaterialization %}