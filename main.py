"""
Copyright (c) 2026 by hqwang, All Rights Reserved.

Software     : VScode
Author       : hqwang
Date         : 2026-01-31 13:11:54
LastEditTime : 2026-01-31 13:15:17
Description  :
"""

import textwrap

import html2text
from calibre.gui2 import error_dialog
from calibre.gui2.actions import InterfaceAction
from PyQt5.QtWidgets import QApplication
from qt.core import QDialog, QLabel, QPushButton, QTextEdit, QVBoxLayout


class Link2ZoteroAction(InterfaceAction):
    """
    插件的 UI 类，控制工具栏按钮的行为。
    """

    # 内部引用名称，建议与类名相关联
    name = "Link2ZoteroAction"

    # 定义动作规范：(默认按钮文本, 图标路径, 悬浮提示, 快捷键)
    # 注意：这里的图标路径是相对于插件包根目录的默认位置
    action_spec = (
        "Link2Zotero",
        "images/link_icon_142996.png",
        "点击执行 Link2Zotero 插件功能",
        None,
    )

    def genesis(self):
        """
        当 Calibre 启动并初始化插件时调用此方法。
        """
        # --- 1. 加载并设置图标 ---
        # get_icons 是 Calibre 内置函数，专门从插件 zip 包中提取图片
        # 参数 1: images 文件夹下的文件名
        # 参数 2: 该图标在内存中的唯一标识字符串
        icon = get_icons("images/link_icon_142996.png", "calibre_link2zotero_icon")
        self.qaction.setIcon(icon)

        # --- 2. 绑定点击事件 ---
        # 当用户点击工具栏按钮时，执行 self.run_action 方法
        self.qaction.triggered.connect(self.run_action)

    def run_action(self):
        """
        Link2Zotero 核心业务逻辑
        """
        # 1. 获取选中的书籍 ID
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows:
            return error_dialog(self.gui, "错误", "请先选中至少一本书籍。", show=True)

        # 2. 获取第一本选中书籍的元数据
        book_id = self.gui.library_view.model().id(rows[0].row())
        db = self.gui.current_db.new_api

        # 2. 读取元数据
        metadata = db.get_metadata(book_id)
        title = metadata.title
        authors = metadata.authors  # 返回列表
        published = (
            metadata.pubdate.strftime("%Y-%m-%d") if metadata.pubdate else "未知日期"
        )
        publisher = metadata.publisher if metadata.publisher else "未知出版社"
        language = "zh" if metadata.language == "zho" else metadata.language
        timestamp = metadata.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        identifiers = (
            (metadata.identifiers.get("isbn") or "")
            if metadata.identifiers
            else "无标识符"
        )
        abstract_html = metadata.comments if metadata.comments else "无摘要"
        converter = html2text.HTML2Text()
        converter.ignore_links = True  # 忽略链接
        abstract_text = converter.handle(abstract_html).strip()

        formats = db.formats(book_id)

        if "PDF" not in formats:
            return error_dialog(
                self.gui,
                "错误",
                "所选书籍不包含 PDF 格式，请手动处理。",
                show=True,
            )

        file_path = db.format_abspath(book_id, "PDF")

        # 3. 生成 JavaScript 代码
        js_code = f"""
        // Link2Zotero 自动化脚本
        var item = new Zotero.Item('book');
        item.setField('title', {repr(title)});
        item.setCreators({repr(self.create_authors_js(authors))});
        item.setField('date', {repr(published)});
        item.setField('publisher', {repr(publisher)});
        item.setField('language', {repr(language)});
        item.setField('ISBN', {repr(identifiers)});
        item.setField('abstractNote', {repr(abstract_text)});
        var itemID = await item.saveTx();

        try {{
            await Zotero.Attachments.linkFromFile({{
                file: {repr(file_path)},
                parentItemID: item.id,
                contentType: 'application/pdf'
            }});
            const now = new Date();
            const time = now.toLocaleTimeString()
            return `[${{time}}] Link2Zotero：1.书籍 {repr(title)} 条目创建成功；2.PDF 链接成功 🎉🎉🎉`;
        }} catch (e) {{
            return "错误：" + e.toString();
        }}

        alert('Link2Zotero 脚本执行完成，已添加书籍到 Zotero。');
        """

        js_code = textwrap.dedent(js_code).strip()

        # info_dialog(
        #     self.gui,
        #     "生成的 JavaScript 代码",
        #     js_code,
        #     show=True,
        # )

        # 5. 弹出自定义对话框，展示代码并提供复制按钮
        self.show_copy_dialog(js_code, title)

    def show_copy_dialog(self, code, title):
        """
        创建一个简单的对话框来显示生成的代码
        """
        d = QDialog(self.gui)
        d.setWindowTitle(f"Link2Zotero - {title}")
        layout = QVBoxLayout()
        d.setLayout(layout)

        layout.addWidget(
            QLabel('请复制下方脚本，在 Zotero "运行 JavaScript" 窗口中运行：')
        )

        # 代码展示框
        text_edit = QTextEdit(d, minimumWidth=600, minimumHeight=400)
        text_edit.setPlainText(code)
        text_edit.setReadOnly(False)
        layout.addWidget(text_edit)

        # 复制并关闭按钮
        btn = QPushButton("复制到剪贴板并关闭", d)

        def copy_and_close():
            # 使用 Qt 的剪贴板
            clipboard = QApplication.clipboard()
            clipboard.setText(code)
            d.accept()

        btn.clicked.connect(copy_and_close)
        layout.addWidget(btn)
        d.exec_()

    def parse_author_name(self, author):
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

    def create_authors_js(self, authors_list):
        """生成 JavaScript 作者数组"""
        authors_js = []

        for author in authors_list:
            first_name, last_name = self.parse_author_name(author)
            authors_js.append(
                {
                    "firstName": first_name,
                    "lastName": last_name,
                    "creatorType": "author",
                }
            )

        return authors_js
