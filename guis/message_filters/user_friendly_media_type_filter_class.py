'''
Docstring for guis.message_filters.user_friendly_filter_interface

这里面是用户对媒体类型的筛选的交互相关的代码

分类关键词,匹配内容说明,包含的常见格式
图片 / photo,所有的照片、以文件形式发送的图片、图集。,"jpg, png, webp, gif"
视频 / video,所有的视频文件、视频消息（圆形视频）。,"mp4, mkv, mov, avi, webm"
音乐 / music,带有歌手、歌名信息的音频文件。,"mp3, flac, wav, m4a"
音频 / voice,语音消息、录音。,"ogg, opus"
文件 / file,除去音视频外的所有办公文档、压缩包、安装包。,"pdf, zip, exe, docx, txt"
动图 / gif,专门的 GIF 动画。,gif
贴纸 / sticker,Telegram 贴纸（静态或动态）。,"tgs, webm, webp"
'''
from telethon.tl.types import (
    MessageMediaPhoto, MessageMediaDocument, DocumentAttributeVideo,
    DocumentAttributeAudio, MessageMediaWebPage
)
import os


import re
from telethon.tl.types import (
    MessageMediaPhoto, MessageMediaDocument, DocumentAttributeVideo,
    DocumentAttributeAudio
)


class SmartMediaFilter:
    # 预定义的映射表
    TYPE_ALIASES = {
        '图片': 'photo', 'photo': 'photo', '照片': 'photo',
        '视频': 'video', 'video': 'video',
        '音频': 'voice', 'voice': 'voice', '语音': 'voice',
        '音乐': 'music', 'music': 'music',
        '文件': 'document', 'file': 'document', '文档': 'document',
        '动图': 'gif', 'gif': 'gif'
    }

    def __init__(self, user_input: str):
        """
        初始化时自动解析用户输入的混合字符串
        支持分隔符：中英文逗号、分号、空格、顿号、反斜杠、下划线
        """
        if not user_input:
            self.target_types, self.target_exts, self.unrecognized = set(), set(), set()
            return

        # 使用正则匹配所有要求的分隔符：
        # ,， (逗号) | ;； (分号) | \s (空格/换行) | 、 (顿号) | \\ (反斜杠) | _ (下划线)
        # [+] 表示匹配一个或陆续多个分隔符
        split_pattern = r'[,，;；\s\n、\\_]+'

        # 1. 预处理用户输入：将中英文逗号、空格统一，并转为列表
        words = re.split(split_pattern, user_input.strip().lower())

        # 2. 分类：哪些是大类，哪些是后缀
        self.target_types = set()
        self.target_exts = set()
        self.unrecognized = set()

        for word in words:
            if not word:
                continue
            if word in self.TYPE_ALIASES:
                self.target_types.add(self.TYPE_ALIASES[word])
            elif len(word) <= 6 or "." in word:
                # 认为是后缀，如 pdf, docx
                self.target_exts.add(word.lstrip('.'))
            else:
                self.unrecognized.add(word)

    def get_status_msg(self):
        """生成一段话告诉用户识别结果"""
        msg = "🔍 正在为您筛选: "
        parts = list(self.target_types) + [f".{e}" for e in self.target_exts]
        msg += "、".join(parts)

        if self.ignored_words:
            msg += f"\n⚠️ 无法识别以下词汇: {', '.join(self.ignored_words)} (已忽略)"
        return msg

    def is_match(self, message):
        if not message or not message.media:
            return False

        # --- A. 先检查后缀匹配 (用户输入了 jpg, pdf 等) ---
        if self.target_exts:
            file_ext = (message.file.ext or '').lower().lstrip(
                '.') if message.file else ''
            if file_ext in self.target_exts:
                return True

        # --- B. 再检查大类匹配 (用户输入了 图片, 视频 等) ---
        if not self.target_types:
            return False

        # 1. 图片类判断
        if 'photo' in self.target_types:
            if isinstance(message.media, MessageMediaPhoto):
                return True
            # 处理以文件形式发送的图片
            if message.file and message.file.mime_type.startswith('image/'):
                return True

        # 2. 视频类判断
        if 'video' in self.target_types:
            if message.file and (message.file.mime_type.startswith('video/') or
               any(isinstance(x, DocumentAttributeVideo) for x in getattr(message.media, 'document', {}).get('attributes', []))):
                return True

        # 3. 音频/音乐判断
        if isinstance(message.media, MessageMediaDocument):
            attrs = message.media.document.attributes
            is_audio = any(isinstance(x, DocumentAttributeAudio)
                           for x in attrs)
            if is_audio:
                is_voice = any(getattr(x, 'voice', False) for x in attrs)
                if 'voice' in self.target_types and is_voice:
                    return True
                if 'music' in self.target_types and not is_voice:
                    return True

        # 4. GIF判断
        if 'gif' in self.target_types:
            if message.file and message.file.mime_type == 'image/gif':
                return True

        # 5. 普通文件判断 (Document 且不是音视频)
        if 'document' in self.target_types:
            if isinstance(message.media, MessageMediaDocument):
                # 如果不是音视频，就归类为普通文件
                is_vid_aud = any(isinstance(x, (DocumentAttributeVideo, DocumentAttributeAudio))
                                 for x in message.media.document.attributes)
                if not is_vid_aud:
                    return True

        return False


