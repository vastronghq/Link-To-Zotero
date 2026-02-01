"""
Copyright (c) 2026 by hqwang, All Rights Reserved.

Software     : VScode
Author       : hqwang
Date         : 2026-01-31 13:11:54
LastEditTime : 2026-01-31 13:15:17
Description  :
"""

from calibre.gui2 import error_dialog
from calibre.gui2.actions import InterfaceAction, menu_action_unique_name
from calibre_plugins.link_to_zotero.common_utils import (
    convert_html_to_text,
    get_js_template,
    simple_name_parser,
)
from PyQt5.QtWidgets import QApplication
from qt.core import QDialog, QLabel, QMenu, QPushButton, QTextEdit, QVBoxLayout


class LinkToZoteroAction(InterfaceAction):
    """
    插件的 UI 类，控制工具栏按钮的行为。
    """

    # 内部引用名称，建议与类名相关联
    name = "Link To Zotero"

    # 定义动作规范：(默认按钮文本, 图标路径, 悬浮提示, 快捷键)
    # 注意：这里的图标路径是相对于插件包根目录的默认位置
    action_spec = (
        "Link To Zotero",
        "images/link_icon_2.png",
        "点击执行 Link To Zotero 插件功能",
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
        icon_interface = get_icons(
            "images/icon_2.png", "calibre_link_to_zotero_icon_interface"
        )
        icon_menu_2 = get_icons(
            "images/icon_3.png", "calibre_link_to_zotero_icon_menu_2"
        )
        self.qaction.setIcon(icon_interface)

        # Setup menu
        self.menu = QMenu()
        self.qaction.setMenu(self.menu)

        self.add_menu(
            _("Step 1: Link Book's PDF to Zotero"),
            icon_interface,
            _("Configure No Trans"),
            self.generate_zotero_script,
        )

        self.add_menu(
            _('Step 2: Apply Book’s "timestamp" to Zotero'),
            icon_menu_2,
            _("Configure No Trans"),
            self.sync_timestamp,
        )

        # --- 2. 绑定点击事件 ---
        # 当用户点击工具栏按钮时，执行 self.generate_zotero_script 方法
        self.qaction.triggered.connect(self.generate_zotero_script)

        db = self.gui.current_db.new_api
        if "#in_zotero" not in db.field_metadata.custom_field_keys():
            db.create_custom_column(
                label="in_zotero",  # 查阅名称 (自动加#)
                name="In Zotero",  # 列标题
                datatype="bool",  # 数据类型：datatype: 'text', 'bool', 'int', 'float', 'rating', 'datetime', 'series', 'comments'
                is_multiple=False,  # 是否多值
                editable=True,  # 是否可编辑
                display={},  # 额外显示配置
            )

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

    def generate_zotero_script(self):
        """
        Link To Zotero 核心业务逻辑
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
            res = metadata.pubdate.strftime("%Y-%m-%d") if metadata.pubdate else ""
            published = res if res[:2] in ["18", "19", "20", "21"] else ""
            publisher = metadata.publisher if metadata.publisher else ""
            language = "zh" if metadata.language == "zho" else metadata.language
            timestamp = (
                db.field_for("#created", book_id).strftime("%Y-%m-%d %H:%M:%S")
                if db.field_for("#created", book_id).strftime("%Y-%m-%d %H:%M:%S")
                else ""
            )
            identifiers = (
                (metadata.identifiers.get("isbn") or "") if metadata.identifiers else ""
            )
            abstract_text = (
                convert_html_to_text(metadata.comments) if metadata.comments else ""
            )

            # --- 文件格式和附件路径获取 ---
            formats = db.formats(book_id)

            if "PDF" not in formats:
                # 如果没有PDF，在日志中记录跳过
                skip_script = (
                    f"results.push(`[跳过] in_书籍 {repr(title)} 没有 PDF 格式`);"
                )
                book_scripts.append(skip_script)
                db.set_field("#in_zotero", {book_id: False})
                continue

            db.set_field("#in_zotero", {book_id: True})

            file_path = db.format_abspath(book_id, "PDF")

            # --- 生成单本书的 JS 片段 ---
            single_book_js_template = get_js_template(
                self, "single_book_js_template.js"
            )
            single_book_js_code = single_book_js_template.replace(
                "__TITLE__", repr(title)
            )
            single_book_js_code = single_book_js_code.replace(
                "__AUTHORS__", repr(simple_name_parser(authors))
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

        final_js_template = get_js_template(self, "final_js_template.js")
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
        d.setWindowTitle(f"Link To Zotero - {title}")
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
