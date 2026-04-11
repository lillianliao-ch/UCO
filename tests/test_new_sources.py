"""
测试脚本：验证新添加的三个数据源

运行方式:
    cd /Users/lillianliao/notion_rag/universal_content_orchestrator
    python tests/test_new_sources.py

说明:
    - 测试YouTube、Reddit、V2EX三个数据源
    - 验证数据源能正常获取内容
    - 验证输出格式符合RawContentEvent规范
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sources.youtube_source import YouTubeSource
from src.sources.reddit_source import RedditSource
from src.sources.v2ex_source import V2EXSource
from src.core.schemas import RawContentEvent


def print_separator():
    """打印分隔线"""
    print("\n" + "=" * 80 + "\n")


def test_youtube_source():
    """测试YouTube数据源"""
    print("🧪 测试 YouTube 数据源")
    print_separator()

    # 使用搜索模式（不需要频道ID）
    source = YouTubeSource(
        search_queries=['AI tutorial']  # 简单搜索词
    )

    try:
        events = source.fetch(limit=2)

        print(f"✅ 获取到 {len(events)} 个YouTube视频\n")

        for i, event in enumerate(events, 1):
            print(f"视频 #{i}:")
            print(f"  ID: {event.id}")
            print(f"  标题: {event.title}")
            print(f"  来源: {event.source_channel}")
            print(f"  URL: {event.url}")
            print(f"  时间戳: {event.timestamp}")
            if event.score:
                print(f"  评分: {event.score}")
            print(f"  内容预览: {event.content[:150]}...")
            print()

        return len(events) > 0

    except FileNotFoundError as e:
        print(f"❌ 错误: yt-dlp 未安装")
        print(f"   请运行: pip install yt-dlp")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_reddit_source():
    """测试Reddit数据源"""
    print("🧪 测试 Reddit 数据源")
    print_separator()

    source = RedditSource(
        subreddits=['MachineLearning']  # 测试一个subreddit
    )

    try:
        events = source.fetch(limit=2)

        print(f"✅ 获取到 {len(events)} 个Reddit帖子\n")

        for i, event in enumerate(events, 1):
            print(f"帖子 #{i}:")
            print(f"  ID: {event.id}")
            print(f"  标题: {event.title}")
            print(f"  来源: {event.source_channel}")
            print(f"  URL: {event.url}")
            print(f"  时间戳: {event.timestamp}")
            if event.score:
                print(f"  评分: {event.score}")
            print(f"  内容预览: {event.content[:150]}...")
            print()

        return len(events) > 0

    except FileNotFoundError as e:
        print(f"❌ 错误: rdt-cli 未安装")
        print(f"   请运行: pipx install rdt-cli")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_v2ex_source():
    """测试V2EX数据源"""
    print("🧪 测试 V2EX 数据源")
    print_separator()

    source = V2EXSource(
        node_ids=['68']  # 人工智能节点
    )

    try:
        events = source.fetch(limit=3)

        print(f"✅ 获取到 {len(events)} 个V2EX帖子\n")

        for i, event in enumerate(events, 1):
            print(f"帖子 #{i}:")
            print(f"  ID: {event.id}")
            print(f"  标题: {event.title}")
            print(f"  来源: {event.source_channel}")
            print(f"  URL: {event.url}")
            print(f"  时间戳: {event.timestamp}")
            if event.score:
                print(f"  评分: {event.score}")
            print(f"  内容预览: {event.content[:150]}...")
            print()

        return len(events) > 0

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_event_schema(event: RawContentEvent) -> bool:
    """验证事件是否符合RawContentEvent规范"""
    required_fields = ['id', 'source_channel', 'title', 'content', 'url', 'timestamp']

    for field in required_fields:
        if not hasattr(event, field) or getattr(event, field) is None:
            print(f"❌ 缺少必需字段: {field}")
            return False

    return True


def main():
    """主测试函数"""
    print("🚀 开始测试新添加的数据源\n")
    print_separator()

    results = {}

    # 测试YouTube
    print("1/3 测试 YouTube 数据源")
    print_separator()
    results['youtube'] = test_youtube_source()
    print_separator()

    # 测试Reddit
    print("2/3 测试 Reddit 数据源")
    print_separator()
    results['reddit'] = test_reddit_source()
    print_separator()

    # 测试V2EX
    print("3/3 测试 V2EX 数据源")
    print_separator()
    results['v2ex'] = test_v2ex_source()
    print_separator()

    # 汇总结果
    print("📊 测试结果汇总")
    print_separator()

    for source, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {source.upper()}: {status}")

    print_separator()

    # 提供安装建议
    failed_sources = [s for s, passed in results.items() if not passed]
    if failed_sources:
        print("📝 安装建议:")
        if 'youtube' in failed_sources:
            print("  - 安装 yt-dlp: pip install yt-dlp")
        if 'reddit' in failed_sources:
            print("  - 安装 rdt-cli: pipx install rdt-cli")
        # V2EX不需要额外依赖，如果失败可能是网络问题
        if 'v2ex' in failed_sources:
            print("  - 检查网络连接或稍后重试")

    print_separator()

    all_passed = all(results.values())
    if all_passed:
        print("🎉 所有数据源测试通过！")
        return 0
    else:
        print("⚠️ 部分数据源测试失败，请根据上述建议修复")
        return 1


if __name__ == "__main__":
    exit(main())
