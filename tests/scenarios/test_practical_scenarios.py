"""
UCO 实用测试场景

针对AI猎头业务的实际需求设计的测试场景，帮助你验证新数据源的价值。

运行方式:
    cd /Users/lillianliao/notion_rag/universal_content_orchestrator
    python tests/scenarios/test_practical_scenarios.py
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.sources.youtube_source import YouTubeSource
from src.sources.v2ex_source import V2EXSource


def print_header(title: str):
    """打印标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_section(title: str):
    """打印小节标题"""
    print(f"\n{'─' * 80}")
    print(f"  {title}")
    print('─' * 80)


# ============================================================================
# 场景1: AI技术趋势监控
# ============================================================================

def scenario_1_ai_trends_monitoring():
    """
    场景1: AI技术趋势监控

    业务价值:
        - 及时了解AI领域最新技术动向
        - 发现新兴技术框架和工具
        - 为候选人技能评估提供参考

    数据源:
        - YouTube: 搜索AI相关教程和分享
        - V2EX: 监控AI节点讨论
    """
    print_header("场景1: AI技术趋势监控")

    print("📊 监控目标:")
    print("  - LLM/Agent相关技术视频")
    print("  - 中文AI社区讨论热点")
    print("  - 新兴技术框架趋势")

    # YouTube: 监控AI技术视频
    print_section("1.1 YouTube AI技术视频")
    youtube = YouTubeSource(
        search_queries=[
            'LLM tutorial',
            'AI agent development',
            'RAG implementation'
        ]
    )

    try:
        youtube_events = youtube.fetch(limit=3)
        print(f"✅ 获取到 {len(youtube_events)} 个AI技术视频\n")

        for i, event in enumerate(youtube_events, 1):
            print(f"视频 #{i}:")
            print(f"  标题: {event.title}")
            print(f"  链接: {event.url}")
            print(f"  来源: {event.source_channel}")
            print()

    except Exception as e:
        print(f"❌ YouTube获取失败: {e}")

    # V2EX: 监控AI社区讨论
    print_section("1.2 V2EX AI社区讨论")
    v2ex = V2EXSource(
        node_ids=['68']  # 人工智能节点
    )

    try:
        v2ex_events = v2ex.fetch(limit=5)
        print(f"✅ 获取到 {len(v2ex_events)} 个AI讨论帖\n")

        for i, event in enumerate(v2ex_events, 1):
            print(f"讨论 #{i}:")
            print(f"  标题: {event.title}")
            print(f"  链接: {event.url}")
            if event.score:
                print(f"  回复数: {event.score}")
            print()

    except Exception as e:
        print(f"❌ V2EX获取失败: {e}")

    # 分析总结
    print_section("1.3 趋势分析")
    total_videos = len(youtube_events) if 'youtube_events' in locals() else 0
    total_discussions = len(v2ex_events) if 'v2ex_events' in locals() else 0

    print(f"📈 本时段监控结果:")
    print(f"  - AI技术视频: {total_videos} 个")
    print(f"  - AI社区讨论: {total_discussions} 个")
    print(f"  - 总计情报点: {total_videos + total_discussions} 个")

    print("\n💡 业务应用建议:")
    print("  1. 关注高频技术关键词，了解市场需求")
    print("  2. 发现新兴技术框架，提前储备相关知识")
    print("  3. 为候选人技能评估提供技术参考")


# ============================================================================
# 场景2: 技术教程自动化总结
# ============================================================================

