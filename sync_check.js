/*
 * Copyright (c) 2026 by hqwang, All Rights Reserved.
 *
 * @Software     : VScode
 * @Author       : hqwang
 * @Date         : 2026-02-02 22:49:27
 * @LastEditTime : 2026-02-06 11:56:08
 * @Description  :
 */
let results = ['🔍 Link To Zotero 开始双向同步检查...', '--------------------------'];
let uuids_deleted_in_zotero = [];
let calibre_marked_uuids = __CALIBRE_MARKED_UUIDS__; // 全量列表

// 1. 获取 Zotero 映射
let allItemIDs = await Zotero.Items.getAll(Zotero.Libraries.userLibraryID, false, false, true);
let zotero_uuid_map = new Map();
for (let id of allItemIDs) {
  let item = Zotero.Items.get(id);
  // 排除附件、笔记和已被删除的条目
  if (!item.isRegularItem() || item.isAttachment() || item.isNote() || item.deleted) continue;
  let cn = item.getField('callNumber') || '';
  if (cn.includes('calibre uuid: ')) {
    let uuid = cn.split('calibre uuid: ')[1];
    zotero_uuid_map.set(uuid, item);
  }
}

// 2. 场景 A: Calibre 中删了某本书 -> Zotero 执行物理删除
let zotero_ids_to_trash = [];
for (let [uuid, item] of zotero_uuid_map) {
  if (!calibre_marked_uuids.includes(uuid)) {
    zotero_ids_to_trash.push(item.id);
    results.push(
      `🗑️ ${new Date().toLocaleTimeString()} 【${item.getField('title')}】 Calibre 端标记取消或无此条目，Zotero 端已同步删除`,
    );
  }
}

if (zotero_ids_to_trash.length > 0) {
  await Zotero.DB.executeTransaction(async () => {
    await Zotero.Items.trash(zotero_ids_to_trash);
  });
  results.push(`✅ 处理完成，已将 ${zotero_ids_to_trash.length} 个无效条目移至回收站`);
}

// 3. 场景 B：Zotero 侧删了 -> 告知 Calibre 取消勾选
for (let uuid of calibre_marked_uuids) {
  if (!zotero_uuid_map.has(uuid)) {
    uuids_deleted_in_zotero.push(uuid);
    results.push(
      `⚠️ ${new Date().toLocaleTimeString()} calibre uuid ${uuid} 此条目在 Zotero 端不存在，将在 Calibre 端取消标记`,
    );
  }
}

let feedback = {
  source: 'Link To Zotero',
  action: 'check',
  uuids_deleted_in_zotero: uuids_deleted_in_zotero,
};
Zotero.Utilities.Internal.copyTextToClipboard(JSON.stringify(feedback));

results.push('--------------------------');

if (zotero_ids_to_trash.length === 0 && uuids_deleted_in_zotero.length === 0) {
  results.push(`✅ 检查完毕，所有记录状态一致，无需进一步操作。`);
} else {
  results.push(`✅ 检查完毕，请回到 Calibre 更新同步状态。`);
}
return results.join('\n');
