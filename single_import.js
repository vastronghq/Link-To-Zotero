// 包裹在大括号中，防止SyntaxError: redeclaration of let
{
  let item;
  let itemID;
  let isUpdate = false;
  // 1. 初始判定
  if (existing_uuid_items.has(__BOOK_UUID__)) {
    item = existing_uuid_items.get(__BOOK_UUID__);
    isUpdate = true;

    // 如果是更新模式，先删除旧的 PDF 附件，否则附件会越来越多
    let oldAttachments = item.getAttachments();
    let idsToTrash = [];
    for (let attID of oldAttachments) {
      let att = Zotero.Items.get(attID);
      // 只要附件不是笔记，就标记删除
      if (att.isAttachment() && !att.isNote()) {
        idsToTrash.push(attID);
      }
    }
    if (idsToTrash.length > 0) {
      // 将旧附件移至回收站
      await Zotero.DB.executeTransaction(async () => {
        await Zotero.Items.trash(idsToTrash);
      });
    }
  } else {
    item = new Zotero.Item('book');
    isUpdate = false;
  }

  // 2. 设置元数据
  try {
    item.setField('title', __TITLE__);
    item.setCreators(__AUTHORS__);
    item.setField('date', __PUBLISHED__);
    item.setField('publisher', __PUBLISHER__);
    item.setField('language', __LANGUAGE__);
    item.setField('ISBN', __IDENTIFIERS__);
    item.setField('abstractNote', __ABSTRACT_TEXT__);
    item.setField('callNumber', 'calibre uuid: ' + __BOOK_UUID__);

    // 执行保存 (如果没变，saveTx 会返回 false，但没关系)
    await item.saveTx();
    itemID = item.id;

    // 链接附件
    const ext = __FILE_PATH__.substring(__FILE_PATH__.lastIndexOf('.')).toLowerCase();
    const mimeType = mimeTypes[ext] || 'application/octet-stream';
    await Zotero.Attachments.linkFromFile({
      file: __FILE_PATH__,
      parentItemID: itemID,
      contentType: mimeType,
    });

    // 记录附件对应的 storage 目录（条目也有 Key，但是我发现实际上没有对应目录生成）
    // 每次添加附件，其对应的 storage 目录都会变化
    // 可以随意删除附件的 storage 目录，标注是存在数据库里，不会消失，可能阅读进度会消失
    let attachments = item.getAttachments();
    if (attachments.length > 0) {
      let mainAtt = Zotero.Items.get(attachments[0]);
      let attKey = mainAtt.key; // 获取附件的 Key
      item.setField('extra', attKey);
      await item.saveTx({ skipNotifier: true });
    }
    // 5. 更新时间戳 (主条目及新链接的附件)
    let idsToUpdateTimestamp = [itemID];
    // 获取并包含所有附件的 ID (确保附件时间也被修正)
    if (attachments.length > 0) {
      idsToUpdateTimestamp.push(...attachments);
    }
    for (let id of idsToUpdateTimestamp) {
      await Zotero.DB.queryAsync('UPDATE items SET dateAdded = ?, dateModified = ? WHERE itemID = ?', [
        __TIMESTAMP__,
        __TIMESTAMP__,
        id,
      ]);
    }
    // 通知 UI 刷新，这样你就不用等下一本书导入了
    Zotero.Notifier.trigger('modify', 'item', idsToUpdateTimestamp);
    if (isUpdate) {
      updated_book_uuids.push(__BOOK_UUID__);
      results.push(`🔄 ${new Date().toLocaleTimeString()} [更新] 【__TITLE__】 (calibre id: __BOOK_ID__) 元数据已更新`);
    } else {
      added_book_uuids.push(__BOOK_UUID__);
      results.push(`✅ ${new Date().toLocaleTimeString()} [新增] 【__TITLE__】 (calibre id: __BOOK_ID__) 已导入并链接`);
    }
  } catch (e) {
    failed_book_uuids.push(__BOOK_UUID__);
    results.push(
      `❌ ${new Date().toLocaleTimeString()} [失败] 【__TITLE__】 (calibre id: __BOOK_ID__) 导入失败：${e.toString()}`,
    );
  }
}
