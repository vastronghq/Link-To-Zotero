"""
Copyright (c) 2026 by hqwang, All Rights Reserved.

Software     : VScode
Author       : hqwang
Date         : 2026-01-31 13:11:54
LastEditTime : 2026-01-31 13:15:17
Description  :
"""

import html2text
from calibre.gui2 import error_dialog
from calibre.gui2.actions import InterfaceAction, menu_action_unique_name
from PyQt5.QtWidgets import QApplication
from qt.core import QDialog, QLabel, QMenu, QPushButton, QTextEdit, QVBoxLayout


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
        "images/link_icon_2.png",
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
        icon_link = get_icons("images/icon_link_2.png", "calibre_link2zotero_icon_1")
        icon_calendar = get_icons(
            "images/icon_calendar.png", "calibre_link2zotero_icon_2"
        )
        self.qaction.setIcon(icon_link)

        # Setup menu
        self.menu = QMenu()
        self.qaction.setMenu(self.menu)

        self.add_menu(
            _("Step 1: Link Book's PDFs to Zotero"),
            icon_link,
            _("Configure No Trans"),
            self.generate_zotero_import_script,
        )

        self.add_menu(
            _('Step 2: Apply Book’s "timestamp" to Zotero'),
            icon_calendar,
            _("Configure No Trans"),
            self.sync_timestamp,
        )

        # --- 2. 绑定点击事件 ---
        # 当用户点击工具栏按钮时，执行 self.generate_zotero_import_script 方法
        self.qaction.triggered.connect(self.generate_zotero_import_script)

    def add_menu(self, text, icon, tooltip, action):
        uni_name = menu_action_unique_name(self, text)
        action = self.create_menu_action(
            menu=self.menu,
            unique_name=uni_name,
            text=text,
            icon=icon,
            description=tooltip,
            triggered=action,
        )
        self.menu.addAction(action)
        return action

    def sync_timestamp(self):
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows:
            return error_dialog(self.gui, "错误", "请先选中至少一本书籍。", show=True)

        db = self.gui.current_db.new_api

        error_dialog(
            self.gui,
            "调试",
            db.field_for("#created", 11).strftime("%Y-%m-%d %H:%M:%S"),
            show=True,
        )

    def get_js_template(self, template):
        """读取插件ZIP包内的 JS 模板文件"""
        content = self.load_resources([template])[template]
        return content.decode("utf-8")

    def generate_zotero_import_script(self):
        # error_dialog(
        #     self.gui,
        #     "调试",
        #     "啊士大夫萨芬仅仅是",
        #     show=True,
        # )
        """
        Link2Zotero 核心业务逻辑
        """
        # 1. 获取选中的书籍 ID
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows:
            return error_dialog(self.gui, "错误", "请先选中至少一本书籍。", show=True)

        db = self.gui.current_db.new_api
        book_scripts = []
        summary_titles = []

        # 2. 遍历每一本书
        for row in rows:
            book_id = self.gui.library_view.model().id(row.row())
            metadata = db.get_metadata(book_id)
            title = metadata.title
            summary_titles.append(title)

            # --- 元数据处理 ---
            authors = metadata.authors  # 返回列表
            published = (
                metadata.pubdate.strftime("%Y-%m-%d")
                if metadata.pubdate
                else "未知日期"
            )
            publisher = metadata.publisher if metadata.publisher else "未知出版社"
            language = "zh" if metadata.language == "zho" else metadata.language
            timestamp = db.field_for("#created", book_id).strftime("%Y-%m-%d %H:%M:%S")
            identifiers = (
                (metadata.identifiers.get("isbn") or "")
                if metadata.identifiers
                else "无标识符"
            )
            abstract_html = metadata.comments if metadata.comments else "无摘要"
            converter = html2text.HTML2Text()
            converter.ignore_links = True  # 忽略链接
            abstract_text = converter.handle(abstract_html).strip()

            # --- 文件格式和附件路径获取 ---
            formats = db.formats(book_id)

            if "PDF" not in formats:
                # 如果没有PDF，在日志中记录跳过
                skip_script = (
                    f"results.push(`[跳过] 书籍 {repr(title)} 没有 PDF 格式`);"
                )
                book_scripts.append(skip_script)
                continue

            file_path = db.format_abspath(book_id, "PDF")

            # --- 生成单本书的 JS 片段 ---
            single_book_js_template = self.get_js_template("single_book_js_template.js")
            single_book_js_code = single_book_js_template.replace(
                "__TITLE__", repr(title)
            )
            single_book_js_code = single_book_js_code.replace(
                "__AUTHORS__", repr(self.create_authors_js(authors))
            )
            single_book_js_code = single_book_js_code.replace(
                "__PUBLISHED__", repr(published)
            )
            single_book_js_code = single_book_js_code.replace(
                "__PUBLISHER__", repr(publisher)
            )
            single_book_js_code = single_book_js_code.replace(
                "__LANGUAGE__", repr(language)
            )
            single_book_js_code = single_book_js_code.replace(
                "__IDENTIFIERS__", repr(identifiers)
            )
            single_book_js_code = single_book_js_code.replace(
                "__ABSTRACT_TEXT__", repr(abstract_text)
            )
            single_book_js_code = single_book_js_code.replace(
                "__FILE_PATH__", repr(file_path)
            )
            single_book_js_code = single_book_js_code.replace(
                "__TIMESTAMP__", repr(timestamp)
            )

            # single_book_js = textwrap.dedent(single_book_js).strip()
            book_scripts.append(single_book_js_code)

        # 3. 合并所有脚本，构建完整的日志回传逻辑
        all_books_js = "\n".join(book_scripts)
        # all_books_js = textwrap.dedent(all_books_js).strip()

        final_js_template = self.get_js_template("final_js_template.js")
        final_js_code = final_js_template.replace("__ALL_BOOKS_JS__", all_books_js)
        final_js_code = final_js_code.replace("__LEN_ROWS__", str(len(rows)))

        # 4. 弹出对话框（显示第一本书名作为标题，或显示选中数量）
        dialog_title = (
            summary_titles[0]
            if len(summary_titles) == 1
            else f"批量处理 {len(summary_titles)} 本书"
        )
        self.show_copy_dialog(final_js_code, dialog_title)

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
        text_edit.setReadOnly(True)
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
