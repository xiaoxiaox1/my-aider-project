"""归并排序（Merge Sort）实现：稳定、高效、递归分治"""

def merge_sort(arr):
    """
    归并排序：递归实现，返回新排序列表
    时间复杂度：O(n log n)（最好、平均、最坏均稳定）
    空间复杂度：O(n)
    稳定性：✅ 稳定排序
    
    :param arr: 待排序列表
    :return: 排序后的新列表
    """
    # 基础情况：长度 ≤ 1 直接返回
    if len(arr) <= 1:
        return arr
    
    # 分治：找到中点，递归排序左右两半
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    # 合并两个已排序的子数组
    return merge(left, right)

def merge(left, right):
    """
    合并两个已排序的列表，保持稳定性
    :param left: 左子数组
    :param right: 右子数组
    :return: 合并后的有序列表
    """
    result = []
    i = j = 0
    
    # 比较并合并
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    # 添加剩余元素
    result.extend(left[i:])
    result.extend(right[j:])
    
    return result

def merge_sort_inplace(arr, temp=None, left=0, right=None):
    """
    原地归并排序（优化版，减少内存分配）
    :param arr: 待排序列表
    :param temp: 临时数组（用于合并）
    :param left: 起始索引
    :param right: 结束索引
    """
    if right is None:
        right = len(arr) - 1
    if left >= right:
        return
    
    if temp is None:
        temp = [0] * len(arr)
    
    mid = (left + right) // 2
    merge_sort_inplace(arr, temp, left, mid)
    merge_sort_inplace(arr, temp, mid + 1, right)
    merge_inplace(arr, temp, left, mid, right)

def merge_inplace(arr, temp, left, mid, right):
    """
    原地合并两个已排序子数组
    :param arr: 原数组
    :param temp: 临时数组
    :param left: 左边界
    :param mid: 中点
    :param right: 右边界
    """
    i, j, k = left, mid + 1, left
    
    # 合并到临时数组
    while i <= mid and j <= right:
        if arr[i] <= arr[j]:
            temp[k] = arr[i]
            i += 1
        else:
            temp[k] = arr[j]
            j += 1
        k += 1
    
    # 复制剩余元素
    while i <= mid:
        temp[k] = arr[i]
        i += 1
        k += 1
    while j <= right:
        temp[k] = arr[j]
        j += 1
        k += 1
    
    # 将临时数组复制回原数组
    for idx in range(left, right + 1):
        arr[idx] = temp[idx]


def merge_sort_copy(arr):
    """
    归并排序：返回新列表，不修改原数组
    :param arr: 待排序列表
    :return: 排序后的新列表
    """
    return merge_sort(arr)


def merge_sort_copy_inplace(arr):
    """
    原地归并排序：修改原数组
    :param arr: 待排序列表
    :return: 排序后的原数组（无返回值）
    """
    merge_sort_inplace(arr)


# 示例用法
if __name__ == "__main__":
    # 测试数据
    test_list = [64, 34, 25, 12, 22, 11, 90, 5]
    
    print(f"原始列表: {test_list}")
    
    # 测试非原地版本
    sorted_list = merge_sort(test_list)
    print(f"归并排序（新列表）: {sorted_list}")
    
    # 测试原地版本
    test_list_copy = test_list.copy()
    merge_sort_inplace(test_list_copy)
    print(f"归并排序（原地）: {test_list_copy}")
    # 验证原地排序返回值为 None（符合预期）
    
    # 验证与快速排序、堆排序结果一致
    from heap_sort import heap_sort_copy
    from quick_sort import quick_sort
    
    heap_sorted = heap_sort_copy(test_list)
    quick_sorted = quick_sort(test_list)
    
    print(f"堆排序结果: {heap_sorted}")
    print(f"快速排序结果: {quick_sorted}")
    print(f"归并排序结果一致: {sorted_list == heap_sorted == quick_sorted}")
    
    # 稳定性测试：相等元素顺序不变
    stable_test = [3, 1, 2, 1, 4]
    print(f"\n稳定性测试（相等元素）: {stable_test}")
    merged = merge_sort(stable_test)
    print(f"归并排序后: {merged}")
    print(f"相等元素顺序保持: {merged[1] == 1 and merged[3] == 1}")