let results = ['🚀 Link2Zotero 开始批量导入...', '--------------------------'];
let succeed_book_ids = [];
let failed_book_ids = [];

__ALL_BOOKS_JS__;

let feedback = {
  source: 'Link To Zotero',
  succeed_book_ids: succeed_book_ids,
  failed_book_ids: failed_book_ids,
};

Zotero.Utilities.Internal.copyTextToClipboard(JSON.stringify(feedback));

results.push('--------------------------');
results.push('✅️ 处理完成！总计: __LEN_ROWS__ 本');
results.push('✅️ 数据已写入剪贴板，请回到 Calibre 查看');
return results.join('\n');
