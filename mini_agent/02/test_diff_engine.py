from diff_engine import apply_search_replace, validate_python_ast


def test_tier1_exact_match():
    file_content = "def add(a, b):\n    return a + b\n"
    search = "return a + b"
    replace = "return a + b + 0"
    
    success, result, tier = apply_search_replace(file_content, search, replace)
    assert success is True
    assert "return a + b + 0" in result
    assert tier == "Tier 1 (Exact Match)"


def test_tier2_crlf_and_trailing_whitespace():
    # 模拟目标文件有末尾空格和 CRLF 换行
    file_content = "def calculate():\r\n    x = 1   \r\n    y = 2  \r\n    return x + y\r\n"
    # 模型输出的 Search 块只有干净的 LF 换行与正确的 4 空格缩进，但没有末尾空格
    search = "    x = 1\n    y = 2"
    replace = "    x = 10\n    y = 20"

    success, result, tier = apply_search_replace(file_content, search, replace)
    assert success is True
    assert "x = 10" in result
    assert "y = 20" in result
    assert "Tier 2" in tier



def test_tier3_indentation_auto_alignment():
    # 目标文件缩进为 8 个空格
    file_content = "class Service:\n        def process(self):\n            val = 42\n            return val\n"
    # 模型输出的 Search/Replace 块误用了 4 个空格缩进
    search = "def process(self):\n    val = 42"
    replace = "def process(self):\n    val = 100"

    success, result, tier = apply_search_replace(file_content, search, replace)
    assert success is True
    assert "val = 100" in result
    # 验证缩进是否被自动修正为 8 个空格
    assert "        def process(self):\n            val = 100" in result
    assert "Tier 3" in tier


def test_ast_syntax_error_rejection():
    file_content = "def hello():\n    print('Hello World')\n"
    search = "print('Hello World')"
    # 注入一个破坏 Python 语法的无效代码 (缺少闭合括号)
    replace = "print('Hello World'"

    success, result, tier = apply_search_replace(file_content, search, replace, filepath="app.py")
    assert success is False
    assert "修改拒绝" in result
    assert "AST 语法校验" in result


if __name__ == "__main__":
    print("=== 运行 Tier 1 测试 ===")
    test_tier1_exact_match()
    print("PASS: Tier 1 精确匹配通过")

    print("\n=== 运行 Tier 2 测试 ===")
    test_tier2_crlf_and_trailing_whitespace()
    print("PASS: Tier 2 CRLF 与空格归一化通过")

    print("\n=== 运行 Tier 3 测试 ===")
    test_tier3_indentation_auto_alignment()
    print("PASS: Tier 3 相对缩进自动补齐通过")

    print("\n=== 运行 Tier 4 测试 ===")
    test_ast_syntax_error_rejection()
    print("PASS: Tier 4 AST 语法防御拦截通过")

    print("\n[SUCCESS] 4 级高容错测试 100% 全部通过！")


