let results = ['🚀 Link2Zotero 开始批量导入...', '--------------------------'];
let succeed_ids = [];

__ALL_BOOKS_JS__;

let sync_status = {
  source: 'Link To Zotero',
  itemIDs: succeed_ids,
};

Zotero.Utilities.Internal.copyTextToClipboard(JSON.stringify(sync_status));

results.push('--------------------------');
results.push('✅️ 处理完成！总计: __LEN_ROWS__ 本');
results.push('✅️ 数据已写入剪贴板，请回到 Calibre 查看');
return results.join('\n');
