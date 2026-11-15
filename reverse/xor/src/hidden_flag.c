#include <stdio.h>
#include <string.h>

unsigned char secret[] = {0x3a, 0x2d, 0x30, 0x1d, 0x29, 0x71, 0x3b, 0x1d, 0x30, 0x71, 0x34, 0x71, 0x30, 0x31, 0x71, 0x26};
const size_t secret_len = sizeof(secret);

int check_password(const char *input) {
    if (strlen(input) != secret_len) return 0;
    for (size_t i = 0; i < secret_len; i++) {
        if (((unsigned char)input[i] ^ 0x42) != secret[i]) return 0;
    }
    return 1;
}

int main(void) {
    char input[128];
    printf("Enter password: ");
    if (!fgets(input, sizeof(input), stdin)) return 1;
    input[strcspn(input, "\n")] = 0;
    if (check_password(input)) {
        printf("Access granted! Flag: tomskfsp{%s}\n", input);
        return 0;
    }
    printf("Access denied\n");
    return 1;
}
