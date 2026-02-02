try {
  let item = new Zotero.Item('book');
  item.setField('title', __TITLE__);
  item.setCreators(__AUTHORS__);
  item.setField('date', __PUBLISHED__);
  item.setField('publisher', __PUBLISHER__);
  item.setField('language', __LANGUAGE__);
  item.setField('ISBN', __IDENTIFIERS__);
  item.setField('abstractNote', __ABSTRACT_TEXT__);
  item.setField('callNumber', 'calibre id: ' + __BOOK_ID__);
  let itemID = await item.saveTx();

  await Zotero.Attachments.linkFromFile({
    file: __FILE_PATH__,
    parentItemID: itemID,
    contentType: 'application/pdf',
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
  results.push(`✅ ${new Date().toLocaleTimeString()} __TITLE__ itemID:${itemID} 已导入并链接`);
  succeed_book_ids.push(__BOOK_ID__);
} catch (e) {
  failed_book_ids.push(__BOOK_ID__);
  results.push(`❌ __TITLE__：${e.toString()}`);
}
