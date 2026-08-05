fn main() {
    const MAX_N: usize = 20;

    println!("计算斐波那契数列前 {} 项：", MAX_N);

    let mut fib = vec![0u64; MAX_N];
    if MAX_N > 0 {
        fib[0] = 0;
    }
    if MAX_N > 1 {
        fib[1] = 1;
    }

    for i in 2..MAX_N {
        fib[i] = fib[i-1] + fib[i-2];
    }

    for i in 0..MAX_N {
        println!("F({}) = {}", i, fib[i]);
    }
}