def scenario_2_tutorial_automation():
    """
    场景2: 技术教程自动化总结

    业务价值:
        - 自动收集技术教程资源
        - 节省手动搜索时间
        - 建立知识库储备

    数据源:
        - YouTube: 搜索Python/机器学习教程
        - V2EX: 监控程序员节点和Python节点
    """
    print_header("场景2: 技术教程自动化总结")

    print("📚 学习目标:")
    print("  - Python高级教程")
    print("  - 机器学习实战")
    print("  - 程序员技能提升")

    # YouTube: 技术教程
    print_section("2.1 YouTube技术教程")
    youtube = YouTubeSource(
        search_queries=[
            'Python advanced tutorial',
            'Machine learning course',
            'LLM fine-tuning tutorial'
        ]
    )

    try:
        youtube_events = youtube.fetch(limit=3)
        print(f"✅ 获取到 {len(youtube_events)} 个教程视频\n")

        for i, event in enumerate(youtube_events, 1):
            print(f"教程 #{i}:")
            print(f"  标题: {event.title[:70]}...")
            print(f"  链接: {event.url}")
            print()

    except Exception as e:
        print(f"❌ YouTube获取失败: {e}")

    # V2EX: 技术讨论
    print_section("2.2 V2EX技术社区")
    v2ex = V2EXSource(
        node_ids=['4', '63']  # Python、程序员
    )

    try:
        v2ex_events = v2ex.fetch(limit=5)
        print(f"✅ 获取到 {len(v2ex_events)} 个技术讨论\n")

        for i, event in enumerate(v2ex_events, 1):
            print(f"讨论 #{i}:")
            print(f"  标题: {event.title[:70]}...")
            print(f"  链接: {event.url}")
            print()

    except Exception as e:
        print(f"❌ V2EX获取失败: {e}")

    print_section("2.3 学习资源汇总")
    print("💡 应用建议:")
    print("  1. 将优质教程加入收藏，建立学习计划")
    print("  2. 结合社区讨论，了解实战经验")
    print("  3. 定期更新知识库，保持技术敏感度")


# ============================================================================
# 场景3: 中英文技术社区对比
# ============================================================================

def scenario_3_community_comparison():
    """
    场景3: 中英文技术社区对比

    业务价值:
        - 了解国内外技术关注点差异
        - 发现本土化技术趋势
        - 更精准地定位候选人背景

    数据源:
        - YouTube: 英文技术内容
        - V2EX: 中文技术社区
    """
    print_header("场景3: 中英文技术社区对比")

    print("🌍 对比维度:")
    print("  - 英文社区: YouTube技术视频")
    print("  - 中文社区: V2EX技术讨论")
    print("  - 分析: 关注点差异和趋势")

    # 同一技术主题在两个平台的表现
    topic = "LLM application"

    print_section(f"3.1 主题: {topic}")

    # YouTube
    print(f"\n📺 YouTube (英文):")
    youtube = YouTubeSource(search_queries=['LLM application tutorial'])

    try:
        youtube_events = youtube.fetch(limit=2)
        print(f"  获取 {len(youtube_events)} 个视频")

        for event in youtube_events:
            # 提取关键词
            title_lower = event.title.lower()
            keywords = []
            if 'tutorial' in title_lower:
                keywords.append('教程')
            if 'production' in title_lower:
                keywords.append('生产环境')
            if 'api' in title_lower:
                keywords.append('API')

            print(f"  - {event.title[:60]}...")
            if keywords:
                print(f"    关键词: {', '.join(keywords)}")

    except Exception as e:
        print(f"  ❌ 获取失败: {e}")

    # V2EX
    print(f"\n💬 V2EX (中文):")
    v2ex = V2EXSource(node_ids=['68'])  # AI节点

    try:
        v2ex_events = v2ex.fetch(limit=3)
        print(f"  获取 {len(v2ex_events)} 个讨论")

        for event in v2ex_events:
            # 提取关键词
            title_lower = event.title.lower()
            keywords = []
            if 'api' in title_lower:
                keywords.append('API')
            if '应用' in title_lower or 'application' in title_lower:
                keywords.append('应用')
            if '部署' in title_lower:
                keywords.append('部署')

            print(f"  - {event.title[:60]}...")
            if keywords:
                print(f"    关键词: {', '.join(keywords)}")

    except Exception as e:
        print(f"  ❌ 获取失败: {e}")

    print_section("3.2 对比分析")
    print("📊 观察要点:")
    print("  1. 英文社区更偏向:")
    print("     - 技术教程和最佳实践")
    print("     - 生产环境部署经验")
    print("     - API使用和集成")
    print()
    print("  2. 中文社区更关注:")
    print("     - 本土化应用场景")
    print("     - 实际部署问题")
    print("     - 行业应用案例")
    print()
    print("💡 猎头应用:")
    print("  - 根据候选人技术背景，匹配合适的社区资源")
    print("  - 了解不同技术栈的国内外发展差异")
    print("  - 为候选人提供更精准的技术评估")


