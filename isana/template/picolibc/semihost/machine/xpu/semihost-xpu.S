#include <picolibc.h>

        .global sys_semihost
        .balign 16
sys_semihost:
        //ecall
        slli zero, zero, 0x1f
        ebreak
        srai zero, zero, 0x7
        ret
