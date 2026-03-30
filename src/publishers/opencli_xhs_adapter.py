import os
import subprocess
from src.publishers.base_publisher import BasePublisherAdapter

class OpenCLIXiaohongshuPublisher(BasePublisherAdapter):
    """
    Subprocess shield wrapping the volatile Node.js OpenCLI command for Xiaohongshu.
    If OpenCLI fails due to disconnected browsers, it traps the exception locally.
    """
    
    def push(self, content: str, title: str, media_paths: list[str] = []) -> bool:
        print(f"🚀 [Publisher: Xiaohongshu] 请求 OpenCLI 跨边界执行，注入草稿【{title}】")
        
        # Prepare basic publish array sequence
        cmd = [
            "npx", "--yes", "@jackwener/opencli", "xiaohongshu", "publish",
            content,
            "--title", title,
            "--draft", "true"
        ]
        
        if media_paths:
            # opencli accepts comma-separated paths or multiple args based on its implementation
            # usually it's a single --images string
            cmd.extend(["--images", media_paths[0]])
            
        try:
            subprocess.run(cmd, check=True) # Let exceptions bubble to catch block
            print(f"   ✅ [Publisher: XHS] 渲染结果已挂载，静默提交通道运作正常！")
            return True
        except subprocess.CalledProcessError as e:
            err_msg = f"子进程调用失败，可能原因是 Chrome 脱靶或 Cookie 丢失。返回码: {e.returncode}"
            print(f"   ❌ [Publisher: XHS] 熔断防护生效: {err_msg}")
            return False
        except Exception as e:
            print(f"   ❌ [Publisher: XHS] 无法预料的系统级中断: {e}")
            return False
