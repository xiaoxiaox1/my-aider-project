def matrix_multiply(A, B):
    """
    2x2 矩阵乘法
    """
    return [
        [A[0][0]*B[0][0] + A[0][1]*B[1][0], A[0][0]*B[0][1] + A[0][1]*B[1][1]],
        [A[1][0]*B[0][0] + A[1][1]*B[1][0], A[1][0]*B[0][1] + A[1][1]*B[1][1]]
    ]


def matrix_power(matrix, n):
    """
    矩阵快速幂：计算 matrix^n
    """
    if n == 1:
        return matrix
    if n % 2 == 0:
        half = matrix_power(matrix, n // 2)
        return matrix_multiply(half, half)
    else:
        return matrix_multiply(matrix, matrix_power(matrix, n - 1))


def fibonacci(n):
    """
    使用矩阵快速幂计算第 n 个斐波那契数（时间复杂度 O(log n)）
    :param n: 非负整数
    :return: 第 n 个斐波那契数
    """
    if n < 0:
        raise ValueError("n 必须是非负整数")
    if n == 0:
        return 0
    if n == 1:
        return 1

    # 基础矩阵 [[1,1],[1,0]]
    base_matrix = [[1, 1], [1, 0]]
    result_matrix = matrix_power(base_matrix, n)
    return result_matrix[0][1]

# 示例用法
if __name__ == "__main__":
    print(f"第 10 个斐波那契数是: {fibonacci(10)}")
    print(f"前 15 个斐波那契数: {[fibonacci(i) for i in range(15)]}")