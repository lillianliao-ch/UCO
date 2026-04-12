import os
import time
from playwright.sync_api import sync_playwright
from src.publishers.base_publisher import BasePublisherAdapter

class OpenCLIXiaohongshuPublisher(BasePublisherAdapter):
    """
    通过底层 CDP 直连本地 Chrome 的小红书发布引擎。
    完全抛弃需要 Browser Bridge 插件支持的脆弱 OpenCLI。
    """
    def __init__(self, port=9224):
        self.port = port
        self.cdp_url = f"http://localhost:{self.port}"
        
    def push(self, content: str, title: str, media_paths: list[str] = []) -> bool:
        print(f"🚀 [Publisher: Xiaohongshu] 请求 Playwright CDP 跨边界执行，注入草稿【{title}】")
        
        with sync_playwright() as p:
            try:
                browser = p.chromium.connect_over_cdp(self.cdp_url)
                context = browser.contexts[0]
                
                page = context.new_page()
                page.goto("https://creator.xiaohongshu.com/publish/publish?from=menu_left", timeout=30000)
                
                print("   ⏳ [Publisher: XHS] 等待创作者中心加载完图文组件...")
                time.sleep(5)
                
                # Check login state
                if "login" in page.url or "explore" in page.url:
                    print("   ❌ [Publisher: XHS] 致命错误：未检测到小红书登录信息！请在 Chrome 窗口扫码。")
                    return False
                    
                page.bring_to_front()
                
                # 1. 甄别发布类型，并切换正确的 UI Tab
                is_video = False
                if media_paths and media_paths[0].lower().endswith(".mp4"):
                    is_video = True
                    print("   🎬 [Publisher: XHS] 侦测到动态多模态资源，切换至短视频分发专版...")
                    
                    # 切换视频Tab，适配新版Creator UI
                    try:
                        tab_candidates = page.locator('div, span, button, a').filter(has_text="上传视频")
                        if tab_candidates.count() > 0:
                            tab_candidates.last.click(timeout=3000)
                    except Exception:
                        pass
                else:
                    print("   🖼️ [Publisher: XHS] 侦测到静态图文资源，锚定图文分发专版...")
                    try:
                        tab_candidates = page.locator('div, span, button, a').filter(has_text="上传图文")
                        if tab_candidates.count() > 0:
                            tab_candidates.last.click(timeout=3000)
                    except Exception:
                        pass
                        
                time.sleep(2)
                
                # 2. 注入图片/媒体
                if media_paths:
                    file_inputs = page.locator('input[type="file"]')
                    if file_inputs.count() > 0:
                        for i in range(file_inputs.count()):
                            input_el = file_inputs.nth(i)
                            try:
                                # Not catching specific accept type since it ranges wildly, just try the first non-hidden one
                                input_el.set_input_files(media_paths)
                                print(f"   📡 [Publisher: XHS] 数据泵启动，正在抽干并上载全尺寸媒体至小红书云丛集: {media_paths}")
                                break
                            except Exception as e:
                                pass
                    
                    print("   ⏳ [Publisher: XHS] 等待云端极速解码、推流预热 (可能需要5-15秒)，等待表单引擎解锁...")
                    # 新版 XHS 会在此刻才渲染编辑器
                    if is_video:
                        time.sleep(12)
                    else:
                        time.sleep(6)
                    
                # 3. 注入标题
                title_filled = False
                title_sels = [
                    '[contenteditable="true"][placeholder*="标题"]',
                    '[contenteditable="true"][placeholder*="赞"]',
                    'input.c-input_inner',
                    'input[placeholder*="标题"]'
                ]
                for sel in title_sels:
                    el = page.locator(sel)
                    if el.count() > 0:
                        el = el.last
                        el.focus()
                        # 使用 Playwright 键盘事件模拟真实手打
                        page.keyboard.press("Control+a")
                        page.keyboard.press("Backspace")
                        page.keyboard.insert_text(title)
                        title_filled = True
                        break
                        
                if not title_filled:
                    print("   ⚠️ [Publisher: XHS] 未能物理定位到标题输入框，请审查网页结构。")
                
                # 4. 注入正文
                content_filled = False
                content_sels = [
                    '[contenteditable="true"][class*="editor"]',
                    '[contenteditable="true"][class*="content"]',
                    '[contenteditable="true"][placeholder*="描述"]',
                    '[contenteditable="true"][placeholder*="正文"]',
                    '[contenteditable="true"]'
                ]
                
                for sel in content_sels:
                    candidates = page.locator(sel)
                    for i in range(candidates.count()):
                        el = candidates.nth(i)
                        # We don't want to insert content into the title box
                        ph = el.get_attribute("placeholder") or ""
                        if "标题" not in ph and "赞" not in ph:
                            try:
                                el.focus()
                                page.keyboard.press("Control+a")
                                page.keyboard.press("Backspace")
                                page.keyboard.insert_text(content)
                                content_filled = True
                                break
                            except Exception:
                                pass
                    if content_filled:
                        break

                if not content_filled:
                    print("   ⚠️ [Publisher: XHS] 极端错误：所有降级探针均未能锁定富文本磁道，无法写正文！")

                time.sleep(2)
                
                # 5. 存为草稿 (极度重要：禁止硬发布)
                draft_btn = page.locator("button:has-text('存草稿'), button:has-text('保存草稿'), button:has-text('暂存')")
                if draft_btn.count() > 0:
                    draft_btn.first.click()
                    print(f"   ✅ [Publisher: XHS] 指挥枢纽核准，战果已安全静默【存入草稿箱】！请按需审核。")
                else:
                    print("   ⚠️ [Publisher: XHS] 界面未找到草稿暂存按钮，为保护宣发安全，已主动暂停。您可手动存为草稿。")

                time.sleep(3)
                return True
                
            except Exception as e:
                print(f"   ❌ [Publisher: XHS] 底层穿透进程核爆异常: {e}")
                return False
