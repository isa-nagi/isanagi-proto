/* Copyright (c) 2019  SiFive Inc. All rights reserved.

   This copyrighted material is made available to anyone wishing to use,
   modify, copy, or redistribute it subject to the terms and conditions
   of the FreeBSD License.   This program is distributed in the hope that
   it will be useful, but WITHOUT ANY WARRANTY expressed or implied,
   including the implied warranties of MERCHANTABILITY or FITNESS FOR
   A PARTICULAR PURPOSE.  A copy of this license is available at
   http://www.opensource.org/licenses.
*/

#include <picolibc.h>

#if defined(PREFER_SIZE_OVER_SPEED) || defined(__OPTIMIZE_SIZE__)
.section .text.memcpy
.global memcpy
.type	memcpy, @function
memcpy:
  addi t1, a0, 0
  beq a2, x0, 2f

1:
  lb t2, 0(a1)
  sb t2, 0(t1)
  addi   a2, a2, -1
  addi   t1, t1, 1
  addi   a1, a1, 1
  bne a2, x0, 1b

2:
  jalr x0, x1, 0

  .size	memcpy, .-memcpy
#endif
