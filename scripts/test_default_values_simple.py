"""
简单测试：验证默认值修复

检查代码逻辑，确保不会设置默认值
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def test_code_logic():
    """测试代码逻辑"""
    
    print("=" * 80)
    print("测试：检查asset_extraction_service.py中的默认值逻辑")
    print("=" * 80)
    
    # 读取文件内容
    file_path = Path(__file__).parent / "app" / "services" / "asset_extraction_service.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否还有默认值设置
    issues = []
    
    # 检查1: 不应该有 'age_range or "30-40"'
    if 'age_range or "30-40"' in content:
        issues.append("❌ 发现默认年龄段: age_range or \"30-40\"")
    else:
        print("✅ 没有发现默认年龄段设置")
    
    # 检查2: 不应该有 'family_structure or "single"'
    if 'family_structure or "single"' in content:
        issues.append("❌ 发现默认家庭结构: family_structure or \"single\"")
    else:
        print("✅ 没有发现默认家庭结构设置")
    
    # 检查3: 应该有条件检查 'if age_range and family_structure:'
    if 'if age_range and family_structure:' in content:
        print("✅ 发现正确的条件检查: if age_range and family_structure:")
    else:
        issues.append("❌ 没有发现条件检查: if age_range and family_structure:")
    
    # 检查4: 应该有日志说明缺少必需字段
    if 'missing required fields' in content:
        print("✅ 发现缺少必需字段的日志")
    else:
        issues.append("❌ 没有发现缺少必需字段的日志")
    
    # 检查5: 不应该有 "Create profile if we have at least one meaningful field"
    if 'Create profile if we have at least one meaningful field' in content:
        issues.append("❌ 发现旧的注释: 'Create profile if we have at least one meaningful field'")
    else:
        print("✅ 没有发现旧的注释")
    
    # 检查6: 应该有新的注释说明只在有必需字段时创建
    if 'Only create profile if we have REQUIRED fields' in content:
        print("✅ 发现新的注释: 'Only create profile if we have REQUIRED fields'")
    else:
        issues.append("❌ 没有发现新的注释")
    
    print("\n" + "=" * 80)
    
    if issues:
        print("❌ 发现问题:")
        for issue in issues:
            print(f"  {issue}")
        print("\n修复失败！")
        return False
    else:
        print("✅ 所有检查通过！默认值问题已修复！")
        print("\n修复内容:")
        print("  1. 移除了 age_range 的默认值 \"30-40\"")
        print("  2. 移除了 family_structure 的默认值 \"single\"")
        print("  3. 添加了条件检查：只有当 age_range 和 family_structure 都存在时才创建 profile")
        print("  4. 添加了日志说明缺少必需字段时跳过创建")
        return True


def show_fix_details():
    """显示修复的详细内容"""
    
    print("\n" + "=" * 80)
    print("修复详情")
    print("=" * 80)
    
    print("\n修复前的代码:")
    print("-" * 80)
    print("""
    # 旧代码（有问题）:
    if any([age_range, family_structure, risk_preference, occupation, income_range, monthly_expense]):
        profile = UserProfile(
            user_id=user_id,
            age_range=age_range or "30-40",  # ❌ 默认值
            family_structure=family_structure or "single",  # ❌ 默认值
            risk_preference=risk_preference or "moderate",
            ...
        )
    """)
    
    print("\n修复后的代码:")
    print("-" * 80)
    print("""
    # 新代码（已修复）:
    if age_range and family_structure:  # ✅ 必须都存在
        profile = UserProfile(
            user_id=user_id,
            age_range=age_range,  # ✅ 不使用默认值
            family_structure=family_structure,  # ✅ 不使用默认值
            risk_preference=risk_preference or "moderate",  # ✅ 风险偏好可以有默认值
            ...
        )
    else:
        logger.info(f"Skipping UserProfile creation - missing required fields")
    """)
    
    print("\n" + "=" * 80)
    print("修复原理")
    print("=" * 80)
    print("""
1. 问题根源:
   - 旧代码在用户没有提供年龄和家庭结构时，会自动填充默认值
   - 这导致系统"假装"知道用户的年龄和家庭结构，但实际上是错误的

2. 修复方案:
   - 只有当用户明确提供了年龄和家庭结构时，才创建 UserProfile
   - 如果缺少这些信息，系统会等待用户提供，而不是假设默认值

3. 为什么 risk_preference 可以有默认值:
   - 风险偏好是一个可以合理假设的字段（大多数人是 moderate）
   - 年龄和家庭结构是事实性信息，不能假设

4. 影响:
   - 用户首次对话时，如果没有提供年龄和家庭结构，Fact Sheet 会显示"暂无用户画像"
   - 这是正确的行为，因为我们确实不知道用户的年龄和家庭结构
   - LLM 仍然可以从对话历史中理解用户信息（Plan E）
    """)


if __name__ == "__main__":
    result = test_code_logic()
    
    if result:
        show_fix_details()
    
    print("\n" + "=" * 80)
    sys.exit(0 if result else 1)
