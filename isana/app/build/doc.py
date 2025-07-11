import os
import pathlib
from jinja2 import Template
from isana.isa import load_isa


def add_subparser_doc(subparsers):
    parser = subparsers.add_parser('doc', help='see `doc -h`')
    parser.add_argument('--isa-dir', metavar='DIR', default='.',
                        help='set isa model directory')
    parser.add_argument('--install-prefix', metavar='PREFIX', default="install",
                        help='set install directory')


def add_subparser_doc_isa_spec(subparsers):
    parser = subparsers.add_parser('isa-spec', help='see `isa-spec -h`')
    parser.add_argument('--isa-dir', metavar='DIR', default='.',
                        help='set isa model directory')
    parser.add_argument('--install-prefix', metavar='PREFIX', default="install",
                        help='set install directory')
    parser.add_argument('--template', metavar='FILE', default='',
                        help='set template file')


def build_doc(args, isa=None):
    if isa is None:
        isa = load_isa(args.isa_dir)

    build_doc_isa_spec(args, isa)


def build_doc_isa_spec(args, isa=None):
    if isa is None:
        isa = load_isa(args.isa_dir)

    template_path = args.template
    if template_path == '':
        cur_dir = pathlib.Path(os.path.dirname(__file__))
        template_dir = os.path.join(str(cur_dir.parent.parent), 'template')
        template_path = os.path.join(template_dir, 'doc', 'spec', 'isa_spec.md')
    # print(template_path)
    # return
    with open(template_path) as f:
        src = f.read()
        s = Template(source=src).render(
            isa=isa,
        )

    output_dir = os.path.join(args.install_prefix, 'doc')
    os.makedirs(output_dir, exist_ok=True)
    outpath = os.path.join(output_dir, 'isa-spec.md')
    with open(outpath, 'w') as f:
        f.write(s)
