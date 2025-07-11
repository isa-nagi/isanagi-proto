import os
from jinja2 import Template
from isana.model.riscvx.python.isa import isa


if __name__ == "__main__":
    with open('isana/template/doc/spec/isa_spec.md') as f:
        src = f.read()
        s = Template(source=src).render(
            isa=isa,
        )

    outpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'spec.md')
    with open(outpath, 'w') as f:
        f.write(s)
