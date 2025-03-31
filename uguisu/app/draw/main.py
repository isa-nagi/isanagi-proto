import argparse

from . import callgraph
from . import cfg
from . import dfg


def main():
    argparser = argparse.ArgumentParser(description='isana build project command')
    subparsers = argparser.add_subparsers(dest="subcommand")
    callgraph.add_args(subparsers)
    cfg.add_args(subparsers)
    dfg.add_args(subparsers)

    args = argparser.parse_args()
    if args.subcommand == "callgraph":
        callgraph.main(args)
    elif args.subcommand == "cfg":
        cfg.main(args)
    elif args.subcommand == "dfg":
        dfg.main(args)
    else:
        argparser.print_help()


if __name__ == '__main__':
    main()
