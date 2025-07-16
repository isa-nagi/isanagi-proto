---
h1_as_title : true
---

# {{ isa.name }} ISA Specification

## Introduction

text.

## Registers

{% for grp in isa.registers %}
### {{ grp.label }}
{#- ```
:type: long #}

| Index | Name | Aliases | Attributes | Register Number | Dwarf Number |
|-------|------|---------|------------|-----------------|--------------|
{%- for reg in grp.regs %}
| {{ reg.idx }} | {{ reg.label }} | 
{%- if reg.aliases %} {{ reg.aliases|join(', ') }}{% else %} --{% endif %} |
{%- if reg.attrs %} {{ reg.attrs|join(', ') }}{% else %} --{% endif %} |
{#- #} {{ reg.number }} | {{ reg.dwarf_number }} |
{%- endfor %}
{#- ``` #}
{% endfor %}

## Instructions

Instruction Format Tree:

```
{%- for node, gofoward in isa._walk_instruction_tree_by_depth() -%}
{%- if gofoward and not node.instr.opn %}
{{ '{:19s} {:>32s}'.format(('  ' * node.depth) + node.instr.__name__, node.pattern) }}
{%- endif %}
{%- endfor %}
```

{% for instr in isa.instructions %}
### {{ instr.opn }}

Parameters
:   (outs {% for label, tp in instr.prm.outputs.items() -%}
    `{{ label }}:{{ tp }}`{% if not loop.last %}, {% endif %}
    {%- endfor %})
    {#- -#}, {# -#}
    (ins {% for label, tp in instr.prm.inputs.items() -%}
    `{{ label }}:{{ tp }}`{% if not loop.last %}, {% endif %}
    {%- endfor %})

Assembly
:   ```
    {% for ast in instr.asm.ast %}
    {%- if ast == '$opn' %}{{ instr.opn }}
    {%- elif ast[0] == '$' %}{{ ast[1:] }}
    {%- else %}{{ ast }}
    {%- endif %}
    {%- endfor %}
    ```

Bitfields
:    ```wavedrom
     {%- for line in instr.bitfield_wavedrom(instr).splitlines() %}
     {{ line }}
     {%- endfor %}
     ```

Semantic
:    ```python
     {%- for line in instr.semantic_str(instr).splitlines() %}
     {{ line }}
     {%- endfor %}
     ```
{% endfor %}

## Instruction Aliases

| Alias | Instructions |
|:------|:-------------|
{%- for alias in isa.instruction_aliases %}
| `{{ alias.src }}` | `{{ alias.dst|join('`<br>`') }}` |
{%- endfor %}

## History

* ver.0.1.0
  * YYYY-MM-DD
  * publicate first edition.
