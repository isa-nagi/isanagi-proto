import glob
import hashlib
import os
import shutil
import subprocess
from isana.isa import load_isa


def add_subparser_sdk(subparsers):
    parser = subparsers.add_parser('sdk', help='see `sdk -h`')
    parser.add_argument('--isa-dir', metavar='DIR', default=".",
                        help='set isa model directory')
    parser.add_argument('--generator', metavar='NAME', default="Unix Makefiles",
                        help='set cmake generator')
    parser.add_argument('--install-prefix', metavar='PREFIX', default="install",
                        help='set install directory')
    parser.add_argument('--llvm-project-dir', metavar='DIR', default="llvm-project",
                        help='set llvm-project directory')
    parser.add_argument('--picolibc-dir', metavar='DIR', default="picolibc",
                        help='set picolibc directory')
    parser.add_argument('--work-dir', metavar='DIR', default="work",
                        help='set work directory')


def add_subparser_sdk_compiler(subparsers):
    parser = subparsers.add_parser('compiler', help='see `compiler -h`')
    parser.add_argument('--isa-dir', metavar='DIR', default=".",
                        help='set isa model directory')
    parser.add_argument('--generator', metavar='NAME', default="Unix Makefiles",
                        help='set cmake generator')
    parser.add_argument('--install-prefix', metavar='PREFIX', default="install",
                        help='set install directory')
    parser.add_argument('--llvm-project-dir', metavar='DIR', default="llvm-project",
                        help='set llvm-project directory')
    parser.add_argument('--work-dir', metavar='DIR', default="work",
                        help='set work directory')


def add_subparser_sdk_compiler_rt(subparsers):
    parser = subparsers.add_parser('compiler-rt', help='see `compiler-rt -h`')
    parser.add_argument('--isa-dir', metavar='DIR', default=".",
                        help='set isa model directory')
    parser.add_argument('--generator', metavar='NAME', default="Unix Makefiles",
                        help='set cmake generator')
    parser.add_argument('--install-prefix', metavar='PREFIX', default="install",
                        help='set install directory')
    parser.add_argument('--llvm-project-dir', metavar='DIR', default="llvm-project",
                        help='set llvm-project directory')
    parser.add_argument('--work-dir', metavar='DIR', default="work",
                        help='set work directory')


def add_subparser_sdk_picolibc(subparsers):
    parser = subparsers.add_parser('picolibc', help='see `picolibc -h`')
    parser.add_argument('--isa-dir', metavar='DIR', default=".",
                        help='set isa model directory')
    parser.add_argument('--generator', metavar='NAME', default="Unix Makefiles",
                        help='set cmake generator')
    parser.add_argument('--install-prefix', metavar='PREFIX', default="install",
                        help='set install directory')
    parser.add_argument('--picolibc-dir', metavar='DIR', default="picolibc",
                        help='set picolibc directory')
    parser.add_argument('--work-dir', metavar='DIR', default="work",
                        help='set work directory')


def build_sdk(args, isa=None):
    if isa is None:
        isa = load_isa(args.isa_dir)

    build_sdk_compiler(args, isa)
    build_sdk_compiler_rt(args, isa)
    build_sdk_picolibc(args, isa)

def copy_template_only_diff_files(files, srcdir, dstdir):
    for file in files:
        src_file = os.path.join(srcdir, file)
        src_hash = None
        with open(src_file) as f:
            src_hash = hashlib.md5()
            src_hash.update(f.read().encode())
            src_hash = src_hash.hexdigest()

        dst_file = os.path.join(dstdir, file)
        dst_hash = None
        if os.path.exists(dst_file):
            with open(dst_file) as f:
                dst_hash = hashlib.md5()
                dst_hash.update(f.read().encode())
                dst_hash = dst_hash.hexdigest()

        if dst_hash is None or src_hash != dst_hash:
            dst_dir, dst_fname = os.path.split(dst_file)
            os.makedirs(dst_dir, exist_ok=True)
            shutil.copy2(src_file, dst_file)


def expand_llvm_template(args, isa):
    print("# Expanding compiler templates")

    llvmcc = isa.compiler
    llvmcc.outdir = os.path.join(args.work_dir, "build-llvm-template")
    llvmcc.gen_llvm_srcs()

    pwd = os.getcwd()
    os.chdir(llvmcc.outdir)
    files = glob.glob("**/*", recursive=True)
    files = [f for f in files if os.path.isfile(f)]
    files.sort()
    os.chdir(pwd)

    # copy only different file
    copy_template_only_diff_files(files, llvmcc.outdir, args.llvm_project_dir)


