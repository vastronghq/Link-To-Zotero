"""
Copyright (c) 2026 by hqwang, All Rights Reserved.

Software     : VScode
Author       : hqwang
Date         : 2026-02-01 08:39:50
LastEditTime : 2026-02-01 09:05:30
Description  :
"""

import html2text


def add():
    return 0


def get_js_template(plugin_obj, template):
    """读取插件ZIP包内的 JS 模板文件"""
    content = plugin_obj.load_resources([template])[template]
    return content.decode("utf-8")


def parse_author_name(author):
    """
    智能解析作者姓名，支持多种格式：
    1. 单字中文名：'陈钧辉' → firstName: '', lastName: '陈钧辉'
    2. 多字中文名：'张 三' → firstName: '张', lastName: '三'
    3. 西式格式：'Bhadra, Pratiti' → firstName: 'Pratiti', lastName: 'Bhadra'
    4. 西式格式：'Smith, John A.' → firstName: 'John A.', lastName: 'Smith'
    5. 直接格式：'John Smith' → firstName: 'John', lastName: 'Smith'
    """
    author = author.strip()

    # 检查是否是 "LastName, FirstName" 格式
    if "," in author:
        parts = [p.strip() for p in author.split(",")]
        if len(parts) >= 2:
            # "Bhadra, Pratiti" 格式
            last_name = parts[0]
            first_name = parts[1]
            # 处理可能有中间名的情况
            remaining = ", ".join(parts[2:]) if len(parts) > 2 else ""
            if remaining:
                first_name = f"{first_name} {remaining}"
            return first_name, last_name

    # 处理普通空格分隔的名字
    parts = author.split()

    # 单个词的名字（可能是单字中文名）
    if len(parts) == 1:
        # 对于单个词，假定为 last name
        return "", parts[0]

    # 两个词的名字
    elif len(parts) == 2:
        # "John Smith" 格式
        return parts[0], parts[1]

    # 多个词的名字
    else:
        # 中文名通常2-3个字，西式可能有中间名
        # 试探性判断：如果全是单字符，可能是中文名
        if all(len(part) == 1 for part in parts):
            # 中文名如 "张 三 丰"
            first_name = parts[0]  # 第一个字作为名
            last_name = "".join(parts[1:])  # 剩余作为姓
        else:
            # 西式名字，假定第一个是名，最后一个是姓，中间是中间名
            first_name = " ".join(parts[:-1])
            last_name = parts[-1]

        return first_name, last_name


def create_authors_js(authors_list):
    """生成 JavaScript 作者数组"""
    authors_js = []

    for author in authors_list:
        first_name, last_name = parse_author_name(author)
        authors_js.append(
            {
                "firstName": first_name,
                "lastName": last_name,
                "creatorType": "author",
            }
        )

    return authors_js


def convert_html_to_text(html_content):
    """处理摘要 HTML 转文本"""
    if not html_content or html_content == "无摘要":
        return "无摘要"
    converter = html2text.HTML2Text()
    converter.ignore_links = True
    return converter.handle(html_content).strip()
