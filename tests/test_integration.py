"""
测试新集成的YouTube和V2EX数据源

验证pipeline配置是否正确工作
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sources.youtube_source import YouTubeSource
from src.sources.v2ex_source import V2EXSource


def test_source_refs_logic():
    """
    测试main.py中的source_refs处理逻辑
    模拟pipeline运行时的行为
    """
    print("🧪 测试新集成的数据源\n")
    print("=" * 80)

    # 模拟pipeline的source_refs
    source_refs = [
        'youtube_ai_trends',
        'v2ex_ai_discussions'
    ]

    events = []

    # 模拟main.py中的处理逻辑
    print("📡 [1] 开始从管线注册的源头抽水汇聚...\n")

    # 7. YouTube AI技术视频监控
    if "youtube_ai_trends" in source_refs:
        print("✅ 检测到 youtube_ai_trends，开始获取YouTube AI技术视频...")
        from src.sources.youtube_source import YouTubeSource
        youtube = YouTubeSource(
            search_queries=['LLM tutorial', 'AI agent development', 'RAG implementation']
        )
        youtube_events = youtube.fetch(limit=3)
        events.extend(youtube_events)
        print(f"   获取到 {len(youtube_events)} 个YouTube视频\n")

    # 8. V2EX中文技术社区监控
    if "v2ex_ai_discussions" in source_refs:
        print("✅ 检测到 v2ex_ai_discussions，开始获取V2EX AI讨论...")
        from src.sources.v2ex_source import V2EXSource
        v2ex = V2EXSource(node_ids=['68'])  # AI节点
        v2ex_events = v2ex.fetch(limit=5)
        events.extend(v2ex_events)
        print(f"   获取到 {len(v2ex_events)} 个V2EX讨论\n")

    print("=" * 80)
    print(f"📊 汇总结果:")
    print(f"   总事件数: {len(events)}")
    print(f"   来源分布:")
    print(f"     - YouTube: {len([e for e in events if 'youtube' in e.source_channel])}")
    print(f"     - V2EX: {len([e for e in events if 'v2ex' in e.source_channel])}")

    print("\n📋 事件预览（前3条）:")
    for i, event in enumerate(events[:3], 1):
        print(f"\n{i}. [{event.source_channel}]")
        print(f"   标题: {event.title[:70]}...")
        print(f"   链接: {event.url}")

    return events


def test_pipeline_config():
    """测试pipelines.yaml配置"""
    import yaml

    print("\n\n🧪 测试pipeline配置\n")
    print("=" * 80)

    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'config', 'pipelines.yaml'
    )

    with open(config_path, 'r', encoding='utf-8') as f:
        pipelines = yaml.safe_load(f)['pipelines']

    # 查找新添加的pipeline
    target_pipeline = None
    for pipeline in pipelines:
        if pipeline.get('id') == 'ai_tech_trends_monitor':
            target_pipeline = pipeline
            break

    if target_pipeline:
        print("✅ 找到新pipeline配置:")
        print(f"   ID: {target_pipeline['id']}")
        print(f"   名称: {target_pipeline['name']}")
        print(f"   描述: {target_pipeline['description']}")
        print(f"   调度时间: {target_pipeline.get('schedule_time', '未设置')}")
        print(f"   状态: {'激活' if target_pipeline.get('active') else '未激活'}")
        print(f"\n   数据源:")
        for ref in target_pipeline.get('source_refs', []):
            print(f"     - {ref}")
        print(f"\n   发布渠道:")
        for ref in target_pipeline.get('publisher_refs', []):
            print(f"     - {ref}")
        print(f"\n   Prompt模板: {target_pipeline.get('prompt_template')}")

        # 检查prompt文件是否存在
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'config', 'prompts', target_pipeline.get('prompt_template', '')
        )
        if os.path.exists(prompt_path):
            print(f"   ✅ Prompt模板文件存在")
        else:
            print(f"   ❌ Prompt模板文件不存在: {prompt_path}")

        return True
    else:
        print("❌ 未找到 ai_tech_trends_monitor pipeline")
        return False


def main():
    """主测试函数"""
    print("🚀 开始测试YouTube和V2EX集成\n")

    # 测试1: 数据源功能
    events = test_source_refs_logic()

    # 测试2: 配置文件
    config_ok = test_pipeline_config()

    # 总结
    print("\n\n" + "=" * 80)
    print("📊 测试总结")
    print("=" * 80)

    if events and config_ok:
        print("✅ 所有测试通过！")
        print(f"\n📝 下一步:")
        print("1. 运行完整pipeline测试:")
        print("   cd /Users/lillianliao/notion_rag/universal_content_orchestrator")
        print("   python main.py ai_tech_trends_monitor")
        print("\n2. 或添加到定时任务:")
        print("   查看文档: docs/SCHEDULED_TASKS.md")
        return 0
    else:
        print("❌ 部分测试失败，请检查配置")
        return 1


if __name__ == "__main__":
    exit(main())
