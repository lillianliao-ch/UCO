"""
FFmpeg Video Engine — Local rendering implementation.

This is the first concrete video engine. It uses:
- TTS providers for narration audio
- Pillow for visual card generation (text overlay frames)
- ffmpeg-python for compositing and final MP4 encoding

Design inspired by RedditVideoMakerBot's rendering pipeline, but fully decoupled
from Reddit-specific logic and integrated into the UCO pipeline architecture.
"""

import os
import re
import json
import textwrap
import tempfile
from pathlib import Path
from typing import List

from .base_engine import BaseVideoEngine, VideoRenderRequest, VideoRenderResult, ScriptSegment

try:
    import ffmpeg
except ImportError:
    ffmpeg = None

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = ImageDraw = ImageFont = None


class FFmpegVideoEngine(BaseVideoEngine):
    """
    FFmpeg-based local video renderer.

    Pipeline:
    1. TTS: Generate MP3 per script segment
    2. Visual: Generate PNG card per segment (Pillow)
    3. Composite: Overlay cards on background, sync with audio (FFmpeg)
    4. Output: Final MP4

    Can be replaced by a different engine (Remotion, Revideo, etc.)
    without touching any pipeline or prompt code.
    """

    # Font paths — macOS defaults with fallback chain
    FONT_PATHS = [
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux fallback
    ]

    def __init__(self):
        self.font_path = self._find_font()
        self._tts_providers = {}

    def _find_font(self) -> str:
        for p in self.FONT_PATHS:
            if os.path.exists(p):
                return p
        return ""

    def _get_tts_provider(self, provider_name: str, reference_audio: str = ""):
        """Lazy-load TTS provider by name."""
        if provider_name not in self._tts_providers:
            if provider_name == "edge_tts":
                from .tts_providers.edge_tts_provider import EdgeTTSProvider
                self._tts_providers[provider_name] = EdgeTTSProvider()
            elif provider_name == "gtts":
                from .tts_providers.gtts_provider import GTTSProvider
                self._tts_providers[provider_name] = GTTSProvider()
            elif provider_name == "cosyvoice":
                from .tts_providers.cosyvoice_provider import CosyVoiceTTSProvider
                self._tts_providers[provider_name] = CosyVoiceTTSProvider(
                    reference_audio_path=reference_audio,
                    voice_name="lilian_voice",
                )
            else:
                # Default fallback to edge_tts
                print(f"   ⚠️ Unknown TTS provider '{provider_name}', falling back to edge_tts")
                from .tts_providers.edge_tts_provider import EdgeTTSProvider
                self._tts_providers[provider_name] = EdgeTTSProvider()
        return self._tts_providers[provider_name]

    def get_supported_tts(self) -> List[str]:
        return ["edge_tts", "gtts", "cosyvoice"]

    def get_engine_name(self) -> str:
        return "FFmpeg Local Renderer"

    def render(self, request: VideoRenderRequest) -> VideoRenderResult:
        """
        Full rendering pipeline:
        1. Create temp working directory
        2. Generate TTS audio per segment
        3. Generate visual cards per segment
        4. Generate or prepare background
        5. Composite everything with FFmpeg
        """
        print(f"\n🎬 [{self.get_engine_name()}] 启动视频渲染引擎...")
        print(f"   📐 分辨率: {request.resolution[0]}x{request.resolution[1]}")
        print(f"   🎙️ TTS: {request.tts_provider} / {request.tts_voice}")
        print(f"   📝 脚本段落: {len(request.script_segments)} 段")

        if not ffmpeg:
            return VideoRenderResult(success=False, error_message="ffmpeg-python not installed. Run: pip install ffmpeg-python")
        if not Image:
            return VideoRenderResult(success=False, error_message="Pillow not installed. Run: pip install Pillow")

        # Create working directory
        work_dir = tempfile.mkdtemp(prefix="uco_video_")
        W, H = request.resolution

        try:
            # ── Step 1: TTS Audio Generation ──
            print("\n🔊 [Step 1/4] 生成 TTS 语音...")
            tts = self._get_tts_provider(request.tts_provider, reference_audio=request.reference_audio)
            audio_paths = []
            audio_durations = []

            # Generate a short silence for the title card intro
            TITLE_INTRO_DURATION = 2.5  # seconds of title card before narration starts
            silence_path = os.path.join(work_dir, "silence.mp3")
            self._generate_silence(silence_path, TITLE_INTRO_DURATION)
            audio_paths.append(silence_path)
            audio_durations.append(TITLE_INTRO_DURATION)

            for i, seg in enumerate(request.script_segments):
                # Add a brief inter-segment pause for natural pacing
                if i > 0:
                    pause_path = os.path.join(work_dir, f"pause_{i}.mp3")
                    self._generate_silence(pause_path, 0.8)
                    audio_paths.append(pause_path)
                    audio_durations.append(0.8)

                audio_path = os.path.join(work_dir, f"seg_{i}.mp3")
                try:
                    duration = tts.synthesize(seg.text, audio_path, request.tts_voice)
                except Exception as e:
                    print(f"   ⚠️ TTS 主引擎失败，尝试 gTTS 降级: {e}")
                    fallback = self._get_tts_provider("gtts")
                    duration = fallback.synthesize(seg.text, audio_path, request.tts_voice)

                audio_paths.append(audio_path)
                audio_durations.append(duration)

            total_duration = sum(audio_durations)
            print(f"   ✅ TTS 完成: 总时长 {total_duration:.1f}s (含 {TITLE_INTRO_DURATION}s 标题卡)")

            # ── Step 2: Visual Card Generation ──
            print("\n🎨 [Step 2/4] 生成视觉卡片...")
            # Build card list aligned with audio segments:
            # [title_card, content_card_0, content_card_1, ...]
            # Audio alignment: [silence, seg0_audio, pause, seg1_audio, pause, seg2_audio]
            card_paths = []
            card_durations = []  # Duration each card is shown

            # Title card shown during silence intro
            title_card_path = os.path.join(work_dir, "card_title.png")
            self._generate_title_card(
                title=request.title,
                badge=request.badge_text,
                subtitle=request.subtitle_text,
                output_path=title_card_path,
                size=(W, H),
                bg_color=request.background_color,
            )
            card_paths.append(title_card_path)
            card_durations.append(TITLE_INTRO_DURATION)

            # Content cards — each shown for its TTS duration + any preceding pause
            seg_audio_idx = 1  # skip silence
            for i, seg in enumerate(request.script_segments):
                card_path = os.path.join(work_dir, f"card_{i}.png")

                # Calculate this card's display duration
                card_dur = 0.0
                if i > 0:
                    card_dur += 0.8  # the pause before this segment
                    seg_audio_idx += 1  # skip the pause audio entry
                card_dur += audio_durations[seg_audio_idx]  # the actual TTS duration
                seg_audio_idx += 1

                self._generate_content_card(
                    headline=seg.visual_text or "",
                    full_text=seg.text,
                    segment_index=i,
                    total_segments=len(request.script_segments),
                    output_path=card_path,
                    size=(W, H),
                    bg_color=request.background_color,
                )
                card_paths.append(card_path)
                card_durations.append(card_dur)

            print(f"   ✅ 卡片完成: {len(card_paths)} 张")

            # ── Step 3: Concatenate Audio ──
            print("\n🔗 [Step 3/4] 拼接音频轨道...")
            final_audio_path = os.path.join(work_dir, "final_audio.mp3")
            self._concat_audio(audio_paths, final_audio_path)

            # ── Step 4: FFmpeg Composite ──
            print("\n🎞️ [Step 4/4] FFmpeg 视频合成...")
            os.makedirs(os.path.dirname(os.path.abspath(request.output_path)), exist_ok=True)

            self._composite_video_v2(
                card_paths=card_paths,
                card_durations=card_durations,
                final_audio_path=final_audio_path,
                output_path=request.output_path,
                resolution=(W, H),
                total_duration=total_duration,
            )

            # Generate thumbnail from title card
            thumbnail_path = request.output_path.replace(".mp4", "_thumb.png")
            if os.path.exists(title_card_path):
                img = Image.open(title_card_path)
                img.thumbnail((540, 960))
                img.save(thumbnail_path)

            print(f"\n✅ [{self.get_engine_name()}] 视频渲染完成!")
            print(f"   📄 输出: {request.output_path}")
            print(f"   ⏱️ 时长: {total_duration:.1f}s")

            return VideoRenderResult(
                success=True,
                video_path=request.output_path,
                duration_seconds=total_duration,
                thumbnail_path=thumbnail_path,
                segments_rendered=len(request.script_segments),
            )

        except Exception as e:
            print(f"\n❌ [{self.get_engine_name()}] 渲染管线严重故障: {e}")
            import traceback
            traceback.print_exc()
            return VideoRenderResult(success=False, error_message=str(e))

        finally:
            # Clean up temp files (keep output)
            self._cleanup_temp(work_dir)

    # ── Visual Card Generators (Premium Design) ──

    # Color palette — dark tech/premium aesthetic
    PALETTE = {
        "bg_dark":      (12, 12, 20),
        "bg_mid":       (22, 22, 38),
        "accent_red":   (227, 55, 55),
        "accent_blue":  (60, 120, 255),
        "accent_purple":(140, 80, 220),
        "accent_cyan":  (40, 200, 220),
        "text_bright":  (245, 245, 250),
        "text_mid":     (180, 180, 195),
        "text_dim":     (100, 100, 120),
        "glass_fill":   (30, 30, 50),
        "glass_border": (60, 60, 90),
    }

    def _draw_gradient_bg(self, draw, W, H, color_top=(12, 12, 25), color_bot=(25, 15, 40)):
        """Draw a vertical gradient background for premium depth."""
        for y in range(H):
            ratio = y / H
            r = int(color_top[0] + (color_bot[0] - color_top[0]) * ratio)
            g = int(color_top[1] + (color_bot[1] - color_top[1]) * ratio)
            b = int(color_top[2] + (color_bot[2] - color_top[2]) * ratio)
            draw.line([(0, y), (W, y)], fill=(r, g, b))

    def _draw_decorative_elements(self, draw, W, H):
        """Add subtle geometric decorations for visual richness."""
        P = self.PALETTE
        # Top-right accent orb (blurred circle effect)
        for r in range(120, 0, -2):
            alpha_ratio = r / 120
            c = (
                int(P["accent_blue"][0] * (1 - alpha_ratio) * 0.15),
                int(P["accent_blue"][1] * (1 - alpha_ratio) * 0.15),
                int(P["accent_blue"][2] * (1 - alpha_ratio) * 0.15 + P["bg_dark"][2]),
            )
            c = tuple(min(255, max(0, v)) for v in c)
            draw.ellipse([W - 200 - r, 80 - r, W - 200 + r, 80 + r], fill=c)

        # Bottom-left accent orb
        for r in range(100, 0, -2):
            alpha_ratio = r / 100
            c = (
                int(P["accent_purple"][0] * (1 - alpha_ratio) * 0.12 + P["bg_dark"][0]),
                int(P["accent_purple"][1] * (1 - alpha_ratio) * 0.12 + P["bg_dark"][1]),
                int(P["accent_purple"][2] * (1 - alpha_ratio) * 0.12 + P["bg_dark"][2]),
            )
            c = tuple(min(255, max(0, v)) for v in c)
            draw.ellipse([100 - r, H - 300 - r, 100 + r, H - 300 + r], fill=c)

        # Thin horizontal line decoration
        draw.line([(60, int(H * 0.05)), (W - 60, int(H * 0.05))], fill=(40, 40, 60), width=1)
        draw.line([(60, H - 60), (W - 60, H - 60)], fill=(40, 40, 60), width=1)

        # Corner brackets (top-left, bottom-right)
        bracket_len = 40
        bc = (50, 50, 80)
        # Top-left
        draw.line([(50, 50), (50 + bracket_len, 50)], fill=bc, width=2)
        draw.line([(50, 50), (50, 50 + bracket_len)], fill=bc, width=2)
        # Bottom-right
        draw.line([(W - 50, H - 50), (W - 50 - bracket_len, H - 50)], fill=bc, width=2)
        draw.line([(W - 50, H - 50), (W - 50, H - 50 - bracket_len)], fill=bc, width=2)

    def _draw_glass_panel(self, draw, x1, y1, x2, y2, radius=20):
        """Draw a frosted glass-like panel."""
        P = self.PALETTE
        draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=P["glass_fill"])
        draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, outline=P["glass_border"], width=1)

    def _generate_title_card(self, title: str, badge: str, subtitle: str,
                             output_path: str, size: tuple, bg_color: tuple):
        """Generate premium title card with gradient, glass panels, and decorations."""
        W, H = size
        P = self.PALETTE
        img = Image.new("RGB", (W, H), color=P["bg_dark"])
        draw = ImageDraw.Draw(img)

        # Gradient background
        self._draw_gradient_bg(draw, W, H, (10, 10, 22), (28, 15, 42))
        # Decorative elements
        self._draw_decorative_elements(draw, W, H)

        PAD_X = 80
        MAX_W = W - PAD_X * 2

        # ── Top status bar ──
        status_font = self._get_font(26)
        draw.text((PAD_X, int(H * 0.07)), "LIVE · AI INTELLIGENCE REPORT",
                  fill=P["accent_cyan"], font=status_font)
        # Blinking dot simulation
        draw.ellipse([PAD_X - 25, int(H * 0.073), PAD_X - 12, int(H * 0.073) + 13],
                     fill=P["accent_red"])

        # ── Badge ──
        if badge:
            badge_font = self._get_font(34)
            badge_text = badge.replace("🎬 ", "").strip()
            box_w = int(badge_font.getlength(badge_text)) + 50
            badge_y = int(H * 0.15)
            # Gradient-effect badge
            draw.rounded_rectangle(
                [PAD_X, badge_y, PAD_X + box_w, badge_y + 55],
                radius=8, fill=P["accent_red"]
            )
            draw.text((PAD_X + 25, badge_y + 10), badge_text,
                      fill=(255, 255, 255), font=badge_font)

        # ── Main Glass Panel ──
        panel_top = int(H * 0.24)
        panel_bottom = int(H * 0.72)
        self._draw_glass_panel(draw, PAD_X - 20, panel_top, W - PAD_X + 20, panel_bottom)

        # ── Title (inside panel) ──
        title_y = panel_top + 50
        title_font_size = 82
        while title_font_size > 40:
            title_font = self._get_font(title_font_size)
            lines = self._wrap_text(title, title_font, MAX_W - 30)
            total_h = len(lines) * (title_font_size + 25)
            if total_h < (panel_bottom - panel_top) * 0.7:
                break
            title_font_size -= 5

        # Accent bar above title
        draw.rectangle([PAD_X + 10, title_y - 15, PAD_X + 80, title_y - 11],
                       fill=P["accent_blue"])

        y = title_y
        for line in lines:
            draw.text((PAD_X + 10, y), line, fill=P["text_bright"], font=title_font,
                       stroke_width=1, stroke_fill=(180, 180, 200))
            y += title_font_size + 25

        # ── Subtitle ──
        if subtitle:
            sub_font = self._get_font(32)
            sub_y = y + 30
            draw.text((PAD_X + 10, sub_y), subtitle,
                      fill=P["text_mid"], font=sub_font)

        # ── Bottom branding bar ──
        bar_y = H - 130
        draw.rectangle([0, bar_y, W, bar_y + 2], fill=P["glass_border"])
        brand_font = self._get_font(28)
        draw.text((PAD_X, bar_y + 20), "Lilian聊AI",
                  fill=P["accent_cyan"], font=brand_font)
        draw.text((PAD_X, bar_y + 55), "AI 行业深度观察 · 每日情报速递",
                  fill=P["text_dim"], font=self._get_font(24))

        img.save(output_path, quality=95)

    def _generate_content_card(self, headline: str, full_text: str,
                               segment_index: int, total_segments: int,
                               output_path: str, size: tuple, bg_color: tuple):
        """Generate rich content card with headline, full narration text, and progress."""
        W, H = size
        P = self.PALETTE
        img = Image.new("RGB", (W, H), color=P["bg_dark"])
        draw = ImageDraw.Draw(img)

        # Gradient background (shifted per segment for visual variety)
        hue_shift = segment_index * 5
        self._draw_gradient_bg(draw, W, H,
                               (10, 10 + hue_shift, 22),
                               (25 + hue_shift, 15, 40))
        self._draw_decorative_elements(draw, W, H)

        PAD_X = 80
        MAX_W = W - PAD_X * 2

        # ── Top: Segment progress bar ──
        progress_y = int(H * 0.06)
        bar_w = W - PAD_X * 2
        draw.rounded_rectangle([PAD_X, progress_y, PAD_X + bar_w, progress_y + 6],
                               radius=3, fill=(40, 40, 60))
        fill_w = int(bar_w * (segment_index + 1) / total_segments)
        draw.rounded_rectangle([PAD_X, progress_y, PAD_X + fill_w, progress_y + 6],
                               radius=3, fill=P["accent_cyan"])
        draw.ellipse([PAD_X + fill_w - 5, progress_y - 4, PAD_X + fill_w + 5, progress_y + 10],
                     fill=P["accent_cyan"])

        seg_font = self._get_font(24)
        seg_label = f"PART {segment_index + 1}/{total_segments}"
        draw.text((PAD_X, progress_y + 18), seg_label, fill=P["text_dim"], font=seg_font)

        # ── Headline glass panel (top section) ──
        if headline:
            hl_panel_top = int(H * 0.14)
            hl_panel_bottom = int(H * 0.32)
            self._draw_glass_panel(draw, PAD_X - 20, hl_panel_top, W - PAD_X + 20, hl_panel_bottom)

            # Headline icon
            icon_font = self._get_font(36)
            icons = ["💡", "🔍", "⚡"]
            icon = icons[segment_index % len(icons)]
            draw.text((PAD_X + 10, hl_panel_top + 18), icon, font=icon_font)

            # Headline text — multi-line supported
            hl_font_size = 44
            hl_font = self._get_font(hl_font_size)
            hl_lines = []
            for raw_line in headline.split('\n'):
                raw_line = raw_line.strip()
                if raw_line:
                    hl_lines.extend(self._wrap_text(raw_line, hl_font, MAX_W - 80))

            # Auto-shrink if too many lines
            while len(hl_lines) > 4 and hl_font_size > 28:
                hl_font_size -= 4
                hl_font = self._get_font(hl_font_size)
                hl_lines = []
                for raw_line in headline.split('\n'):
                    raw_line = raw_line.strip()
                    if raw_line:
                        hl_lines.extend(self._wrap_text(raw_line, hl_font, MAX_W - 80))

            hl_y = hl_panel_top + 25
            for line in hl_lines:
                draw.text((PAD_X + 55, hl_y), line,
                          fill=P["accent_cyan"], font=hl_font)
                hl_y += hl_font_size + 12

        # ── Full narration text panel (main body) ──
        body_panel_top = int(H * 0.35) if headline else int(H * 0.14)
        body_panel_bottom = int(H * 0.82)
        self._draw_glass_panel(draw, PAD_X - 20, body_panel_top, W - PAD_X + 20, body_panel_bottom)

        # Large quote mark
        quote_font = self._get_font(100)
        draw.text((PAD_X + 5, body_panel_top + 5), "\u201c", fill=(50, 50, 80), font=quote_font)

        # Full narration text — auto-scale to fit
        body_y_start = body_panel_top + 60
        available_h = body_panel_bottom - body_y_start - 30
        font_size = 44
        while font_size > 24:
            font = self._get_font(font_size)
            lines = self._wrap_text(full_text, font, MAX_W - 60)
            total_h = len(lines) * (font_size + 18)
            if total_h < available_h:
                break
            font_size -= 2

        # Vertical accent bar
        draw.rectangle([PAD_X + 5, body_y_start, PAD_X + 9, body_y_start + len(lines) * (font_size + 18)],
                       fill=P["accent_blue"])

        y = body_y_start
        for line in lines:
            draw.text((PAD_X + 25, y), line, fill=P["text_bright"], font=font)
            y += font_size + 18

        # ── Bottom branding ──
        bar_y = H - 130
        draw.rectangle([0, bar_y, W, bar_y + 2], fill=P["glass_border"])
        brand_font = self._get_font(28)
        draw.text((PAD_X, bar_y + 20), "Lilian聊AI",
                  fill=P["accent_cyan"], font=brand_font)
        draw.text((PAD_X, bar_y + 55), "AI 行业深度观察 · 每日情报速递",
                  fill=P["text_dim"], font=self._get_font(24))

        img.save(output_path, quality=95)

    # ── Audio Utilities ──

    def _concat_audio(self, audio_paths: list, output_path: str):
        """Concatenate multiple MP3 files into a single audio track."""
        if len(audio_paths) == 1:
            import shutil
            shutil.copy2(audio_paths[0], output_path)
            return

        # Create concat list file for ffmpeg
        list_path = output_path + ".list.txt"
        with open(list_path, "w") as f:
            for p in audio_paths:
                f.write(f"file '{p}'\n")

        try:
            (
                ffmpeg
                .input(list_path, format='concat', safe=0)
                .output(output_path, acodec='libmp3lame', ab='192k')
                .overwrite_output()
                .run(quiet=True)
            )
        finally:
            if os.path.exists(list_path):
                os.remove(list_path)

    # ── Audio Helpers ──

    def _generate_silence(self, output_path: str, duration: float):
        """Generate a silent MP3 file of given duration."""
        try:
            (
                ffmpeg
                .input(f"anullsrc=r=44100:cl=mono", f="lavfi", t=duration)
                .output(output_path, acodec='libmp3lame', ab='128k')
                .overwrite_output()
                .run(quiet=True)
            )
        except Exception:
            # Fallback: create a tiny silent file
            import struct, wave
            with wave.open(output_path.replace('.mp3', '.wav'), 'w') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(44100)
                wf.writeframes(struct.pack('<' + 'h' * int(44100 * duration), *([0] * int(44100 * duration))))

    # ── FFmpeg Composite V2 (with transitions) ──

    def _composite_video_v2(self, card_paths: list, card_durations: list,
                            final_audio_path: str, output_path: str,
                            resolution: tuple, total_duration: float):
        """
        Composite visual cards into a video using concat demuxer.

        Each card becomes a video segment of the specified duration.
        Uses concat for reliable timing instead of complex overlay filters.
        """
        W, H = resolution
        segment_videos = []

        # Convert each card + duration into a short video clip
        for i, (card_path, dur) in enumerate(zip(card_paths, card_durations)):
            seg_video = card_path.replace('.png', '.mp4')
            try:
                (
                    ffmpeg
                    .input(card_path, loop=1, t=dur, framerate=24)
                    .filter('scale', W, H)
                    .output(seg_video,
                            vcodec='libx264',
                            pix_fmt='yuv420p',
                            **{'b:v': '5M', 'r': 24})
                    .overwrite_output()
                    .run(quiet=True)
                )
                segment_videos.append(seg_video)
            except ffmpeg.Error as e:
                stderr = e.stderr.decode('utf8') if e.stderr else str(e)
                raise RuntimeError(f"Segment {i} encode failed: {stderr}")

        # Now concatenate all segment videos + add crossfade transitions
        # Use concat filter for smooth joining
        concat_list = os.path.join(os.path.dirname(card_paths[0]), 'concat_list.txt')
        with open(concat_list, 'w') as f:
            for sv in segment_videos:
                f.write(f"file '{sv}'\n")

        # Concat video segments, then mux with the full audio
        concat_video = os.path.join(os.path.dirname(card_paths[0]), 'concat_video.mp4')
        try:
            (
                ffmpeg
                .input(concat_list, format='concat', safe=0)
                .output(concat_video, vcodec='libx264', pix_fmt='yuv420p',
                        **{'b:v': '5M', 'r': 24})
                .overwrite_output()
                .run(quiet=True)
            )
        except ffmpeg.Error as e:
            stderr = e.stderr.decode('utf8') if e.stderr else str(e)
            raise RuntimeError(f"Video concat failed: {stderr}")

        # Final mux: concat_video + full audio
        video_in = ffmpeg.input(concat_video)
        audio_in = ffmpeg.input(final_audio_path)

        try:
            (
                ffmpeg
                .output(video_in, audio_in, output_path,
                        vcodec='copy',
                        acodec='aac',
                        movflags='+faststart',
                        shortest=None,
                        **{'b:a': '192k'})
                .overwrite_output()
                .run(quiet=True)
            )
        except ffmpeg.Error as e:
            stderr = e.stderr.decode('utf8') if e.stderr else str(e)
            raise RuntimeError(f"Final mux failed: {stderr}")

    # ── Helpers ──

    def _get_font(self, size: int):
        """Load a font at the given size, with fallback to default."""
        if self.font_path:
            try:
                return ImageFont.truetype(self.font_path, size, index=0)
            except Exception:
                pass
        return ImageFont.load_default()

    def _wrap_text(self, text: str, font, max_width: int) -> list:
        """
        Word-wrap text to fit within max_width pixels.
        Handles mixed Chinese/English text correctly.
        """
        lines = []
        current_line = ""
        # Split into tokens: English words as units, Chinese chars individually
        tokens = re.findall(r'[a-zA-Z0-9.,!?/\'\"-]+|.', text)

        for token in tokens:
            test_line = current_line + token
            if font.getlength(test_line) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = token
        if current_line:
            lines.append(current_line)
        return lines

    def _cleanup_temp(self, work_dir: str):
        """Remove temporary working directory."""
        try:
            import shutil
            shutil.rmtree(work_dir, ignore_errors=True)
        except Exception:
            pass