# ============================================================================
# 场景4: 快速情报收集（适合日常使用）
# ============================================================================

def scenario_4_daily_intelligence():
    """
    场景4: 快速情报收集

    业务价值:
        - 每日快速了解技术动态
        - 发现高价值内容
        - 为内容创作提供素材

    数据源:
        - YouTube + V2EX 混合
    """
    print_header("场景4: 每日快速情报收集")

    print("⏰ 适用场景: 每日早晨/每周定期执行")
    print("📊 收集目标: 快速获取高价值技术情报")

    # 同时获取多个来源
    all_events = []

    # YouTube: AI/技术趋势
    print_section("4.1 收集中...")
    youtube = YouTubeSource(
        search_queries=['AI news', 'tech trends']
    )

    try:
        youtube_events = youtube.fetch(limit=2)
        all_events.extend(youtube_events)
        print(f"✅ YouTube: {len(youtube_events)} 条")
    except:
        print("⚠️  YouTube: 获取失败")

    # V2EX: 技术社区
    v2ex = V2EXSource(
        node_ids=['68', '63', '8']  # AI、程序员、分享创造
    )

    try:
        v2ex_events = v2ex.fetch(limit=3)
        all_events.extend(v2ex_events)
        print(f"✅ V2EX: {len(v2ex_events)} 条")
    except:
        print("⚠️  V2EX: 获取失败")

    # 汇总展示
    print_section("4.2 情报汇总")
    print(f"📦 总计收集: {len(all_events)} 条情报\n")

    for i, event in enumerate(all_events, 1):
        print(f"{i}. [{event.source_channel}] {event.title[:70]}")
        print(f"   {event.url}")
        print()

    print_section("4.3 快速行动")
    print("🎯 建议操作:")
    print("  1. 标记高价值内容 (收藏/转发)")
    print("  2. 提取关键信息 (笔记/摘要)")
    print("  3. 分享给团队 (协作/讨论)")


# ============================================================================
# 主函数
# ============================================================================

def main():
    """主测试函数"""
    print("\n" + "🚀" * 40)
    print("  UCO 实用测试场景 - AI猎头业务版")
    print("🚀" * 40)

    print("\n📋 可用场景:")
    print("  1. AI技术趋势监控")
    print("  2. 技术教程自动化总结")
    print("  3. 中英文技术社区对比")
    print("  4. 每日快速情报收集")
    print("  5. 运行所有场景")

    # 简单的交互式选择
    try:
        choice = input("\n请选择场景 (1-5, 默认5): ").strip()

        if not choice:
            choice = "5"

        choice = int(choice)

        if choice == 1:
            scenario_1_ai_trends_monitoring()
        elif choice == 2:
            scenario_2_tutorial_automation()
        elif choice == 3:
            scenario_3_community_comparison()
        elif choice == 4:
            scenario_4_daily_intelligence()
        elif choice == 5:
            # 运行所有场景
            scenario_1_ai_trends_monitoring()
            scenario_2_tutorial_automation()
            scenario_3_community_comparison()
            scenario_4_daily_intelligence()
        else:
            print("❌ 无效选择")
            return 1

    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        return 1
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return 1

    print("\n" + "=" * 80)
    print("  ✅ 测试场景执行完成")
    print("=" * 80 + "\n")

    print("📝 后续建议:")
    print("  1. 根据业务需求调整搜索关键词")
    print("  2. 将高价值场景集成到日常流程")
    print("  3. 结合LLM进行内容自动总结")
    print("  4. 建立情报库，定期回顾分析")

    return 0


if __name__ == "__main__":
    exit(main())
