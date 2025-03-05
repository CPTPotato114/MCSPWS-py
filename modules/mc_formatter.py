import re
from html import escape

def mc_to_html(text):
    """
    将Minecraft格式代码转换为HTML标签
    支持颜色代码和格式代码（§格式）
    """
    # 转义HTML特殊字符
    text = escape(text)
    
    # 处理渐变色标签（支持 <gradient:#FF0000:#00FF00>文本</gradient> 格式）
    text = re.sub(
        r'<gradient:(#[\da-fA-F]{6}):(#[\da-fA-F]{6})>(.+?)</gradient>',
        _handle_gradient,
        text,
        flags=re.DOTALL
    )
    
    # 定义转换规则（支持16种颜色+格式代码）
    replacements = {
        '0': ('<span style="color: #000000;">', '</span>'),   # 黑色
        '1': ('<span style="color: #0000AA;">', '</span>'),   # 深蓝
        '2': ('<span style="color: #00AA00;">', '</span>'),   # 深绿
        '3': ('<span style="color: #00AAAA;">', '</span>'),   # 湖蓝
        '4': ('<span style="color: #AA0000;">', '</span>'),   # 深红
        '5': ('<span style="color: #AA00AA;">', '</span>'),   # 紫色
        '6': ('<span style="color: #FFAA00;">', '</span>'),   # 金色
        '7': ('<span style="color: #AAAAAA;">', '</span>'),   # 灰色
        '8': ('<span style="color: #555555;">', '</span>'),   # 深灰
        '9': ('<span style="color: #5555FF;">', '</span>'),   # 蓝色
        'a': ('<span style="color: #55FF55;">', '</span>'),   # 亮绿
        'b': ('<span style="color: #55FFFF;">', '</span>'),   # 天蓝
        'c': ('<span style="color: #FF5555;">', '</span>'),   # 红色
        'd': ('<span style="color: #FF55FF;">', '</span>'),   # 粉红
        'e': ('<span style="color: #FFFF55;">', '</span>'),   # 黄色
        'f': ('<span style="color: #FFFFFF;">', '</span>'),   # 白色
        'l': ('<strong>', '</strong>'),                      # 加粗
        'm': ('<del>', '</del>'),                            # 删除线
        'n': ('<u>', '</u>'),                                # 下划线
        'o': ('<em>', '</em>'),                              # 斜体
        'r': ('', '')                                        # 重置样式
    }

    # 使用正则匹配所有格式代码
    pattern = re.compile(r'§([0-9a-fk-or])', re.IGNORECASE)
    stack = []
    output = []
    pos = 0

    for match in pattern.finditer(text):
        code = match.group(1).lower()
        start, end = match.span()
        
        # 添加之前的文本
        output.append(text[pos:start])
        pos = end
        
        if code == 'r':  # 重置所有样式
            close_tags = ''.join(tag[1] for tag in reversed(stack))
            output.append(close_tags)
            stack.clear()
        elif code in replacements:
            open_tag, close_tag = replacements[code]
            output.append(open_tag)
            stack.append((code, close_tag))
        # 其他格式代码（如k=随机字符）暂不处理

    # 添加剩余文本
    output.append(text[pos:])
    
    # 关闭所有未闭合的标签
    output.extend(tag[1] for tag in reversed(stack))
    
    return ''.join(output)

def _handle_gradient(match):
    """处理渐变色匹配"""
    start_color = match.group(1)
    end_color = match.group(2)
    content = match.group(3)
    
    # 生成唯一ID避免样式冲突
    gradient_id = f"gradient-{abs(hash(match.group(0)))}"
    
    return (
        f'<span class="{gradient_id}">{content}</span>'
        f'<style>.{gradient_id} {{'
        f'background: linear-gradient(90deg, {start_color}, {end_color});'
        f'-webkit-background-clip: text;'
        f'background-clip: text;'
        f'color: transparent;'
        f'display: inline-block;}}'
        f'</style>'
    )