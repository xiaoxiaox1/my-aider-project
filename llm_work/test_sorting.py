"""测试堆排序、快速排序与归并排序的调用与对比"""

from heap_sort import heap_sort, heap_sort_copy
from quick_sort import quick_sort, quick_sort_inplace
from merge_sort import merge_sort, merge_sort_inplace, merge_sort_copy


def test_sorting_algorithms():
    """测试三种排序算法的调用方式与结果一致性"""
    # 测试数据
    test_data = [64, 34, 25, 12, 22, 11, 90, 5]
    print(f"原始数据: {test_data}")
    print("""\n--- 堆排序测试 ---""")
    
    # 测试原地堆排序
    arr1 = test_data.copy()
    heap_sort(arr1)
    print(f"堆排序（原地）: {arr1}")
    
    # 测试返回新列表的堆排序
    arr2 = heap_sort_copy(test_data)
    print(f"堆排序（新列表）: {arr2}")
    
    print("""\n--- 快速排序测试 ---""")
    
    # 测试返回新列表的快速排序
    arr3 = quick_sort(test_data)
    print(f"快速排序（新列表）: {arr3}")
    
    # 测试原地快速排序
    arr4 = test_data.copy()
    quick_sort_inplace(arr4)
    print(f"快速排序（原地）: {arr4}")
    
    print("""\n--- 归并排序测试 ---""")
    
    # 测试返回新列表的归并排序
    arr5 = merge_sort(test_data)
    print(f"归并排序（新列表）: {arr5}")
    
    # 测试原地归并排序
    arr6 = test_data.copy()
    merge_sort_inplace(arr6)
    print(f"归并排序（原地）: {arr6}")
    
    # 验证结果一致性
    print(f"\n结果一致性验证: {arr2 == arr3 == arr5 == arr6}")


def performance_comparison():
    """性能对比（大样本）"""
    import time
    import random
    
    # 生成大样本数据
    sizes = [1000, 5000, 10000]
    for n in sizes:
        data = [random.randint(1, 1000) for _ in range(n)]
        
        # 测试堆排序
        start_time = time.time()
        heap_sort(data.copy())
        heap_time = time.time() - start_time
        
        # 测试快速排序
        start_time = time.time()
        quick_sort(data)
        quick_time = time.time() - start_time
        
        # 测试归并排序
        start_time = time.time()
        merge_sort(data)
        merge_time = time.time() - start_time
        
        print(f"数据规模 {n}: 堆排序 {heap_time:.4f}s, 快速排序 {quick_time:.4f}s, 归并排序 {merge_time:.4f}s")


if __name__ == "__main__":
    test_sorting_algorithms()
    print("\n" + """\n--- 性能对比（大样本）---""")
    performance_comparison()