import argparse
from .sdk import (
    add_subparser_sdk, build_sdk,
    add_subparser_sdk_compiler, build_sdk_compiler,
    add_subparser_sdk_compiler_rt, build_sdk_compiler_rt,
    add_subparser_sdk_picolibc, build_sdk_picolibc,
)


def main():
    argparser = argparse.ArgumentParser(description='isana build project command')
    subparsers = argparser.add_subparsers(dest="subcommand")
    add_subparser_sdk(subparsers)
    add_subparser_sdk_compiler(subparsers)
    add_subparser_sdk_compiler_rt(subparsers)
    add_subparser_sdk_picolibc(subparsers)

    args = argparser.parse_args()
    if args.subcommand == "sdk":
        build_sdk(args)
    elif args.subcommand == "compiler":
        build_sdk_compiler(args)
    elif args.subcommand == "compiler-rt":
        build_sdk_compiler_rt(args)
    elif args.subcommand == "picolibc":
        build_sdk_picolibc(args)
    else:
        argparser.print_help()


if __name__ == '__main__':
    main()
