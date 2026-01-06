import re


def parse_size_to_bytes(size_str: str, default_unit: str = "MB") -> float:
    """
    将用户输入的字符串转化为统一的字节数(Bytes)或目标单位数值。
    支持输入格式: "10", "1.5G", "500MB", "20kb" 等。
    """
    if not size_str or not size_str.strip():
        raise ValueError("输入不能为空")

    # 清理空格并转为大写
    clean_input = size_str.strip().upper()

    # 匹配数字部分和单位部分
    # 预设单位权重
    units = {
        "B": 1,
        "K": 1024, "KB": 1024,
        "M": 1024**2, "MB": 1024**2,
        "G": 1024**3, "GB": 1024**3,
        "T": 1024**4, "TB": 1024**4
    }

    # 正则表达式拆分数字和字母
    match = re.match(r"^([0-9.]+)\s*([A-Z]*)$", clean_input)
    if not match:
        raise ValueError(f"无效的格式: '{size_str}'")

    number_part, unit_part = match.groups()

    try:
        value = float(number_part)
    except ValueError:
        raise ValueError(f"数字部分无效: '{number_part}'")

    # 处理单位：如果没有单位则使用默认单位
    actual_unit = unit_part if unit_part else default_unit.upper()

    if actual_unit not in units:
        raise ValueError(f"不支持的单位: '{actual_unit}'")

    # 返回以字节为单位的数值 (方便后续做文件对比，os.path.getsize 返回的是字节)
    return value * units[actual_unit]


def get_file_size_range(start_val: str, end_val: str):
    """
    获取范围，并返回一个标志位，判断筛选是否激活。
    """
    # 预处理：去除空格
    s = start_val.strip() if start_val else ""
    e = end_val.strip() if end_val else ""

    # 如果两个输入框都为空，直接返回未激活状态
    if not s and not e:
        return None, None, False

    # 逻辑同前：处理单边为空的情况
    min_bytes = parse_size_to_bytes(s) if s else 0.0
    max_bytes = parse_size_to_bytes(e) if e else float('inf')

    if min_bytes > max_bytes:
        raise ValueError("起始大小不能大于结束大小")

    return min_bytes, max_bytes, True
# 示例用法


# def on_confirm_click():
#     entry_start = None
#     entry_end = None
#     # 假设 entry_start 和 entry_end 是你的 Tkinter Entry 组件
#     raw_start = entry_start.get()
#     raw_end = entry_end.get()

#     try:
#         size_range = get_file_size_range(raw_start, raw_end)
#         print(f"转换成功，字节范围: {size_range}")
#         # 后续筛选逻辑...
#     except ValueError as err:
#         messagebox.showerror("输入错误", str(err))


# async def filter_messages_by_size(client, entity, start_input, end_input, limit=None):
#     """
#     流式获取并过滤消息
#     :param client: Telethon TelegramClient 实例
#     :param entity: 对话 ID 或实体
#     :param start_input: 用户输入的开始大小 (如 "10MB")
#     :param end_input: 用户输入的结束大小 (如 "1GB")
#     """
#     try:
#         # 1. 调用之前定义的通用转换函数获取字节范围
#         min_bytes, max_bytes = get_file_size_range(start_input, end_input)
#     except ValueError as e:
#         print(f"参数错误: {e}")
#         return

#     # 2. 使用 iter_messages 获取消息迭代器
#     # 注意：为了效率，我们只获取包含媒体文件的消息
#     async for message in client.iter_messages(entity, limit=limit):
#         # 检查消息是否包含文件
#         if message.file:
#             file_size = message.file.size  # Telethon 直接提供字节大小

#             # 3. 筛选逻辑
#             if min_bytes <= file_size <= max_bytes:
#                 yield message  # 使用 yield 构造异步生成器，非常 Pythonic


# async def main():
#     # 假设这是从 tkinter 输入框获取的值
#     user_start = entry_start.get()  # 比如 "20MB"
#     user_end = entry_end.get()     # 比如 "100MB"

#     print(f"正在搜索范围在 {user_start} 到 {user_end} 之间的文件...")

#     async for msg in filter_messages_by_size(client, 'me', user_start, user_end):
#         # 此时得到的 msg 已经是过滤好的了
#         print(
#             f"发现匹配文件: {msg.file.name} | 大小: {msg.file.size / 1024**2:.2f} MB")
#         # 可以执行下载或其他操作
#         # await msg.download_media()
