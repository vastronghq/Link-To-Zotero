"""
Copyright (c) 2026 by hqwang, All Rights Reserved.

Software     : VScode
Author       : hqwang
Date         : 2026-01-31 13:10:09
LastEditTime : 2026-02-01 03:09:49
Description  :
"""

from calibre.customize import InterfaceActionBase


class CalibrePluginTemplateBase(InterfaceActionBase):
    """
    插件的基础类，负责定义插件的元数据信息。
    """

    # 插件在插件列表中显示的名称
    name = "Link2Zotero"
    # 插件的功能描述
    description = "A Calibre plugin to link books to Zotero entries."
    # 支持的平台
    supported_platforms = ["windows", "osx", "linux"]
    # 作者
    author = "hqwang"
    # 版本号 (主版本, 次版本, 修订号)
    version = (1, 0, 0)
    # 要求的最低 Calibre 版本 (5.0.0 开始支持 Python 3)
    minimum_calibre_version = (5, 0, 0)

    # 【关键】连接 UI 逻辑。格式：calibre_plugins.命名空间.模块名:类名
    # 这里的 'Link2Zotero' 必须与 .txt 文件中的别名一致
    actual_plugin = "calibre_plugins.Link2Zotero.main:Link2ZoteroAction"

    def is_customizable(self):
        """是否允许用户在插件设置中进行配置"""
        return False
