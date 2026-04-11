"""
改进的测试脚本：自动处理rdt路径问题

运行方式:
    cd /Users/lillianliao/notion_rag/universal_content_orchestrator
    python tests/test_new_sources_v2.py
"""

import sys
import os
import subprocess

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def find_rdt_path():
    """自动查找rdt命令的路径"""
    # 方法1: 从PATH中查找
    try:
        result = subprocess.run(['which', 'rdt'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass

    # 方法2: 从pipx环境中查找
    try:
        result = subprocess.run(
            ['python', '-m', 'pipx', 'environment', '--value', 'VENV_REALPATH'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            venv_path = result.stdout.strip().split('\n')[0]
            rdt_path = os.path.join(venv_path, 'rdt-cli', 'bin', 'rdt')
            if os.path.exists(rdt_path):
                return rdt_path
    except:
        pass

    # 方法3: 已知的常见路径
    common_paths = [
        os.path.expanduser('~/.local/pipx/venvs/rdt-cli/bin/rdt'),
        os.path.expanduser('~/.local/bin/rdt'),
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path

    return None


def patch_reddit_source(rdt_path):
    """临时修改reddit_source.py中的rdt命令路径"""
    reddit_source_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'src/sources/reddit_source.py'
    )

    with open(reddit_source_path, 'r') as f:
        content = f.read()

    # 检查是否已经patch过了
    if 'RDT_PATH' in content:
        return rdt_path

    # 在文件开头添加rdt路径配置
    patch = f'''
import subprocess
import os

# 自动检测的rdt路径
RDT_PATH = "{rdt_path}"
'''

    # 替换import subprocess部分
    content = content.replace('import subprocess', patch)
    content = content.replace("subprocess.run(['rdt',", f"subprocess.run([RDT_PATH,")
    content = content.replace("cmd = [\n        'rdt',", f"cmd = [\n        RDT_PATH,")

    with open(reddit_source_path, 'w') as f:
        f.write(content)

    return rdt_path


def test_v2ex():
    """测试V2EX数据源（最简单，不需要额外依赖）"""
    print("🧪 测试 V2EX 数据源")
    print("=" * 80)

    from src.sources.v2ex_source import V2EXSource

    try:
        source = V2EXSource(node_ids=['68'])  # AI节点
        events = source.fetch(limit=2)

        print(f"\n✅ 获取到 {len(events)} 个V2EX帖子\n")

        for i, event in enumerate(events, 1):
            print(f"帖子 #{i}:")
            print(f"  ID: {event.id}")
            print(f"  标题: {event.title[:60]}...")
            print(f"  URL: {event.url}")
            print(f"  来源: {event.source_channel}")
            print(f"  时间: {event.timestamp}")
            print()

        return True, events

    except Exception as e:
        print(f"❌ V2EX测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, []


def test_youtube():
    """测试YouTube数据源"""
    print("\n🧪 测试 YouTube 数据源")
    print("=" * 80)

    from src.sources.youtube_source import YouTubeSource

    try:
        # 使用搜索模式
        source = YouTubeSource(search_queries=['AI tutorial'])
        events = source.fetch(limit=1)

        print(f"\n✅ 获取到 {len(events)} 个YouTube视频\n")

        for i, event in enumerate(events, 1):
            print(f"视频 #{i}:")
            print(f"  ID: {event.id}")
            print(f"  标题: {event.title[:60]}...")
            print(f"  URL: {event.url}")
            print(f"  来源: {event.source_channel}")
            print()

        return True, events

    except FileNotFoundError:
        print(f"❌ 错误: yt-dlp 未安装")
        print(f"   请运行: pip install yt-dlp")
        return False, []
    except Exception as e:
        print(f"❌ YouTube测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, []


def test_reddit(rdt_path):
    """测试Reddit数据源"""
    print("\n🧪 测试 Reddit 数据源")
    print("=" * 80)

    if not rdt_path:
        print(f"❌ 错误: 无法找到rdt命令")
        print(f"   请运行: python -m pipx install rdt-cli")
        return False, []

    print(f"📌 使用rdt路径: {rdt_path}")

    # Patch the source
    patch_reddit_source(rdt_path)

    from src.sources.reddit_source import RedditSource

    try:
        source = RedditSource(subreddits=['MachineLearning'])
        events = source.fetch(limit=2)

        print(f"\n✅ 获取到 {len(events)} 个Reddit帖子\n")

        for i, event in enumerate(events, 1):
            print(f"帖子 #{i}:")
            print(f"  ID: {event.id}")
            print(f"  标题: {event.title[:60]}...")
            print(f"  URL: {event.url}")
            print(f"  来源: {event.source_channel}")
            if event.score:
                print(f"  评分: {event.score}")
            print()

        return True, events

    except Exception as e:
        print(f"❌ Reddit测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, []


def main():
    """主测试函数"""
    print("🚀 开始测试新添加的数据源（改进版）")
    print("=" * 80)

    # 查找rdt路径
    rdt_path = find_rdt_path()
    if rdt_path:
        print(f"✅ 找到rdt: {rdt_path}")
    else:
        print(f"⚠️  未找到rdt命令，Reddit测试将被跳过")
    print("=" * 80)

    results = {}
    all_events = {}

    # 测试V2EX（最简单）
    results['v2ex'], all_events['v2ex'] = test_v2ex()

    # 测试YouTube
    results['youtube'], all_events['youtube'] = test_youtube()

    # 测试Reddit（如果rdt可用）
    if rdt_path:
        results['reddit'], all_events['reddit'] = test_reddit(rdt_path)
    else:
        results['reddit'] = False
        all_events['reddit'] = []

    # 汇总结果
    print("\n" + "=" * 80)
    print("📊 测试结果汇总")
    print("=" * 80)

    for source, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        event_count = len(all_events.get(source, []))
        print(f"  {source.upper():10s}: {status:8s} (获取 {event_count} 条)")

    print("=" * 80)

    # 统计总事件数
    total_events = sum(len(events) for events in all_events.values())
    print(f"📦 总共获取 {total_events} 条原始事件")

    # 详细输出前3条事件
    if total_events > 0:
        print("\n📋 部分事件预览（前3条）:")
        print("-" * 80)
        count = 0
        for source, events in all_events.items():
            for event in events:
                if count >= 3:
                    break
                print(f"\n[{source.upper()}] {event.title[:70]}")
                print(f"URL: {event.url}")
                count += 1

    print("\n" + "=" * 80)

    all_passed = all(results.values())
    if all_passed:
        print("🎉 所有数据源测试通过！")
        return 0
    else:
        failed = [s for s, p in results.items() if not p]
        print(f"⚠️  部分数据源测试失败: {', '.join(failed)}")
        return 1


if __name__ == "__main__":
    exit(main())
