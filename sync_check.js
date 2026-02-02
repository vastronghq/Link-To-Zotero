/*
 * Copyright (c) 2026 by hqwang, All Rights Reserved.
 *
 * @Software     : VScode
 * @Author       : hqwang
 * @Date         : 2026-02-02 22:49:27
 * @LastEditTime : 2026-02-03 01:43:42
 * @Description  :
 */
let results = ['🔍 Link To Zotero 开始双向同步检查...', '--------------------------'];
let deleted_in_zotero_ids = [];
let calibreMarkedIds = __CALIBRE_MARKED_IDS__; // 全量列表

// 1. 获取 Zotero 映射
let allItemIDs = await Zotero.Items.getAll(Zotero.Libraries.userLibraryID, false, false, true);
let zoteroCidMap = new Map();
for (let id of allItemIDs) {
  let item = Zotero.Items.get(id);
  // 排除附件、笔记和已被删除的条目
  if (!item.isRegularItem() || item.isAttachment() || item.isNote() || item.deleted) continue;
  let cn = item.getField('callNumber') || '';
  if (cn.includes('calibre id: ')) {
    let cid = parseInt(cn.split('calibre id: ')[1]);
    zoteroCidMap.set(cid, item);
  }
}

// 2. 场景 A: Calibre 中删了某本书 -> Zotero 执行物理删除
let idsToTrash = [];
for (let [cid, item] of zoteroCidMap) {
  if (!calibreMarkedIds.includes(cid)) {
    idsToTrash.push(item.id);
    results.push(`🗑️【${item.getField('title')}】：Calibre 端无此条目，Zotero 端已同步删除`);
  }
}

if (idsToTrash.length > 0) {
  await Zotero.DB.executeTransaction(async () => {
    await Zotero.Items.trash(idsToTrash);
  });
  results.push(`✅ 成功将 ${idsToTrash.length} 个无效条目移至回收站`);
}

// 3. 场景 B：Zotero 侧删了 -> 告知 Calibre 取消勾选
for (let cid of calibreMarkedIds) {
  if (!zoteroCidMap.has(cid)) {
    deleted_in_zotero_ids.push(cid);
    results.push(`⚠️ calibre id ${cid}： 此条目在 Zotero 端不存在，将在 Calibre 端取消勾选`);
  }
}

let feedback = {
  source: 'Link To Zotero',
  action: 'check',
  deleted_in_zotero_ids: deleted_in_zotero_ids,
};
Zotero.Utilities.Internal.copyTextToClipboard(JSON.stringify(feedback));

results.push('--------------------------');

if (idsToTrash.length === 0 && deleted_in_zotero_ids.length === 0) {
  results.push(`✅ 检查完毕，所有记录状态一致，无需进一步操作。`);
} else {
  results.push(`✅ 检查完毕，请回到 Calibre 处理回传数据。`);
}
return results.join('\n');
