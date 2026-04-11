import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from src.publishers.opencli_xhs_adapter import OpenCLIXiaohongshuPublisher

content = """不用写代码也能量化交易？港大团队开源了一个 AI 交易 Agent！

最近发现一个非常有意思的开源项目——Vibe-Trading，把"Vibe Coding"的理念搬到了量化投资领域。

🎯 它能做什么？
一句话：用自然语言描述你的交易想法，AI 帮你自动写策略代码 → 回测 → 出报告 → 导出到 TradingView。

比如你只需要说：
"帮我回测过去一年 BTC 的 MACD 策略，每次信号加仓 10%"

AI Agent 就会自动：
1. 调用数据源获取行情（自带 A 股/港美股/Crypto 免费数据源）
2. 生成策略代码并跑回测
3. 输出收益率、夏普比率、最大回撤等关键指标

🤖 团队预设：投资委员会模式
最精彩的是它内置了多 Agent 协作模式。例如"投资委员会"，由 4 个 AI 分别扮演：
- 🐂 多头分析师：做看多研究
- 🐻 空头分析师：做看空研究
- 🛡️ 风控官：独立审查双方论点并控制仓位
- 💼 基金经理：综合判断做最后决策（也就是买不买、买多少）

这 4 个 AI 会通过 DAG 有向无环图进行编排，多空先并行研究，然后交由风控和决策。

💡 适合什么人？
不仅适合想要尝试量化交易的普通人，它里面用到的三层上下文压缩、DAG 编排和渐进式技能加载，对于 AI Agent 开发者来说也是极其宝贵的参考！

🔗 项目地址：HKUDS / Vibe-Trading

#AI[话题]# #量化交易[话题]# #VibeCoding[话题]# #AIAgent[话题]# #开源项目[话题]#"""

from src.core.visual_engine import PillowVisualEngine

title = "港大开源 AI 交易 Agent"

# 动态生成纯 Python 美学卡片
visual_inst = PillowVisualEngine()
poster_path = "/Users/lillianliao/notion_rag/universal_content_orchestrator/data/assets/vibe_trading_poster.jpg"
visual_inst.generate_poster(title, "Vibe Coding 的落地：自然语言自动化策略与回测", "🚀 AI 前沿开源观察", poster_path, mode="xhs")

media = [poster_path]

print("准备发布到小红书（草稿箱）...")
pub = OpenCLIXiaohongshuPublisher()
success = pub.push(content, title, media)

if success:
    print("✅ 发布脚本执行完毕！请去网页端草稿箱查看。")
else:
    print("❌ 发布失败。")