def expand_compiler_rt_template(args, isa):
    print("# Expanding compiler-rt templates")

    llvmcc = isa.compiler
    llvmcc.outdir = os.path.join(args.work_dir, "build-compiler-rt-template")
    llvmcc.gen_compiler_rt_srcs()

    pwd = os.getcwd()
    os.chdir(llvmcc.outdir)
    files = glob.glob("**/*", recursive=True)
    files = [f for f in files if os.path.isfile(f)]
    files.sort()
    os.chdir(pwd)

    # copy only different file
    copy_template_only_diff_files(files, llvmcc.outdir, args.llvm_project_dir)


def expand_picolibc_template(args, isa):
    print("# Expanding picolibc templates")

    llvmcc = isa.compiler
    llvmcc.outdir = os.path.join(args.work_dir, "build-picolibc-template")
    llvmcc.gen_picolibc_srcs()

    pwd = os.getcwd()
    os.chdir(llvmcc.outdir)
    files = glob.glob("**/*", recursive=True)
    files = [f for f in files if os.path.isfile(f)]
    files.sort()
    os.chdir(pwd)

    # copy only different file
    copy_template_only_diff_files(files, llvmcc.outdir, args.picolibc_dir)


def build_sdk_compiler(args, isa=None):
    if isa is None:
        isa = load_isa(args.isa_dir)

    expand_llvm_template(args, isa)

    llvm_install_prefix = os.path.join(os.path.abspath(args.install_prefix), "sdk")
    work_dir = os.path.join(args.work_dir, "build-llvm")

    cmake_cmds = [
        "cmake",
        "-S", "{}".format(os.path.join(args.llvm_project_dir, "llvm")),
        "-B", "{}".format(work_dir),
        "-G", "{}".format(args.generator),
        "-DCMAKE_BUILD_TYPE=Debug",
        "-DCMAKE_INSTALL_PREFIX={}".format(llvm_install_prefix),
        "-DCMAKE_CXX_COMPILER=clang++",
        "-DCMAKE_C_COMPILER=clang",
        "-DLLVM_TARGETS_TO_BUILD={}".format(isa.compiler.target),
        "-DLLVM_ENABLE_PROJECTS=clang;lld",
        "-DLLVM_DEFAULT_TARGET_TRIPLE={}".format(isa.compiler.triple),
    ]

    print("# Building compiler")
    print(" ".join([f'"{c}"' for c in cmake_cmds]))
    proc = subprocess.run(cmake_cmds)
    if proc.returncode != 0:
        raise Exception("[ERROR] failed building compiler.")

    pwd = os.getcwd()
    os.chdir(work_dir)
    cmds = ["make"]
    print(" ".join([f'"{c}"' for c in cmds]))
    proc = subprocess.run(cmds)
    if proc.returncode != 0:
        raise Exception("[ERROR] failed building compiler.")

    cmds = ["make", "install"]
    print(" ".join([f'"{c}"' for c in cmds]))
    proc = subprocess.run(cmds)
    if proc.returncode != 0:
        raise Exception("[ERROR] failed building compiler.")
    os.chdir(pwd)


