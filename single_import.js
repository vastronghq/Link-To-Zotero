// 包裹在大括号中，防止SyntaxError: redeclaration of let
{
  let item;
  let itemID;
  let isUpdate;
  let title_log = __TITLE__.substring(0, 50);
  // 1. 初始判定
  if (existing_uuid_items.has(__BOOK_UUID__)) {
    item = existing_uuid_items.get(__BOOK_UUID__);
    isUpdate = true;
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

    // 执行保存
    await item.saveTx();
    itemID = item.id;

    // 链接附件
    if (!isUpdate) {
      const ext = __FILE_PATH__.substring(__FILE_PATH__.lastIndexOf('.')).toLowerCase();
      const mimeType = mimeTypes[ext] || 'application/octet-stream';
      await Zotero.Attachments.linkFromFile({
        file: __FILE_PATH__,
        parentItemID: itemID,
        contentType: mimeType,
      });
    } else {
      // 对于更新操作，原来的重链接方式会导致标注丢失，故该用修改链接路径的方式，一方面可以保留标注，另一方面可以应对Calire把PDF文件重命名了的情况
      // 只要还是同一份PDF，标注就能正确显示在PDF上，否则，标注会错位
      // 此外，saveTx()方法会根据Zotero中“链接文件根路径”的设置决定是存储绝对路径还是存储相对路径，无需担心
      let attachmentIDs = item.getAttachments();
      if (attachmentIDs.length > 0) {
        for (let attID of attachmentIDs) {
          let att = Zotero.Items.get(attID);
          // 确保它是我们要找的链接文件附件
          if (att.isAttachment() && !att.isNote()) {
            // 核心操作：直接修改附件的 path 字段
            att.attachmentPath = __FILE_PATH__;
            await att.saveTx();
          }
        }
      }
    }
    // 记录附件对应的 storage 目录（条目也有 Key，但是我发现实际上没有对应目录生成）
    // 可以随意删除附件的 storage 目录，标注是存在数据库里，不会消失，但是存储在.zotero-reader-state文件里的阅读进度会消失
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
      log.push(
        `🔄 [__INDEX__/__TOTAL__] ${new Date().toLocaleTimeString()} [更新] 【${title_log}...】 (calibre id: __BOOK_ID__) 元数据已更新`,
      );
      progressWin.addDescription(
        `🔄 [__INDEX__/__TOTAL__] ${new Date().toLocaleTimeString()} [更新] 【${title_log}...】 (calibre id: __BOOK_ID__) 元数据已更新`,
      );
    } else {
      new_book_uuids.push(__BOOK_UUID__);
      log.push(
        `✅ [__INDEX__/__TOTAL__] ${new Date().toLocaleTimeString()} [新增] 【${title_log}...】 (calibre id: __BOOK_ID__) 已导入并链接`,
      );
      progressWin.addDescription(
        `✅ [__INDEX__/__TOTAL__] ${new Date().toLocaleTimeString()} [新增] 【${title_log}...】 (calibre id: __BOOK_ID__) 已导入并链接`,
      );
    }
  } catch (e) {
    failed_book_uuids.push(__BOOK_UUID__);
    log.push(
      `❌ [__INDEX__/__TOTAL__] ${new Date().toLocaleTimeString()} [失败] 【${title_log}...】 (calibre id: __BOOK_ID__) 导入失败：${e.toString()}`,
    );
    progressWin.addDescription(
      `❌ [__INDEX__/__TOTAL__] ${new Date().toLocaleTimeString()} [失败] 【${title_log}...】 (calibre id: __BOOK_ID__) 导入失败：${e.toString()}`,
    );
  }

  if (true) {
    // 克隆分类
    if (__COLLECTION__) {
      for (let col of __COLLECTION__) {
        let parts = col.split('.');
        let libraryID = ZoteroPane.getSelectedLibraryID();
        let currentParentID = null;

        for (let segment of parts) {
          let existingCollections;

          // 1. 根据层级获取“同级”分类
          if (currentParentID === null) {
            // 顶级
            existingCollections = Zotero.Collections.getByLibrary(libraryID);
          } else {
            // 子级
            existingCollections = Zotero.Collections.getByParent(currentParentID);
          }

          // 2. 查找同名分类
          let target = existingCollections.find((c) => c.name === segment);

          if (target) {
            currentParentID = target.id;
          } else {
            // 3. 创建新分类
            let newCol = new Zotero.Collection();
            newCol.name = segment;

            if (currentParentID === null) {
              newCol.libraryID = libraryID;
            } else {
              newCol.parentID = currentParentID;
            }

            currentParentID = await newCol.saveTx();
          }
        }

        // 4. 把 item 加入最终分类
        if (!item.inCollection(currentParentID)) {
          item.addToCollection(currentParentID);
        }
      }

      // 5. 必须保存 item
      await item.saveTx();
    }
  }
}
