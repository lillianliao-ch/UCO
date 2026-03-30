import os
import re
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    pass

class PillowVisualEngine:
    """
    100% 纯 Python 画布渲染中枢 (Deterministic Graphic Visualizer).
    Creates standardized, highly aesthetic visual content dynamically without LLM hallucination risks.
    """
    
    def __init__(self, font_path: str = "/System/Library/Fonts/Hiragino Sans GB.ttc"):
        # 兼容 Mac 的主流黑体，Hiragino 拥有极佳的字重感
        if not os.path.exists(font_path):
            self.font_path = "/System/Library/Fonts/STHeiti Medium.ttc"
        else:
            self.font_path = font_path

    def _measure_wrap(self, text, font, max_width):
        """
        完美支持中英文混排的自动换行算法
        利用正则将英文单词打包为一个整体Token，将中文字符打散为单字符Token
        """
        lines = []
        current_line = ''
        # 这个正则表达式能完美包裹英文单词组合，而把汉字逐一劈开，实现完美的中西方混排截断
        tokens = re.findall(r'[a-zA-Z0-9.,!?/\'\"-]+|.', text)
        
        for token in tokens:
            test_line = current_line + token
            # 如果当前行加上新Token还没撑爆画布宽度，就在当前行继续堆叠
            if font.getlength(test_line) <= max_width:
                current_line = test_line
            else:
                # 撑爆了，就把当前行推入数组，新行以新Token开始
                if current_line: 
                    lines.append(current_line)
                current_line = token
                
                # 如果单个Token（例如超长网址）居然比一整行还长，就强制截断
                while font.getlength(current_line) > max_width:
                    if max_width < 10: break 
                    for i in range(1, len(current_line)):
                        if font.getlength(current_line[:i]) > max_width:
                            lines.append(current_line[:i-1])
                            current_line = current_line[i-1:]
                            break
                    else: break
        if current_line: 
            lines.append(current_line)
        return lines

    def generate_poster(self, title: str, subtitle: str, badge: str, output_path: str, mode: str = "xhs") -> str:
        print(f"🎨 [Brain: Visualizer] 发动画布引擎渲染极简海报 ({mode}模式): {title[:10]}...")
        
        if mode == "wechat":
            W, H = 1175, 500  # 2.35:1 aspect ratio
            PAD_X = 60
            MAX_W = W - PAD_X * 2
            badge_y, badge_font_size = 40, 35
            title_start_y = 120
            title_font_size = 85
            sub_font_size = 40
            min_title_font, min_sub_font = 35, 20
        else:
            W, H = 1080, 1440  # 3:4 aspect ratio
            PAD_X = 80
            MAX_W = W - PAD_X * 2
            badge_y, badge_font_size = 150, 50
            title_start_y = 300
            title_font_size = 180
            sub_font_size = 75
            min_title_font, min_sub_font = 60, 30

        img = Image.new('RGB', (W, H), color=(250, 250, 250))
        draw = ImageDraw.Draw(img)

        try: badge_font = ImageFont.truetype(self.font_path, badge_font_size, index=0)
        except: badge_font = ImageFont.load_default()
        
        # 画红底徽章
        box_w = len(badge) * badge_font_size + (20 if mode=="wechat" else 60)
        draw.rounded_rectangle([PAD_X, badge_y, PAD_X+box_w, badge_y + badge_font_size * 1.6], radius=15 if mode=="xhs" else 8, fill=(227, 35, 34))
        draw.text((PAD_X + (10 if mode=="wechat" else 30), badge_y + (5 if mode=="wechat" else 15)), badge, fill=(255, 255, 255), font=badge_font)

        # 动态自适应字号
        while title_font_size > min_title_font:
            try: title_font = ImageFont.truetype(self.font_path, title_font_size, index=0)
            except: title_font = ImageFont.load_default()
            
            lines = self._measure_wrap(title, title_font, MAX_W)
            
            # 为副标题留下足够防线
            allowed_max_h = H - 150 if mode=="wechat" else 1100
            if len(lines) * (title_font_size + (15 if mode=="wechat" else 40)) + title_start_y < allowed_max_h: 
                break
            title_font_size -= 5

        wrapped_title = "\n".join(lines)
        draw.multiline_text((PAD_X, title_start_y), wrapped_title, fill=(22, 22, 22), font=title_font, spacing=15 if mode=="wechat" else 40, stroke_width=1 if mode=="wechat" else 2, stroke_fill=(22, 22, 22))

        while sub_font_size > min_sub_font:
            try: sub_font = ImageFont.truetype(self.font_path, sub_font_size, index=0)
            except: sub_font = ImageFont.load_default()
            sub_lines = self._measure_wrap(subtitle, sub_font, MAX_W)
            if len(sub_lines) <= (2 if mode=="wechat" else 4): break
            sub_font_size -= 5
            
        sub_start_y = title_start_y + len(lines) * (title_font_size + (15 if mode=="wechat" else 40)) + (30 if mode=="wechat" else 70)
        wrapped_sub = "\n".join(sub_lines)
        draw.multiline_text((PAD_X, sub_start_y), wrapped_sub, fill=(90, 90, 90), font=sub_font, spacing=10 if mode=="wechat" else 30, stroke_width=0)
        
        img.save(output_path)
        print(f"   ✓ 海报产出完毕留存至 {output_path}")
        return output_path