def build_sdk_compiler_rt(args, isa=None):
    if isa is None:
        isa = load_isa(args.isa_dir)

    expand_compiler_rt_template(args, isa)

    llvm_install_prefix = os.path.join(os.path.abspath(args.install_prefix), "sdk")
    def toolchain_path(name):
        return os.path.join(llvm_install_prefix, "bin", name)
    rt_install_prefix = os.path.join(args.install_prefix, "sdk", "lib", "clang", "20")
    work_dir = os.path.join(args.work_dir, "build-compiler-rt")

    cmake_cmds = [
        "cmake",
        "-S", "{}".format(os.path.join(args.llvm_project_dir, "compiler-rt")),
        "-B", "{}".format(work_dir),
        "-G", "{}".format(args.generator),
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_INSTALL_PREFIX={}".format(rt_install_prefix),
        "-DCMAKE_C_COMPILER_TARGET={}".format(isa.compiler.triple),
        "-DCMAKE_ASM_COMPILER_TARGET={}".format(isa.compiler.triple),
        "-DCMAKE_C_COMPILER_FORCED=ON",
        "-DCMAKE_CXX_COMPILER_FORCED=ON",
        "-DCMAKE_CXX_COMPILER={}".format(toolchain_path("clang++")),
        "-DCMAKE_C_COMPILER={}".format(toolchain_path("clang")),
        "-DCMAKE_AR={}".format(toolchain_path("llvm-ar")),
        "-DCMAKE_NM={}".format(toolchain_path("llvm-nm")),
        "-DCMAKE_RANLIB={}".format(toolchain_path("llvm-ranlib")),
        "-DLLVM_CONFIG_PATH={}".format(toolchain_path("llvm-config")),

        "-DCOMPILER_RT_DEFAULT_TARGET_ONLY=ON",
        # "-DLLVM_TARGETS_TO_BUILD={}32LE".format(isa.compiler.target),

        "-DCMAKE_C_FLAGS=-fno-optimize-sibling-calls -fno-jump-tables -Oz",
        "-DCMAKE_ASM_FLAGS=",

        "-DCOMPILER_RT_BUILD_BUILTINS=ON",
        "-DCOMPILER_RT_BUILD_SANITIZERS=OFF",
        "-DCOMPILER_RT_BUILD_XRAY=OFF",
        "-DCOMPILER_RT_BUILD_LIBFUZZER=OFF",
        "-DCOMPILER_RT_BUILD_PROFILE=OFF",
        "-DCOMPILER_RT_OS_DIR=baremetal",
        "-DCOMPILER_RT_BAREMETAL_BUILD=ON",
    ]

    print("# Building compiler-rt")
    print(" ".join([f'"{c}"' for c in cmake_cmds]))
    proc = subprocess.run(cmake_cmds)
    if proc.returncode != 0:
        raise Exception("[ERROR] failed building compiler-rt.")

    pwd = os.getcwd()
    os.chdir(work_dir)
    cmds = ["make"]
    print(" ".join([f'"{c}"' for c in cmds]))
    proc = subprocess.run(cmds)
    if proc.returncode != 0:
        raise Exception("[ERROR] failed building compiler-rt.")

    cmds = ["make", "install"]
    print(" ".join([f'"{c}"' for c in cmds]))
    proc = subprocess.run(cmds)
    if proc.returncode != 0:
        raise Exception("[ERROR] failed building compiler-rt.")
    os.chdir(pwd)


def build_sdk_picolibc(args, isa=None):
    if isa is None:
        isa = load_isa(args.isa_dir)

    expand_picolibc_template(args, isa)

    llvm_install_prefix = os.path.join(os.path.abspath(args.install_prefix), "sdk")
    picolibc_install_prefix = os.path.join(llvm_install_prefix, "picolibc")
    cross_file = os.path.join(args.picolibc_dir, "scripts",
                              "cross-clang-{}.txt".format(isa.compiler.target.lower()))
    work_dir = os.path.join(args.work_dir, "build-picolibc")

    meson_cmds = [
        "meson",
        "setup",
        "-Dincludedir=include",
        "-Dlibdir=lib",
        "-Dprefix={}".format(picolibc_install_prefix),
        "--cross-file", cross_file,
        work_dir,
        args.picolibc_dir,
    ]

    print("# Building picolibc")
    print(" ".join([f'"{c}"' for c in meson_cmds]))
    os.environ["PATH"] = os.path.join(llvm_install_prefix, "bin") + os.pathsep + os.environ["PATH"]
    proc = subprocess.run(meson_cmds)
    if proc.returncode != 0:
        raise Exception("[ERROR] failed building picloibc.")

    pwd = os.getcwd()
    os.chdir(work_dir)
    cmds = ["ninja"]
    print(" ".join([f'"{c}"' for c in cmds]))
    proc = subprocess.run(cmds)
    if proc.returncode != 0:
        raise Exception("[ERROR] failed building picloibc.")

    cmds = ["ninja", "install"]
    print(" ".join([f'"{c}"' for c in cmds]))
    proc = subprocess.run(cmds)
    if proc.returncode != 0:
        raise Exception("[ERROR] failed building picloibc.")
    os.chdir(pwd)
