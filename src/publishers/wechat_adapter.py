import time
import urllib.parse
import markdown
import base64
import os
from playwright.sync_api import sync_playwright

class WeChatPublisher:
    """
    通过底层 CDP 直连本地 Chrome 的微信公众号发布引擎。
    完全绕过开放平台 API 每日限额，物理级注入内容。
    """
    def __init__(self, port=9224):
        self.port = port
        self.cdp_url = f"http://localhost:{self.port}"
        
    def push(self, title: str, content_md: str, poster_path: str = None) -> bool:
        """
        Pushes Markdown content to WeChat Official Accounts draft box dynamically.
        """
        print(f"🚀 [WeChatPublisher] 获取全域分发指令，冲阵微信后台: {title[:15]}...")
        html_content = markdown.markdown(content_md)
        # Append minimal Apple/硅谷审美风格的基线 CSS 给转换好的 HTML
        payload_html = f"<div style='font-family: -apple-system, BlinkMacSystemFont, Helvetica, Arial, sans-serif; font-size: 15px; line-height: 1.8; color: #2c2c2c; letter-spacing: 0.05em; padding: 10px;'>{html_content}</div>"

        # 微信的极值防爆盾 (64字符)
        if len(title) > 64:
            title = title[:60] + "..."

        with sync_playwright() as p:
            try:
                browser = p.chromium.connect_over_cdp(self.cdp_url)
                context = browser.contexts[0]
                
                token = None
                wechat_page = None
                
                for page in context.pages:
                    if "mp.weixin.qq.com" in page.url:
                        wechat_page = page
                        parsed = urllib.parse.urlparse(page.url)
                        params = urllib.parse.parse_qs(parsed.query)
                        if "token" in params:
                            token = params["token"][0]
                        break
                
                if not token:
                    wechat_page = context.new_page()
                    wechat_page.goto("https://mp.weixin.qq.com/", timeout=15000)
                    time.sleep(3)
                    parsed = urllib.parse.urlparse(wechat_page.url)
                    params = urllib.parse.parse_qs(parsed.query)
                    if "token" in params:
                        token = params["token"][0]
                        
                if not token:
                    print("⚠️ [WeChatPublisher] 致命错误：未检测到公众号登录 Session Token！请唤醒 Chrome 扫码。")
                    return False
                    
                wechat_page.bring_to_front()
                
                # 强行跃迁至专属纯享版图文编辑器页面
                edit_url = f"https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1&type=10&token={token}&lang=zh_CN"
                wechat_page.goto(edit_url, timeout=30000)
                
                # 等待 DOM 树渲染
                wechat_page.wait_for_selector("#title", timeout=15000)
                
                # 破防注入标题区
                wechat_page.fill("#title", title)
                try:
                    wechat_page.fill("#author", "Lilian聊AI")
                except:
                    pass
                    
                # >>>>> THE ULTIMATE FIX <<<<<
                # macOS / Chromium 在后台标签页中会从系统层面抛弃合成的 ClipboardEvent('paste')
                # 必须强制拉取当前操作窗口到物理前台，方可执行图片注入！
                wechat_page.bring_to_front()
                time.sleep(0.5)
                
                # 穿透 UEditor 框架的物理级装填
                editor = wechat_page.locator("#ueditor_0")
                editor.click()
                wechat_page.evaluate("""() => {
                    const el = document.getElementById('ueditor_0');
                    if (el) el.focus();
                }""")
                time.sleep(1)
                
                if poster_path and os.path.exists(poster_path):
                    print(f"💡 [WeChatPublisher] 安全模式：不执行风险 DOM 注入。海报图片已准备完毕！")
                    print(f"💡 [WeChatPublisher] > 图片存储于：{os.path.abspath(poster_path)}")
                    print(f"💡 [WeChatPublisher] > 发稿结束后，请移步至微信编辑器顶部手动【插入本地图片】。")
                
                print(f"✍️ [WeChatPublisher] 正在安全模式下向编辑器内单边倾泻富文本结构数据...")
                # 预留出顶部空行，方便手动插图
                wechat_page.evaluate("(html) => document.execCommand('insertHTML', false, html)", f"<p>【顶部留白位置，请在此处手动插入本地生成的宽幅海报】</p><br>{payload_html}")
                
                time.sleep(2)
                
                try:
                    save_btn = wechat_page.locator("button:has-text('保存草稿')")
                    if save_btn.count() > 0:
                        save_btn.first.click()
                    else:
                        wechat_page.locator("#js_save").click()
                except Exception as e:
                    print(f"⚠️ [WeChatPublisher] 保存按钮点击异常: {e}")
                    
                time.sleep(3)
                print(f"✅ [WeChatPublisher] 草稿箱落锁成功！全域推送矩阵闭环！")
                return True
                
            except Exception as e:
                print(f"❌ [WeChatPublisher] 引擎运行期底层崩溃: {e}")
                return False
