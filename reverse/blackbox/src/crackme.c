/* Сгенерировано src/generate.py - справочник для преподавателя. */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

int main(int argc, char **argv)
{
    unsigned char buf[64] = {0};
    const size_t n = 31;                 /* длина флага */

    /* stack string: шифртекст (flag XOR 0xd2) пришит в код константами */
    *(uint64_t *)(buf +  0) = 0xA2A1B4B9A1BFBDA6ULL;
    *(uint64_t *)(buf +  8) = 0x8DA1BB8DA0BDAAA9ULL;
    *(uint64_t *)(buf + 16) = 0xA0B1BCB78DA6BDBCULL;
    *(uint64_t *)(buf + 24) = 0xD2AFBCBDBBA6A2ABULL;

    for (size_t i = 0; i < n; i++)
        buf[i] ^= 0xd2;
    buf[n] = '\0';

    if (argc < 2) {
        printf("usage: %s <key>\n", argv[0]);
        return 1;
    }
    if (strcmp((const char *)argv[1], (const char *)buf) == 0) {
        printf("ACCESS GRANTED\n");
        return 0;
    }
    printf("ACCESS DENIED\n");
    return 1;
}
