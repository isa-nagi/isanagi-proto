# isana-build

ISAモデルからSDKを生成します。


## 依存関係

* llvm-project
    * llvmorg-20-init +α  
      (hash: d21e731c42d6b967e29dbe2edc16c1b86885df0d)
* picolibc
    * (hash: fb36d6cebb7b5abd7a9497ddda9b7627b7cd0624)

## 使用方法

```
isana-build <subcommand> [options...]

  subcommand:
    sdk                   SDKの全てのツールを生成します。
    compiler              コンパイラを生成します。
    compiler-rt           ランタイム・ライブラリを生成します。
    picolibc              組み込み向け標準Cライブラリ Picolibc を生成します。

  options
    --isa-dir DIR         ISAモデルがあるディレクトリを設定します。
    --generator NAME      cmake generatorを設定します。
    --install-prefix PREFIX
                          SDKのインストールディレクトリを設定します。
    --llvm-project-dir DIR
                          llvm-project ソースがあるディレクトリを設定します。
    --picolibc-dir DIR    picolibc ソースがあるディレクトリを設定します。
    --work-dir DIR        作業ディレクトリを設定します。

```

例：

```
isana-build sdk \
  --isa-dir isanagi-proto/isana/model/riscvx/python \
  --install-prefix ./riscvxpu \
  --llvm-project-dir ./llvm-project \
  --picolibc-dir ./picolibc \
  --work-dir ./work
```

## SDK使用方法

SDKファイル構成：

```
riscvxpu
└── sdk
    ├── bin
    ├── include
    ├── lib
    │   └── clang
    │       └── 20  # compiler-rt
    │           ├── include
    │           └── lib
    ├── libexec
    ├── picolibc
    │   ├── include
    │   └── lib
    └── share
```

コンパイルコマンド：

```
./riscvxpu/sdk/bin/clang
  -Oz \
  -lsemihost \
  -T picolibc.ld \
  helloworld.c
```
