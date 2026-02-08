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
        "images/icon_6.png",
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
        icon_interface = get_icons("images/icon_6.png", "icon_main")
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
            if question_dialog(
                self.gui,
                "初始化确认",
                '插件需要创建一个自定义列 "#in_zotero" 用于记录同步状态。<br><br>'
                "是否现在创建？(创建后需要重启 Calibre)",
                yes_text="立即创建",
                no_text="稍后再说",
            ):
                # 创建自定义列
                try:
                    db.create_custom_column(
                        label="in_zotero",
                        name="In Zotero",
                        datatype="bool",
                        is_multiple=False,
                        display={},
                    )
                    info_dialog(
                        self.gui,
                        "初始化成功",
                        '已为您创建 "#in_zotero" 自定义列<br><br>'
                        "请重启 Calibre 以激活该列。",
                        show=True,
                    )
                except Exception as e:
                    error_dialog(
                        self.gui,
                        "初始化失败",
                        f"创建自定义列失败：{e}",
                        show=True,
                    )
                # 只要进到这个 if 分支，说明当前环境肯定没准备好（要么没创建，要么刚创建完还没重启）
                return False
            else:
                return False
        return True

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

    def uuid_id_map(self):
        db = self.gui.current_db.new_api
        all_book_ids = db.all_book_ids()
        uuid_id = {}
        for book_id in all_book_ids:
            uuid = db.get_metadata(book_id).uuid
            uuid_id[uuid] = book_id
        return uuid_id

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
        for i, row in enumerate(rows):
            book_id = self.gui.library_view.model().id(row.row())
            script_import = self._build_single_import_js(db, book_id, i + 1, len(rows))
            book_scripts.append(script_import)
        final_template = get_js_template(self, "all_import.js")
        js_code = final_template.replace("__ALL_BOOKS_JS__", "\n".join(book_scripts))

        self._show_and_listen(js_code, f"导入 {len(rows)} 本书籍")

    def _build_single_import_js(self, db, book_id, index, total):
        metadata = db.get_metadata(book_id)
        formats = db.formats(book_id)
        if len(formats) == 0:
            return f"results.push(`[跳过] {repr(metadata.title)} 无可用格式`);"
        if "PDF" in formats:
            file_path = db.format_abspath(book_id, "PDF")
        else:
            file_path = db.format_abspath(book_id, formats[0])

        title = metadata.title
        book_uuid = metadata.uuid
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
        collection = db.field_for("#collection", book_id)

        tpl = get_js_template(self, "single_import.js")
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
        tpl = tpl.replace("__BOOK_UUID__", repr(book_uuid))
        tpl = tpl.replace("__INDEX__", repr(index))
        tpl = tpl.replace("__TOTAL__", repr(total))
        tpl = tpl.replace("__COLLECTION__", json.dumps(collection))
        return tpl

    # --- 核心逻辑 B：检查脚本生成 ---
    def generate_check_script(self):
        db = self.gui.current_db.new_api
        marked_ids = list(db.search("#in_zotero:true"))
        marked_uuids = [db.get_metadata(book_id).uuid for book_id in marked_ids]

        tpl = get_js_template(self, "sync_check.js")
        js_code = tpl.replace("__CALIBRE_MARKED_UUIDS__", json.dumps(marked_uuids))

        self._show_and_listen(js_code, "双向同步检查")

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

    def _apply_sync_results(self, response_data):
        uuid_id = self.uuid_id_map()
        db = self.gui.current_db.new_api
        updates = {}
        default_log.warn(response_data)

        # 标记成功的
        for uuid in response_data.get("succeed_book_uuids", []):
            updates[int(uuid_id[uuid])] = True

        # 取消标记 (Zotero 侧已删)
        deleted_uuids = response_data.get("uuids_deleted_in_zotero", [])
        if deleted_uuids:
            items_html = "".join(
                [
                    f"<li>{db.get_metadata(uuid_id[uuid]).title}</li>"
                    for i, uuid in enumerate(deleted_uuids[:5])
                ]
            )
            if len(deleted_uuids) > 5:
                items_html += f"<li>... 以及另外 {len(deleted_uuids) - 5} 本</li>"

            if question_dialog(
                self.gui,
                "同步更新",
                f"<b>检测到 Zotero 端删除了 {len(deleted_uuids)} 本书：</b><br><ul>{items_html}</ul><br>是否同步取消 Calibre 端的标记？",
            ):
                for uuid in deleted_uuids:
                    updates[int(uuid_id[uuid])] = None
        if updates:
            db.set_field("#in_zotero", updates)
            self.gui.library_view.model().refresh_ids(list(updates.keys()))
            info_dialog(self.gui, "完成", "同步状态已更新", show=True)

    def show_copy_dialog(self, code, title):
        # 此处保留你原有的 QDialog 代码，只需确保点击按钮时 clipboard.setText(code) 即可
        d = QDialog(self.gui)
        d.setWindowTitle(f"Link To Zotero - {title}")
        layout = QVBoxLayout()
        d.setLayout(layout)

        layout.addWidget(
            QLabel(
                "<b>使用说明：</b><br>"
                "1. 复制下方脚本；<br>"
                "2. 前往 Zotero 菜单：<b>工具 > 开发者 > Run JavaScript</b>；<br>"
                "3. 在窗口中粘贴并点击<b>执行</b>。"
            )
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
