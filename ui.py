"""
Copyright (c) 2026 by hqwang, All Rights Reserved.

Software     : VScode
Author       : hqwang
Date         : 2026-01-31 13:11:54
LastEditTime : 2026-01-31 13:15:17
Description  :
"""

import json

from calibre.gui2 import error_dialog, info_dialog, question_dialog
from calibre.gui2.actions import InterfaceAction, menu_action_unique_name
from calibre.utils.logging import default_log
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
        "同步选中书籍到 Zotero",
        None,
    )

    def genesis(self):
        """
        当 Calibre 启动并初始化插件时调用此方法。
        """
        # 初始化图标
        # get_icons 是 Calibre 内置函数，专门从插件 zip 包中提取图片
        # 参数 1: images 文件夹下的文件名
        # 参数 2: 该图标在内存中的唯一标识字符串
        icon_interface = get_icons("images/icon_2.png", "icon_main")
        icon_sync = get_icons("images/icon_3.png", "icon_sync")
        self.qaction.setIcon(icon_interface)
        # self._check_and_create_column()

        # 构建菜单
        self.menu = QMenu()
        self.qaction.setMenu(self.menu)

        self.add_menu(
            "双向同步检查 (清理)",
            icon_sync,
            "检查并同步两端删除状态",
            self.generate_check_script,
        )

        # 绑定主按钮点击事件
        # 当用户点击工具栏按钮时，执行 self.generate_import_script 方法
        self.qaction.triggered.connect(self.generate_import_script)

        # 内部状态管理
        self.clipboard = QApplication.clipboard()

    def _check_and_create_column(self):
        db = self.gui.current_db.new_api
        is_exist = "#in_zotero" in db.field_metadata.custom_field_keys()
        if not is_exist:
            default_log.warn("未检测到 '#in_zotero' 自定义列，尝试创建...")
            # 创建自定义列
            db.create_custom_column(
                label="in_zotero",
                name="In Zotero",
                datatype="bool",
                is_multiple=False,
                display={},
            )
            info_dialog(
                self.gui,
                "初始化",
                "已为您创建 '#in_zotero' 自定义列，请**重启 Calibre** 以启用同步功能。",
                show=True,
            )
        return is_exist

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

    # --- 核心逻辑 A：导入脚本生成 ---
    def generate_import_script(self):
        if not self._check_and_create_column():
            return
        # 1. 获取选中的书籍 ID
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows:
            return error_dialog(self.gui, "错误", "请先选中至少一本书籍。", show=True)

        db = self.gui.current_db.new_api
        book_scripts = []

        # 2. 遍历每一本书
        for row in rows:
            book_id = self.gui.library_view.model().id(row.row())
            script = self._build_single_book_js(db, book_id)
            if script:
                book_scripts.append(script)
        final_template = get_js_template(self, "import_final.js")
        js_code = final_template.replace("__ALL_BOOKS_JS__", "\n".join(book_scripts))
        js_code = js_code.replace("__LEN_ROWS__", str(len(rows)))

        self._show_and_listen(js_code, f"导入 {len(rows)} 本书籍")

    def _build_single_book_js(self, db, book_id):
        metadata = db.get_metadata(book_id)
        formats = db.formats(book_id)
        if "PDF" not in formats:
            return f"results.push(`[跳过] {repr(mi.title)} 无 PDF`);"
        file_path = db.format_abspath(book_id, "PDF")

        title = metadata.title
        authors = metadata.authors
        published = metadata.pubdate.strftime("%Y-%m-%d") if metadata.pubdate else ""
        published = published if published[:2] in ["18", "19", "20", "21"] else ""
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

        tpl = get_js_template(self, "single_book_js_template.js")
        # 填充元数据
        tpl = tpl.replace("__TITLE__", json.dumps(title))
        tpl = tpl.replace("__AUTHORS__", repr(simple_name_parser(authors)))
        tpl = tpl.replace("__PUBLISHED__", repr(published))
        tpl = tpl.replace("__PUBLISHER__", repr(publisher))
        tpl = tpl.replace("__LANGUAGE__", repr(language))
        tpl = tpl.replace("__IDENTIFIERS__", repr(identifiers))
        tpl = tpl.replace("__ABSTRACT_TEXT__", repr(abstract_text))
        tpl = tpl.replace("__FILE_PATH__", repr(file_path))
        tpl = tpl.replace("__TIMESTAMP__", repr(timestamp))
        tpl = tpl.replace("__BOOK_ID__", repr(book_id))
        return tpl

    # --- 核心逻辑 B：检查脚本生成 ---
    def generate_check_script(self):
        db = self.gui.current_db.new_api
        all_marked_ids = list(db.search("#in_zotero:true"))

        tpl = get_js_template(self, "sync_check.js")
        js_code = tpl.replace("__CALIBRE_MARKED_IDS__", json.dumps(all_marked_ids))
        default_log.warn(js_code)

        self._show_and_listen(js_code, "全库同步检查")

    # --- 通用 UI 与 监听逻辑 ---
    def _show_and_listen(self, code, title):
        self.show_copy_dialog(code, title)
        # 开启剪贴板监听
        self.clipboard.dataChanged.connect(self.on_clipboard_changed)
        self.gui.status_bar.show_message("脚本已复制，等待 Zotero 回传结果...", 10000)

    def on_clipboard_changed(self):
        text = self.clipboard.text()
        if '"source":"Link To Zotero"' in text:
            try:
                # 必须断开连接，否则 clear() 又会触发一次
                self.clipboard.dataChanged.disconnect(self.on_clipboard_changed)
                data = json.loads(text)
                self._apply_sync_results(data)
                self.clipboard.clear()
            except Exception as e:
                default_log.error(f"解析回传失败: {e}")

    def _apply_sync_results(self, data):
        db = self.gui.current_db.new_api
        updates = {}

        # 标记成功的
        for bid in data.get("succeed_book_ids", []):
            updates[int(bid)] = True

        # 取消标记 (Zotero 侧已删)
        deleted_ids = data.get("deleted_in_zotero_ids", [])
        if deleted_ids:
            items_html = "".join(
                [
                    f"<li>{i + 1}. {db.get_metadata(book_id).title}</li>"
                    for i, book_id in enumerate(deleted_ids[:5])
                ]
            )
            if len(deleted_ids) > 5:
                items_html += f"<li>... 以及另外 {len(deleted_ids) - 5} 本</li>"

            if question_dialog(
                self.gui,
                "同步更新",
                f"<b>检测到 Zotero 端删除了 {len(deleted_ids)} 本书：</b><br><ul>{items_html}</ul><br>是否同步取消 Calibre 端的标记？",
            ):
                for bid in deleted_ids:
                    updates[int(bid)] = None
        if updates:
            # self._ensure_custom_column(db)
            db.set_field("#in_zotero", updates)
            self.gui.library_view.model().refresh_ids(list(updates.keys()))
            info_dialog(self.gui, "完成", "同步状态已更新", show=True)

    def _ensure_custom_column(self, db):
        if "#in_zotero" not in db.field_metadata.custom_field_keys():
            db.create_custom_column(
                label="in_zotero", name="In Zotero", datatype="bool"
            )

    def show_copy_dialog(self, code, title):
        # 此处保留你原有的 QDialog 代码，只需确保点击按钮时 clipboard.setText(code) 即可
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
