#include <iostream>
#include <vector>
#include <string>

// 简单的 C++ 程序：计算斐波那契数列前 N 项

define MAX_N 20

int main() {
    std::cout << "计算斐波那契数列前 " << MAX_N << " 项：\n";

    std::vector<long long> fib(MAX_N);
    fib[0] = 0;
    fib[1] = 1;

    for (int i = 2; i < MAX_N; ++i) {
        fib[i] = fib[i-1] + fib[i-2];
    }

    for (int i = 0; i < MAX_N; ++i) {
        std::cout << "F(" << i << ") = " << fib[i] << std::endl;
    }

    return 0;
}