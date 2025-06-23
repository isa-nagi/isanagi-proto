# okojo-elfeditor

ELFファイルを編集します。

## 使用方法

```
okojo-elfeditor [options...] <elf>

positional arguments:
  elf                   編集するELFファイル。

options:
  -c COMMANDS           編集コマンド。
  -o OUTPUT             出力ファイル。
```

## 使用例

### ELF Header のマシン情報を RISC-V にする

```
okojo-elfeditor -c "eh.e_machine=243" test.elf
```
