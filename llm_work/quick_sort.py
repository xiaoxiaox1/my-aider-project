def quick_sort(arr):
    """
    快速排序：递归实现，返回新排序列表
    :param arr: 待排序列表
    :return: 排序后的新列表
    """
    if len(arr) <= 1:
        return arr
    
    pivot = arr[len(arr) // 2]  # 选择中间元素作为基准
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    
    return quick_sort(left) + middle + quick_sort(right)


def quick_sort_inplace(arr, low=0, high=None):
    """
    原地快速排序（优化版，减少内存开销）
    :param arr: 待排序列表
    :param low: 起始索引
    :param high: 结束索引
    """
    if high is None:
        high = len(arr) - 1
    if low < high:
        pivot_index = partition(arr, low, high)
        quick_sort_inplace(arr, low, pivot_index - 1)
        quick_sort_inplace(arr, pivot_index + 1, high)


def partition(arr, low, high):
    """
    分区函数：以最后一个元素为基准，返回基准最终位置
    """
    pivot = arr[high]
    i = low - 1
    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1


# 示例用法
if __name__ == "__main__":
    # 测试数据
    test_list = [64, 34, 25, 12, 22, 11, 90, 5]
    
    print(f"原始列表: {test_list}")
    
    # 测试非原地版本
    sorted_list = quick_sort(test_list)
    print(f"排序后（新列表）: {sorted_list}")
    
    # 测试原地版本
    test_list_copy = test_list.copy()
    quick_sort_inplace(test_list_copy)
    print(f"排序后（原地）: {test_list_copy}")
    # 验证原地排序返回值为 None（符合预期）