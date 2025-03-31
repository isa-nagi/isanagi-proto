/* Copyright (c) 2017  SiFive Inc. All rights reserved.

   This copyrighted material is made available to anyone wishing to use,
   modify, copy, or redistribute it subject to the terms and conditions
   of the FreeBSD License.   This program is distributed in the hope that
   it will be useful, but WITHOUT ANY WARRANTY expressed or implied,
   including the implied warranties of MERCHANTABILITY or FITNESS FOR
   A PARTICULAR PURPOSE.  A copy of this license is available at
   http://www.opensource.org/licenses.
*/

#include <picolibc.h>

.section .text.memset
.global memset
.type	memset, @function
memset:
#if defined(PREFER_SIZE_OVER_SPEED) || defined(__OPTIMIZE_SIZE__)
  add t1, a0, zero
  beq a2, x0, 2f

1:
  sb a1, 0(t1)
  addi  a2, a2, -1
  addi  t1, t1, 1
  bne a2, x0, 1b

2:
  jalr x0, x1, 0

#else
  addi t1, zero, 15
  addi a4, a0, 0
  bleu a2, t1, .Ltiny
  andi a5, a4, 15
  bne a5, x0, .Lmisaligned

.Laligned:
  bne a1, x0, .Lwordify

.Lwordified:
  andi a3, a2, ~15
  andi a2, a2, 15
  add  a3, a3, a4

#if __riscv_xlen == 64
1:sd a1, 0(a4)
  sd a1, 8(a4)
#else
1:sw a1, 0(a4)
  sw a1, 4(a4)
  sw a1, 8(a4)
  sw a1, 12(a4)
#endif
  addi a4, a4, 16
  bltu a4, a3, 1b

  bne a2, x0, .Ltiny
  jalr x0, x1, 0

.Ltiny:
  sub a3, t1, a2
  slli a3, a3, 2
1:auipc t0, %pcrel_hi(.Ltable)
  add a3, a3, t0
.option push
.option norvc
.Ltable_misaligned:
  //jr a3, %pcrel_lo(1b)
  jalr x0, a3,1b
.Ltable:
  sb a1,14(a4)
  sb a1,13(a4)
  sb a1,12(a4)
  sb a1,11(a4)
  sb a1,10(a4)
  sb a1, 9(a4)
  sb a1, 8(a4)
  sb a1, 7(a4)
  sb a1, 6(a4)
  sb a1, 5(a4)
  sb a1, 4(a4)
  sb a1, 3(a4)
  sb a1, 2(a4)
  sb a1, 1(a4)
  sb a1, 0(a4)
.option pop
  jalr x0, x1, 0

.Lwordify:
  andi a1, a1, 0xFF
  slli a3, a1, 8
  or   a1, a1, a3
  slli a3, a1, 16
  or   a1, a1, a3
#if __riscv_xlen == 64
  slli a3, a1, 32
  or   a1, a1, a3
#endif
  jal zero, .Lwordified

.Lmisaligned:
  slli a3, a5, 2
1:auipc t0, .Ltable_misaligned
  add a3, a3, t0
  addi t0, ra, 0
  jalr a3, 1b, 0
  addi ra, t0, 0

  addi a5, a5, -16
  sub  a4, a4, a5
  add  a2, a2, a5
  bleu a2, t1, .Ltiny
  jal zero, .Laligned
#endif
  .size	memset, .-memset
