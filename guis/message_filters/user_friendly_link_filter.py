from telethon import TelegramClient, events
from telethon.tl.types import MessageEntityUrl, MessageEntityTextUrl


def has_links(message) -> bool:
    """
    判断单条消息中是否包含任何形式的链接。

    参数:
    - message: Telethon 的 Message 对象

    返回值:
    - bool: 如果包含链接返回 True，否则返回 False
    """
    # 1. 基础检查：如果消息没有实体，可能只是纯文本或媒体
    if not message.entities:
        return False

    # 2. 遍历消息中的实体，寻找 URL 类型
    for entity in message.entities:
        if isinstance(entity, (MessageEntityUrl, MessageEntityTextUrl)):
            return True

    return False


def process_links_filter(input_str, message=None):

    if (not input_str) or (not message):
        print("未发现相关指令，不执行任何操作。" + input_str)
        return

    keyword1 = "包含链接"
    keyword2 = "排除链接"

    # 使用 rfind 获取关键词最后一次出现的索引位置
    # 如果没找到，返回 -1
    pos1 = input_str.rfind(keyword1)
    pos2 = input_str.rfind(keyword2)

    # 情况 1：两个都没找到
    if pos1 == -1 and pos2 == -1:
        print('"未发现相关指令，不执行任何操作。"')
        return

    # 情况 2：两者都存在，或者只存在其中一个
    # 比较两者的索引，谁大说明谁出现在最后（即“后面的那个”）
    if pos1 > pos2:
        print(f"执行操作：【{keyword1}】", has_links(message))
        return has_links(message)
    else:
        print(f"执行操作：【{keyword2}】", not has_links(message))
        return not has_links(message)


# --- 测试代码 ---
# test_cases = [
#     "请帮我处理，包含链接",               # 只有包含
#     "这里需要排除链接",                   # 只有排除
#     "包含链接，但最后还是要排除链接",      # 两者都有，排除在后
#     "排除链接，后来决定包含链接",          # 两者都有，包含在后
#     "这段话里什么都没有"                  # 都没有
# ]

# for text in test_cases:
#     print(f"输入: {text}  => 结果: {process_links(text)}")


async def filter_messages_by_link(messages, mode="include"):
    """
    对消息列表进行筛选。

    参数:
    - messages: iter_messages 返回的消息迭代器或列表
    - mode: 筛选模式。
        - "include": 仅保留【包含链接】的消息
        - "exclude": 仅保留【不包含链接】的消息

    返回值:
    - 过滤后的消息列表
    """
    filtered_list = []

    async for msg in messages:
        # 如果消息本身没有文本内容（例如单纯的投票、服务通知），跳过
        if not msg.text:
            continue

        contains_link = await has_links(msg)

        if mode == "include" and contains_link:
            filtered_list.append(msg)
        elif mode == "exclude" and not contains_link:
            filtered_list.append(msg)

    return filtered_list

# --- 使用示例 ---


async def main():
    # 假设已经初始化了 client
    async for message in client.iter_messages(chat_id, limit=100):
        # 实时处理示例：
        if await has_links(message):
            print(f"发现带链接的消息: {message.id}")
        else:
            print(f"这是一条纯文本消息: {message.id}")

    # 批量筛选示例：
    # all_msgs = client.iter_messages(chat_id, limit=50)
    # only_links = await filter_messages_by_link(all_msgs, mode="include")
