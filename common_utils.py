"""
Copyright (c) 2026 by hqwang, All Rights Reserved.

Software     : VScode
Author       : hqwang
Date         : 2026-02-01 08:39:50
LastEditTime : 2026-02-01 09:05:30
Description  :
"""

import re

import html2text


def add():
    return 0


def get_js_template(plugin_obj, template):
    """读取插件ZIP包内的 JS 模板文件"""
    content = plugin_obj.load_resources([template])[template]
    return content.decode("utf-8")


def simple_name_parser(raw_list):
    js_obj_list = []

    for item in raw_list:
        # 1. 基础清洗：去掉 [美]、(美) 等标签
        # 同时去掉括号内的内容，例如 "史蒂芬·普拉达（stephen Prata）" -> "史蒂芬·普拉达"
        name = re.sub(r"\[.*?\]|\(.*?\)|\（.*?\）", "", item).strip()

        # 2. 处理英文逗号倒置逻辑： "Bhadra, Pratiti" -> "Pratiti Bhadra"
        if "," in name:
            parts = [p.strip() for p in name.split(",")]
            if len(parts) == 2:
                # 将 "姓, 名" 转换为 "名 姓"
                name = f"{parts[1]} {parts[0]}"

        if not name:
            continue

        js_obj_list.append(
            {
                "firstName": "",
                "lastName": name,
                "creatorType": "author",
            }
        )

    return js_obj_list


def convert_html_to_text(html_content):
    """处理摘要 HTML 转文本"""
    if not html_content or html_content == "无摘要":
        return "无摘要"
    converter = html2text.HTML2Text()
    converter.ignore_links = True
    return converter.handle(html_content).strip()
