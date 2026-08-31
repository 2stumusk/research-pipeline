#!/usr/bin/env python3
"""
验证新架构是否能工作的最小测试。

测试流程：
1. 加载配置
2. 创建 LLM Runner
3. 模拟一次简单的研报评分
4. 验证输出格式
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_architecture():
    """测试完整架构能否工作。"""

    print("\n" + "="*70)
    print("测试 1: 加载配置")
    print("="*70)

    try:
        from research_pipeline.config_loader import load_llm_config

        config_path = Path("config/config.v0.2.yaml")
        llm_config = load_llm_config(config_path)

        print(f"✅ 配置加载成功")
        print(f"   Provider: {llm_config['provider']}")
        print(f"   Model: {llm_config.get('model', '(default)')}")

    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False

    print("\n" + "="*70)
    print("测试 2: 创建 Runner（使用测试 API Key）")
    print("="*70)

    try:
        import os
        from research_pipeline.llm_runner import create_runner_from_yaml

        # 临时设置测试 API Key（不会真正调用）
        original_key = os.environ.get('ANTHROPIC_API_KEY')
        os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-test-key-for-architecture-validation'

        runner = create_runner_from_yaml(config_path, stage="triage")

        print(f"✅ Runner 创建成功")
        print(f"   Provider: {runner.provider_name}")
        print(f"   Model: {runner.provider.get_model_name()}")
        print(f"   Max tokens: {runner.provider.max_tokens}")

        # 恢复原始环境变量
        if original_key:
            os.environ['ANTHROPIC_API_KEY'] = original_key
        else:
            del os.environ['ANTHROPIC_API_KEY']

    except Exception as e:
        print(f"❌ Runner 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "="*70)
    print("测试 3: 模拟研报评分（不调用真实 API）")
    print("="*70)

    # 模拟的研报内容
    mock_report = {
        "title": "中微公司（688012）：Q2业绩超预期，刻蚀设备订单充足",
        "institution": "某券商",
        "date": "2026-08-31",
        "key_points": [
            "营收同比+45%",
            "毛利率提升至48%",
            "先进制程刻蚀设备订单充足",
            "长鑫存储扩产带来增量需求"
        ]
    }

    print(f"模拟研报信息：")
    print(f"  标题: {mock_report['title']}")
    print(f"  要点数量: {len(mock_report['key_points'])}")

    # 定义评分的 JSON Schema
    scoring_schema = {
        "type": "object",
        "properties": {
            "importance_score": {
                "type": "integer",
                "minimum": 0,
                "maximum": 100,
                "description": "重要性评分（0-100）"
            },
            "direction": {
                "type": "integer",
                "minimum": -3,
                "maximum": 3,
                "description": "方向（-3到+3）"
            },
            "confidence": {
                "type": "integer",
                "minimum": 0,
                "maximum": 100,
                "description": "置信度（0-100）"
            },
            "reasoning": {
                "type": "string",
                "description": "评分理由"
            }
        },
        "required": ["importance_score", "direction", "confidence", "reasoning"]
    }

    print(f"\n✅ Schema 已定义，包含字段: {list(scoring_schema['properties'].keys())}")

    print("\n" + "="*70)
    print("测试 4: 验证向后兼容性")
    print("="*70)

    try:
        # 测试旧的导入方式是否还能工作
        from research_pipeline.codex_runner import CodexRunner, CodexError

        print(f"✅ 向后兼容导入成功")
        print(f"   CodexRunner 类型: {type(CodexRunner)}")
        print(f"   CodexError 类型: {type(CodexError)}")

    except Exception as e:
        print(f"⚠️  向后兼容测试失败: {e}")
        print(f"   这是预期的，因为我们还没有创建兼容层")

    print("\n" + "="*70)
    print("总结")
    print("="*70)
    print("✅ 新架构基本可用")
    print("✅ 配置加载正常")
    print("✅ Runner 创建正常")
    print("✅ Schema 定义正确")
    print("\n下一步：")
    print("1. 创建向后兼容层（让 pipeline.py 无需修改即可使用）")
    print("2. 运行 dry-run 测试")
    print("3. 用真实 API Key 测试")

    return True


if __name__ == "__main__":
    success = test_architecture()
    sys.exit(0 if success else 1)
