# 消息筛选，里面又有根据消息类型筛选，根据文件大小筛选

from telethon.tl.types import (
    PeerUser,
    PeerChat,
    PeerChannel,
    MessageService, MessageMediaWebPage, MessageMediaPhoto, MessageMediaDocument, MessageMediaPoll, MessageMediaPaidMedia,
    MessageMediaUnsupported,
    MessageMediaGiveaway, MessageMediaGiveawayResults
)

from guis.file_type_handles.media_type_judge import human_readable_size
from guis.message_filters.user_friendly_link_filter import process_links_filter

import logging
logger = logging.getLogger(__name__)


def msg_media_type_filter(message, frozen_config):
  # 图片、视频、语音、文件、纯文本
  # TODO
  # https://gemini.google.com/app/767ceaeecc5ec695
  # https://gemini.google.com/app/fdd46bcf097df764
    media_type_searcher = frozen_config['media_type_searcher']
    return media_type_searcher.check(message)


def msg_media_size_filter(message, frozen_config):
    # 首先，获取信息的文件大小
    # 获取当前消息的“逻辑大小”
    # 如果有文件，取文件大小；如果是纯文本，大小视为 0
    current_msg_size = message.file.size if message.file else 0

    min_b = frozen_config['min_file_size']
    max_b = frozen_config['max_file_size']
    if min_b <= current_msg_size <= max_b:
        # 符合条件的记录（包括文本消息和符合大小的媒体）
        print(
            f"筛选通过: ID={message.id}, 大小={current_msg_size}字节（{human_readable_size(current_msg_size)}）")
        return True

    print(
        f"筛选失败: ID={message.id}, 大小={current_msg_size}字节（{human_readable_size(current_msg_size)}）")
    return False


def rule_syntax_filter(message, frozen_config=None):
    rule_syntax_filter_input = frozen_config['rule_syntax_filter_input']
    return process_links_filter(rule_syntax_filter_input, message)


def should_skip_message(message, frozen_config=None, ctx=None):
    """
    具体的过滤规则判断
    返回 True: 表示消息不合格，应该跳过
    返回 False: 表示消息合格，需要处理
    """

    # 规则 3: 关键词屏蔽
    # if "spam" in msg.get('content', ''):
    #     return True
    # 服务消息跳过
    if (type(message) == MessageService):
        return True

    print('\033[96m' + '=' * 80 + '\033[0m')
    print(f"\033[1;32m 变量值： {message.media} 👈  message.media  \033[m")
    # print('type(message)', type(message))
    # print('type(message.media)', type(message.media))
    # print(message)

    # 抽奖消息跳过
    if (message.media and type(message.media) in [MessageMediaGiveaway, MessageMediaGiveawayResults]):
        return True

    # 对于特殊消息，比如频道开启私信 之类的跳过
    if (message.media and type(message.media) in [MessageMediaUnsupported] and not message.message):
        logger.info(f'跳过了具有无法识别的媒体内容而且无文案的消息：{message.id}')
        return True

    # 文件大小筛选
    if frozen_config['is_file_size_active']:
        if not msg_media_size_filter(message, frozen_config):
            return True  # 文件大小不满足的消息，直接跳过

    # 媒体类型筛选
    if frozen_config['is_media_type_active']:
        if not msg_media_type_filter(message, frozen_config):
            print('\033[96m' + '=' * 80 + '\033[0m')
            print(f"消息不符合媒体类型: {message.id}")
            return True

    # 自定义筛选 这个类似于指令模式，以后可以定义很多规则在里面，本次开发只定义了【包含链接】【排除链接】
    if frozen_config['rule_syntax_filter_input']:
        if not rule_syntax_filter(message, frozen_config):
            return True

    return False


# def msg_filter(messages):
#     """
#     高层处理函数：负责执行过滤动作
#     """
#     # 使用列表推导式，保留那些 "不应该被跳过" 的消息
#     return [m for m in messages if not should_skip_message(m)]
