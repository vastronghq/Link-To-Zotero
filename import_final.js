let results = ['🚀 Link2Zotero 开始同步...', '--------------------------'];
let succeed_book_ids = [];
let failed_book_ids = [];

// Python 填充每本书的片段
__ALL_BOOKS_JS__;

let feedback = {
  source: 'Link To Zotero',
  action: 'import',
  succeed_book_ids: succeed_book_ids,
  failed_book_ids: failed_book_ids,
};
Zotero.Utilities.Internal.copyTextToClipboard(JSON.stringify(feedback));

results.push('--------------------------');
results.push(`✅ 处理完成：__LEN_ROWS__ 本`);
return results.join('\n');
