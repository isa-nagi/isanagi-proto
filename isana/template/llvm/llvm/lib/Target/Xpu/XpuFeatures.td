{% for feature in features %}
def Feature_{{ feature.varname }} : SubtargetFeature<
  "{{ feature.name }}",
  "{{ feature.fieldname }}",
  "{{ feature.value }}",
  "{{ feature.desc }}",
  []>;
def Has_{{ feature.varname }}
  : Predicate<"Subtarget->has_{{ feature.varname }}()">,
  AssemblerPredicate<(all_of Feature_{{ feature.varname }}),
  "{{ feature.desc }}">;
{% endfor %}
