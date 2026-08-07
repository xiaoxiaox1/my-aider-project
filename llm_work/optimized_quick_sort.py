import random

def dual_pivot_quick_sort(arr, low=0, high=None):
    """
    双基准快速排序（Dual-Pivot Quicksort）：
    - 使用两个基准值将数组分为三部分：小于小基准、介于两基准之间、大于大基准
    - 由 Vladimir Yaroslavskiy 提出，Java 7+ 的 Arrays.sort() 默认使用此算法
    - 在大多数情况下比传统快排更快，尤其对已排序或部分排序数据
    :param arr: 待排序列表
    :param low: 起始索引
    :param high: 结束索引
    """
    if high is None:
        high = len(arr) - 1

    # 小数组使用插入排序（更高效）
    if high - low < 10:
        insertion_sort(arr, low, high)
        return

    if low < high:
        # 选择两个基准：首、中、尾三数取中，取较小和较大者
        # 保证 pivot1 <= pivot2
        pivot1_idx, pivot2_idx = median_of_three_dual(arr, low, high)
        arr[pivot1_idx], arr[low] = arr[low], arr[pivot1_idx]
        arr[pivot2_idx], arr[high] = arr[high], arr[pivot2_idx]

        # 确保 pivot1 <= pivot2
        if arr[low] > arr[high]:
            arr[low], arr[high] = arr[high], arr[low]

        # 分区：三段：[low, i), [i, j), [j, high]
        # i: 小于 pivot1 的边界
        # j: 大于 pivot2 的边界
        # k: 当前遍历位置
        i = low + 1
        j = high - 1
        k = low + 1

        while k <= j:
            if arr[k] < arr[low]:
                arr[i], arr[k] = arr[k], arr[i]
                i += 1
            elif arr[k] > arr[high]:
                arr[k], arr[j] = arr[j], arr[k]
                j -= 1
                # 注意：这里 k 不动，因为交换来的元素还未检查
                # 所以 k 保持不变，继续检查新元素
            else:
                # arr[low] <= arr[k] <= arr[high]
                k += 1

        # 将基准值放到正确位置
        arr[low], arr[i - 1] = arr[i - 1], arr[low]
        arr[high], arr[j + 1] = arr[j + 1], arr[high]

        # 递归排序三段
        dual_pivot_quick_sort(arr, low, i - 2)
        dual_pivot_quick_sort(arr, i, j)
        dual_pivot_quick_sort(arr, j + 2, high)


def median_of_three_dual(arr, low, high):
    """
    三数取中：返回首、中、尾三元素中位数的索引，用于双基准快排
    返回两个索引：较小值的索引和较大值的索引
    """
    mid = (low + high) // 2
    # 保证 arr[low] <= arr[mid] <= arr[high]
    if arr[low] > arr[mid]:
        arr[low], arr[mid] = arr[mid], arr[low]
    if arr[mid] > arr[high]:
        arr[mid], arr[high] = arr[high], arr[mid]
    if arr[low] > arr[mid]:
        arr[low], arr[mid] = arr[mid], arr[low]
    # 此时 arr[low] <= arr[mid] <= arr[high]
    # 所以较小基准是 arr[low]，较大基准是 arr[high]
    return low, high


def partition(arr, low, high):
    """
    分区函数：以最后一个元素为基准（已通过三数取中调整）
    """
    pivot = arr[high]
    i = low - 1
    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1


def insertion_sort(arr, low, high):
    """
    插入排序：用于小数组优化
    """
    for i in range(low + 1, high + 1):
        key = arr[i]
        j = i - 1
        while j >= low and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key


# 示例用法
if __name__ == "__main__":
    # 测试数据：包含已排序、逆序、重复元素
    test_cases = [
        [64, 34, 25, 12, 22, 11, 90],
        [1, 2, 3, 4, 5],
        [5, 4, 3, 2, 1],
        [3, 3, 3, 3],
        [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
    ]

    for i, test_list in enumerate(test_cases):
        arr_copy = test_list.copy()
        print(f"测试 {i+1}: 原始: {test_list}")
        optimized_quick_sort(arr_copy)
        print(f"排序后: {arr_copy}")
        print("-" * 40)