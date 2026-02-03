if (existing_uuids.has(__BOOK_UUID__)) {
  results.push(`⏭️ [跳过] 【__TITLE__】已存在于 Zotero 中（如果有元数据更新，请在 Zotero 中手动删除，然后重新导入）`);
  skipped_book_uuids.push(__BOOK_UUID__); // 依然标记为成功，以便 Calibre 端更新 In Zotero 状态
} else {
  try {
    let item = new Zotero.Item('book');
    item.setField('title', __TITLE__);
    item.setCreators(__AUTHORS__);
    item.setField('date', __PUBLISHED__);
    item.setField('publisher', __PUBLISHER__);
    item.setField('language', __LANGUAGE__);
    item.setField('ISBN', __IDENTIFIERS__);
    item.setField('abstractNote', __ABSTRACT_TEXT__);
    item.setField('callNumber', 'calibre uuid: ' + __BOOK_UUID__);
    let itemID = await item.saveTx();

    const ext = __FILE_PATH__.substring(__FILE_PATH__.lastIndexOf('.')).toLowerCase();
    const mimeType = mimeTypes[ext] || 'application/octet-stream';

    await Zotero.Attachments.linkFromFile({
      file: __FILE_PATH__,
      parentItemID: itemID,
      contentType: mimeType,
    });

    // 1. 待修改的item
    let idsToUpdate = [itemID];

    // 2. 获取并包含所有附件的 ID (确保附件时间也被修正)
    let itemObj = Zotero.Items.get(itemID);
    let attachments = itemObj.getAttachments();
    if (attachments.length > 0) {
      idsToUpdate.push(...attachments);
    }
    // 3. 批量更新数据库
    for (let id of idsToUpdate) {
      await Zotero.DB.queryAsync('UPDATE items SET dateAdded = ?, dateModified = ? WHERE itemID = ?', [
        __TIMESTAMP__,
        __TIMESTAMP__,
        id,
      ]);
    }
    // 4. 核心：通知 UI 刷新，这样你就不用等下一本书导入了
    Zotero.Notifier.trigger('modify', 'item', idsToUpdate);
    results.push(`✅ ${new Date().toLocaleTimeString()} 【__TITLE__】 calibre id: __BOOK_ID__ 已导入并链接`);
    succeed_book_uuids.push(__BOOK_UUID__);
  } catch (e) {
    failed_book_uuids.push(__BOOK_UUID__);
    results.push(`❌ __TITLE__：${e.toString()}`);
  }
}
