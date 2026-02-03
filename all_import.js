let results = ['🚀 Link To Zotero 开始导入...', '--------------------------'];
let succeed_book_uuids = [];
let skipped_book_uuids = [];
let failed_book_uuids = [];
const mimeTypes = {
  // Kindle/Amazon 格式
  '.azw': 'application/vnd.amazon.ebook', // Kindle 7 及之前版本
  '.azw3': 'application/vnd.amazon.mobi8-ebook', // KF8 格式，Kindle 8+ 支持
  '.kfx': 'application/vnd.amazon.ebook', // Kindle Format X，最新格式
  // 通用电子书格式
  '.mobi': 'application/x-mobipocket-ebook',
  '.epub': 'application/epub+zip',
  '.pdf': 'application/pdf',
  // 文档格式
  '.pdf': 'application/pdf',
  '.txt': 'text/plain',
  '.rtf': 'application/rtf',
  '.doc': 'application/msword',
  '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  // 其他电子书格式
  '.fb2': 'text/xml', // 或 'application/x-fictionbook+xml'
  '.cbr': 'application/x-cbr',
  '.cbz': 'application/x-cbz',
};

// --- 查重处理 ---
let existing_uuids = new Set();
let allItemIDs = await Zotero.Items.getAll(Zotero.Libraries.userLibraryID, false, false, true);
for (let id of allItemIDs) {
  let item = Zotero.Items.get(id);
  // 仅检查常规条目
  if (!item.isRegularItem() || item.isAttachment() || item.isNote() || item.deleted) continue;

  let cn = item.getField('callNumber') || '';
  if (cn.includes('calibre uuid: ')) {
    let uuid = cn.split('calibre uuid: ')[1]; // 此处不可以 parseInt
    existing_uuids.add(uuid);
  }
}

// Python 填充每本书的片段
__ALL_BOOKS_JS__;

let feedback = {
  source: 'Link To Zotero',
  action: 'import',
  succeed_book_uuids: [...succeed_book_uuids, ...skipped_book_uuids],
  failed_book_uuids: failed_book_uuids,
};
Zotero.Utilities.Internal.copyTextToClipboard(JSON.stringify(feedback));

results.push('--------------------------');
results.push(
  `✅ 处理完成，成功：${succeed_book_uuids.length}，跳过：${skipped_book_uuids.length}，失败：${failed_book_uuids.length}。`,
);
return results.join('\n');
