def heapify(arr, n, i):
    """
    维护堆的性质：以 i 为根的子树满足最大堆性质
    :param arr: 数组
    :param n: 堆的大小
    :param i: 当前根节点索引
    """
    largest = i  # 初始化最大值为根
    left = 2 * i + 1    # 左子节点
    right = 2 * i + 2   # 右子节点

    # 如果左子节点存在且大于根
    if left < n and arr[left] > arr[largest]:
        largest = left

    # 如果右子节点存在且大于当前最大值
    if right < n and arr[right] > arr[largest]:
        largest = right

    # 如果最大值不是根，则交换并继续向下调整
    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        heapify(arr, n, largest)


def heap_sort(arr):
    """
    堆排序：将数组构建成最大堆，然后逐个提取最大值
    :param arr: 待排序列表
    :return: 排序后的列表（原地修改）
    """
    n = len(arr)

    # 构建最大堆：从最后一个非叶子节点开始，自底向上调整
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i)

    # 逐个提取最大值（即根节点），放到末尾
    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]  # 将最大值移到末尾
        heapify(arr, i, 0)  # 重新调整堆（大小为 i）

    return arr


def heap_sort_copy(arr):
    """
    堆排序：返回新列表，不修改原数组
    :param arr: 待排序列表
    :return: 排序后的新列表
    """
    arr_copy = arr.copy()
    return heap_sort(arr_copy)


# 示例用法
if __name__ == "__main__":
    # 测试数据
    test_list = [64, 34, 25, 12, 22, 11, 90, 5]
    
    print(f"原始列表: {test_list}")
    
    # 测试原地堆排序
    arr_copy = test_list.copy()
    heap_sort(arr_copy)
    print(f"堆排序后（原地）: {arr_copy}")
    
    # 测试返回新列表的堆排序
    sorted_list = heap_sort_copy(test_list)
    print(f"堆排序后（新列表）: {sorted_list}")
    
    # 验证与快速排序结果一致
    from quick_sort import quick_sort
    quick_sorted = quick_sort(test_list)
    print(f"快速排序结果: {quick_sorted}")
    print(f"堆排序结果一致: {sorted_list == quick_sorted}")
    # 验证堆排序与快速排序结果完全一致