async def get_filtered_messages(client, entity, user_input_types, user_input_exts=None, limit=100):
    """
    业务调用示例：遍历并筛选
    """
    async for message in client.iter_messages(entity, limit=limit):
        if MediaFilter.is_match(message, user_input_types, user_input_exts):
            yield message


class TelethonMediaSearcher:
    # 预定义的合法大类映射
    TYPE_ALIASES = {
        '图片': 'photo', 'photo': 'photo', '照片': 'photo',
        '视频': 'video', 'video': 'video',
        '音频': 'voice', 'voice': 'voice', '语音': 'voice',
        '音乐': 'music', 'music': 'music',
        '文件': 'document', 'file': 'document', '文档': 'document',
        '动图': 'gif', 'gif': 'gif',
        '文本': 'text', 'text': 'text', '文字': 'text',  # 新增文本支持
    }

    def __init__(self, user_input: str):
        """
        初始化时自动解析用户输入的混合字符串
        支持分隔符：中英文逗号、分号、空格、顿号、反斜杠、下划线
        """
        if not user_input:
            self.target_types, self.target_exts, self.unrecognized = set(), set(), set()
            return

        # 使用正则匹配所有要求的分隔符：
        # ,， (逗号) | ;； (分号) | \s (空格/换行) | 、 (顿号) | \\ (反斜杠) | _ (下划线)
        # [+] 表示匹配一个或陆续多个分隔符
        split_pattern = r'[,，;；\s\n、\\_]+'
        # 1. 规范化输入：处理中英文逗号、空格、换行
        words = re.split(split_pattern, user_input.strip().lower())

        self.target_types = set()
        self.target_exts = set()
        self.unrecognized = set()

        # 2. 关键词自动分拣
        for word in words:
            if not word:
                continue

            if word in self.TYPE_ALIASES:
                self.target_types.add(self.TYPE_ALIASES[word])
            # 简单的后缀识别逻辑：如果包含点，或者是3-5位字母数字组合
            # elif len(word) <= 6 or "." in word:
            # 重新定义了逻辑，现在只要不能识别的就是不行
            elif "." in word:
                # 认为是后缀，如 pdf, docx
                self.target_exts.add(word.lstrip('.'))
            else:
                self.unrecognized.add(word)

    def can_filter(self):
        """
        判断当前的输入是否包含至少一个可识别的筛选条件。

        该函数用于在执行耗时的历史记录遍历前进行预校验。
        如果用户输入的字符串中没有任何一个词能匹配大类（如图片、视频）
        或者有效的后缀（如pdf、jpg），则认为无法执行筛选。

        Returns:
            tuple: (bool, str)
                - bool: True 表示可以执行筛选，False 表示无法执行。
                - str: 提示信息。成功时为 None 或简短提示，失败时为错误原因。
        """
        # 1. 检查是否完全没有识别到任何有效项
        if not self.target_types and not self.target_exts:
            # 如果有无法识别的词，提示用户这些词无效
            if self.unrecognized:
                return False, f"❌ 无法识别您输入的条件：'{', '.join(self.unrecognized)}'。请重新输入，例如：'图片' 或 'pdf'。"
            # 如果用户输入的是纯空格或空字符串
            return False, "⚠️ 您没有输入任何筛选条件，请输入想要查找的类型（如：文本、视频、zip）。"

        # 2. 如果有有效项，但同时也存在部分无法识别的词
        if self.unrecognized:
            return True, f"✅ 已识别部分条件，但忽略了：'{', '.join(self.unrecognized)}'。即将开始筛选..."

        # 3. 完全匹配成功
        return True, None

    def generate_feedback(self):
        """
        生成给用户的识别反馈文案
        """
        if not self.target_types and not self.target_exts:
            return "❌ 未识别到任何有效的筛选类型，请尝试输入 '图片'、'视频' 或后缀名如 'pdf'。"

        # 将内部别名转回中文用于显示
        reverse_map = {'photo': '图片', 'video': '视频', 'voice': '语音',
                       'music': '音乐', 'document': '文件', 'gif': '动图'}
        active_filters = [reverse_map.get(t, t) for t in self.target_types]
        active_filters += [f".{e}" for e in self.target_exts]

        msg = f"🔍 **筛选条件：** {'、'.join(active_filters)}"
        if self.unrecognized:
            msg += f"\n⚠️ **忽略未识别词：** {', '.join(self.unrecognized)}"
        return msg

    def check(self, message):
        """
        核心匹配函数：判断单条 Telethon 消息是否符合条件
        """
        if not message:
            return False

        # --- 1. 处理“文本”类型的筛选 ---
        if 'text' in self.target_types:
            # 如果没有媒体内容，且有文本内容，则判定为纯文本消息
            if not message.media and message.text:
                return True
            # 如果你希望“带图片的文字说明”也算作文本，可以去掉 not message.media 的限制
            # 但通常用户的意图是寻找“纯聊天记录”

        # 如果消息没有媒体，且用户没搜文本，直接返回 False
        if not message.media:
            return False

        # --- A. 后缀精准匹配 ---
        if self.target_exts:
            # message.file.ext 已经处理好了所有媒体的后缀判断
            file_ext = (message.file.ext or '').lower().lstrip(
                '.') if message.file else ''
            if file_ext in self.target_exts:
                return True

        # --- B. 大类模糊匹配 ---
        if not self.target_types:
            return False

        # 1. 图片匹配 (包含原生照片和作为文件发送的图片)
        if 'photo' in self.target_types:
            if isinstance(message.media, MessageMediaPhoto):
                return True
            if message.file and message.file.mime_type.startswith('image/'):
                return True

        # 2. 视频匹配 (包含视频文件、圆形视频)
        if 'video' in self.target_types:
            if message.file and message.file.mime_type.startswith('video/'):
                return True
            if any(isinstance(x, DocumentAttributeVideo) for x in getattr(message.media, 'document', {}).get('attributes', [])):
                return True

        # 3. 文档类匹配 (排除掉音视频后的 Document)
        if 'document' in self.target_types:
            if isinstance(message.media, MessageMediaDocument):
                attrs = message.media.document.attributes
                is_media = any(isinstance(
                    x, (DocumentAttributeVideo, DocumentAttributeAudio)) for x in attrs)
                if not is_media:
                    return True

        # 4. 音乐与语音匹配
        if isinstance(message.media, MessageMediaDocument):
            attrs = message.media.document.attributes
            audio_attr = next(
                (x for x in attrs if isinstance(x, DocumentAttributeAudio)), None)
            if audio_attr:
                if 'voice' in self.target_types and audio_attr.voice:
                    return True
                if 'music' in self.target_types and not audio_attr.voice:
                    return True

        # 5. 动图匹配
        if 'gif' in self.target_types:
            if message.file and message.file.mime_type == 'image/gif':
                return True

        return False

# --- 使用示例 ---


async def main_logic(client, chat_id, user_input_text):
    # 1. 初始化解析器
    searcher = TelethonMediaSearcher(user_input_text)

    # 2. 先给用户发送一个解析反馈
    await client.send_message('me', searcher.generate_feedback())

    # 3. 开始迭代消息
    async for message in client.iter_messages(chat_id, limit=200):
        if searcher.check(message):
            # 找到匹配的消息，执行业务逻辑（如转发、记录 ID）
            print(f"找到匹配: {message.id}")
