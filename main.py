import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
from astrbot.core.conversation_mgr import Conversation

DREAM_TEMPLATE_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;700&family=Orbitron:wght@500&display=swap" rel="stylesheet">
    <style>
        {% if theme == 'midnight_gothic' %}
        :root {
            --bg-color: #1a1b26;
            --card-bg: radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%);
            --font-color: #a9b1d6;
            --title-color: #bb9af7;
            --border-color: #3b4261;
            --shadow-color: rgba(187, 154, 247, 0.3);
            --font-main: 'Noto Serif SC', serif;
            --font-title: 'Orbitron', sans-serif;
        }
        {% elif theme == 'starlight_nebula' %}
        :root {
            --bg-color: #000000;
            --card-bg: #0d0d2b;
            --font-color: #e0e0e0;
            --title-color: #7dcfff;
            --border-color: #4a4a70;
            --shadow-color: rgba(125, 207, 255, 0.4);
            --font-main: 'Noto Serif SC', serif;
            --font-title: 'Orbitron', sans-serif;
        }
        {% elif theme == 'ancient_scroll' %}
        :root {
            --bg-color: #f5e8d7;
            --card-bg: #fdf6e3;
            --font-color: #654321;
            --title-color: #8b4513;
            --border-color: #d2b48c;
            --shadow-color: rgba(139, 69, 19, 0.2);
            --font-main: 'Noto Serif SC', serif;
            --font-title: 'Noto Serif SC', serif;
        }
        {% endif %}

        body {
            margin: 0;
            padding: 40px;
            background-color: var(--bg-color);
            font-family: var(--font-main);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            box-sizing: border-box;
        }
        .card {
            background: var(--card-bg);
            color: var(--font-color);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            box-shadow: 0 10px 40px var(--shadow-color);
            padding: 40px 50px;
            width: 800px;
            max-width: 90vw;
            box-sizing: border-box;
        }
        .header {
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 20px;
            margin-bottom: 30px;
            text-align: center;
        }
        .title {
            font-family: var(--font-title);
            font-size: 28px;
            color: var(--title-color);
            margin: 0;
            letter-spacing: 2px;
            text-shadow: 0 0 10px var(--shadow-color);
        }
        .content {
            font-size: 18px;
            line-height: 2;
            white-space: pre-wrap;
            text-align: justify;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            font-size: 14px;
            color: var(--font-color);
            opacity: 0.7;
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <h1 class="title">A Dream From Yesterday</h1>
        </div>
        <div class="content">
            <p>{{ dream_text }}</p>
        </div>
        <div class="footer">
            <span>{{ group_name }}</span>
            <span>{{ dream_date }}</span>
        </div>
    </div>
</body>
</html>
"""

@register("dreamwaver", "LumineStory", "将对话编织成梦境图片", "1.0.0")
class DreamWaver(Star):
    def __init__(self, context: Context, config: AstrBotConfig = None):
        super().__init__(context)
        self.config = config if config else {}
        defaults = {
            "enabled": True,
            "trigger_mode": "command_only",
            "auto_trigger_time": "23:59",
            "dream_style": "一段融合了赛博朋克与古典悲剧元素的意识流独白",
            "dream_theme": "midnight_gothic",
            "min_messages_for_dream": 20,
        }
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
        self.config.save_config()

        self.monitor_task = None
        if "daily_auto" in self.config.get("trigger_mode"):
            self.monitor_task = asyncio.create_task(self._daily_dream_task())

    async def _daily_dream_task(self):
        while True:
            now = datetime.now()
            trigger_time_str = self.config.get("auto_trigger_time", "23:59")
            try:
                hour, minute = map(int, trigger_time_str.split(':'))
            except ValueError:
                logger.error(f"[DreamWaver] Invalid auto_trigger_time format: {trigger_time_str}. Please use HH:MM format.")
                await asyncio.sleep(3600) 
                continue

            next_trigger = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if now >= next_trigger:
                next_trigger += timedelta(days=1)
            
            sleep_seconds = (next_trigger - now).total_seconds()
            logger.info(f"[DreamWaver] Next automatic dream at: {next_trigger}, waiting for {sleep_seconds:.0f} seconds.")
            await asyncio.sleep(sleep_seconds)

            logger.info("[DreamWaver] Daily auto-dream task triggered.")
            # This is a pseudo-code implementation as the documentation does not provide a direct API
            # to get all active sessions. A real implementation would require framework support.
            # for uid in self.context.conversation_manager.get_all_uids():
            #     await self.generate_and_send_dream(uid)
            
    async def _generate_dream(self, event: AstrMessageEvent, time_delta: timedelta) -> Dict:
        try:
            uid = event.unified_msg_origin
            curr_cid = await self.context.conversation_manager.get_curr_conversation_id(uid)
            if not curr_cid:
                return {"error": "无法找到当前会话。"}
            conversation: Conversation = await self.context.conversation_manager.get_conversation(uid, curr_cid)
            if not conversation or not conversation.history:
                return {"error": "这里似乎一片寂静，连梦的碎片也找不到。"}

            history_list = json.loads(conversation.history)
            
            max_messages = self.config.get("max_history_messages", 300)
            min_messages = self.config.get("min_messages_for_dream", 20)
            
            recent_messages_content = []
            for msg in reversed(history_list):
                if len(recent_messages_content) >= max_messages:
                    break
                
                if not isinstance(msg, dict):
                    continue

                if msg.get("role") == "assistant" or not msg.get("content"):
                    continue
                
                recent_messages_content.append(msg.get("content", ""))

            if len(recent_messages_content) < min_messages:
                return {"error": f"梦境的素材太少了，至少需要 {min_messages} 条有效对话才能编织哦。"}
            
            recent_messages_content.reverse()
            formatted_dialogue = "\n".join([f"- {c}" for c in recent_messages_content])

            llm_provider = self.context.get_using_provider()
            if not llm_provider:
                return {"error": "核心分析服务不可用，请联系管理员。"}
            
            dream_style = self.config.get("dream_style", "超现实主义短篇故事")
            dream_prompt = (
                f"你是一位名为“入梦师”的艺术家，擅长将人们的对话转化为充满想象力的艺术作品。\n"
                f"你的任务是阅读以下的对话片段，然后以【{dream_style}】的风格，创作一段文字。作品需要捕捉对话中隐藏的情绪、关键词和内在联系，但不要直接引用或总结对话内容，而是进行艺术化、抽象化的再创作。\n"
                "让作品充满美感、意象，甚至可以有些怪诞，就像一个真实的梦。\n\n"
                "--- 对话素材 ---\n"
                f"{formatted_dialogue}\n"
                "--- 素材结束 ---\n\n"
                "现在，请开始你的创作："
            )
            result = await llm_provider.text_chat(prompt=dream_prompt, session_id=f"dream_{event.get_session_id()}")
            dream_text = result.completion_text.strip()

            group_name = "一个神秘的梦境空间"
            if not event.is_private_chat():
                group = await event.get_group()
                if group and group.name:
                    group_name = group.name

            render_data = {
                "theme": self.config.get("dream_theme", "midnight_gothic"),
                "dream_text": dream_text,
                "group_name": group_name,
                "dream_date": datetime.now().strftime("%Y-%m-%d")
            }
            
            image_url = await self.html_render(DREAM_TEMPLATE_HTML, render_data)
            return {"image_url": image_url}

        except Exception as e:
            logger.error(f"[DreamWaver] Error during dream generation: {e}", exc_info=True)
            return {"error": "梦境在编织的途中消散了，似乎遇到了一些阻碍..."}

    @filter.command("dream", aliases={"入梦", "织梦"})
    async def dream_handler(self, event: AstrMessageEvent):
        if not self.config.get("enabled"):
            return

        yield event.plain_result("嘘...我正在潜入大家的意识深处，寻找梦的素材...")
        
        result_dict = await self._generate_dream(event, timedelta(days=1))
        
        if "image_url" in result_dict:
            yield event.image_result(result_dict["image_url"])
        else:
            yield event.plain_result(f"❌ {result_dict.get('error', '未知错误')}")

    async def terminate(self):
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                logger.info("[DreamWaver] Daily dream monitoring task cancelled.")
        logger.info("DreamWaver plugin terminated.")
