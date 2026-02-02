let results = ['🚀 Link To Zotero 开始导入...', '--------------------------'];
let succeed_book_ids = [];
let failed_book_ids = [];

// --- 查重处理 ---
let existingCids = new Set();
let allItemIDs = await Zotero.Items.getAll(Zotero.Libraries.userLibraryID, false, false, true);
for (let id of allItemIDs) {
  let item = Zotero.Items.get(id);
  // 仅检查常规条目
  if (!item.isRegularItem() || item.isAttachment() || item.isNote() || item.deleted) continue;

  let cn = item.getField('callNumber') || '';
  if (cn.includes('calibre id: ')) {
    let cid = cn.split('calibre id: ')[1]; // 此处不可以 parseInt
    existingCids.add(cid);
  }
}

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
