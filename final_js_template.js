let results = ['🚀 Link2Zotero 开始批量导入...', '--------------------------'];
let succeed_book_ids = [];
let failed_book_ids = [];
let deleted_in_zotero_ids = []; // Calibre 还在但 Zotero 删了的
let removed_from_zotero_count = 0;

// 1. 获取 Calibre 传过来的全量已标记 ID 列表
let calibreMarkedIds = __CALIBRE_MARKED_IDS__;

__ALL_BOOKS_JS__;

let allItemIDs = await Zotero.Items.getAll(Zotero.Libraries.userLibraryID, false, false, true);
// 提取当前 Zotero 中存在的 Calibre ID 映射
let zoteroCidMap = new Map();
for (let id of allItemIDs) {
  let item = Zotero.Items.get(id);

  // 排除附件、笔记和已被删除的条目
  if (!item.isRegularItem() || item.isAttachment() || item.isNote() || item.deleted) continue;

  // 获取 callNumber 字段
  let cn = item.getField('callNumber') || '';
  if (cn.includes('calibre id: ')) {
    // 提取 ID 数字
    let cidStr = cn.split('calibre id: ')[1];
    if (cidStr) {
      let cid = parseInt(cidStr);
      zoteroCidMap.set(cid, item);
    }
  }
}

// 场景 A: Calibre 中删了某本书 -> Zotero 执行物理删除
// 如果 Zotero 里的 ID 不在 Calibre 传过来的全量标记列表中，说明 Calibre 侧已删
let idsToTrash = [];
for (let [cid, item] of zoteroCidMap) {
  // 排除掉刚刚成功导入/更新的书，防止误删
  if (!calibreMarkedIds.includes(cid) && !succeed_book_ids.includes(cid)) {
    let title = item.getField('title');
    // 将条目移至回收站
    idsToTrash.push(item.id); // 收集需要删除的 ID
    removed_from_zotero_count++;
    results.push(`🗑️ Calibre 侧已删：Zotero 条目 "${title}" 已移至回收站`);
  }
}
// 执行批量删除（移至回收站）
if (idsToTrash.length > 0) {
  try {
    // 使用 Zotero 核心事务处理
    await Zotero.DB.executeTransaction(async () => {
      // 直接传入 ID 数组，这是最稳健的 API 调用方式
      await Zotero.Items.trash(idsToTrash);
    });
    results.push(`✅ 成功将 ${idsToTrash.length} 个无效条目移至回收站`);
  } catch (err) {
    // 如果 trash 依然有问题，尝试最后一种强制删除方式
    results.push(`⚠️ 事务删除失败，尝试强制删除: ${err.toString()}`);
    for (let id of idsToTrash) {
      await Zotero.DB.queryAsync('UPDATE items SET clientDateModified = CURRENT_TIMESTAMP WHERE itemID = ?', [id]);
      await Zotero.Items.erase(id); // 物理删除
    }
  }
}

// 场景 B: Zotero 中删了某本书 -> Calibre 取消勾选
for (let cid of calibreMarkedIds) {
  // 如果 Calibre 认为在，但 Zotero 映射表里没有，说明 Zotero 侧删了
  if (!zoteroCidMap.has(cid) && !succeed_book_ids.includes(cid)) {
    deleted_in_zotero_ids.push(cid);
    results.push(`⚠️ Zotero 侧已删：ID ${cid} 将在 Calibre 中取消勾选`);
  }
}

let feedback = {
  source: 'Link To Zotero',
  succeed_book_ids: succeed_book_ids,
  failed_book_ids: failed_book_ids,
  deleted_in_zotero_ids: deleted_in_zotero_ids,
};

Zotero.Utilities.Internal.copyTextToClipboard(JSON.stringify(feedback));

results.push('--------------------------');
results.push('✅️ 处理完成！总计: __LEN_ROWS__ 本');
results.push('✅️ 数据已写入剪贴板，请回到 Calibre 查看');
return results.join('\n');
