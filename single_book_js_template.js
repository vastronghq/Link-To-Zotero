try {
  let item = new Zotero.Item('book');
  item.setField('title', __TITLE__);
  item.setCreators(__AUTHORS__);
  item.setField('date', __PUBLISHED__);
  item.setField('publisher', __PUBLISHER__);
  item.setField('language', __LANGUAGE__);
  item.setField('ISBN', __IDENTIFIERS__);
  item.setField('abstractNote', __ABSTRACT_TEXT__);
  let itemID = await item.saveTx();

  await Zotero.Attachments.linkFromFile({
    file: __FILE_PATH__,
    parentItemID: itemID,
    contentType: 'application/pdf',
  });
  results.push(`[成功] ${new Date().toLocaleTimeString()}：__TITLE__ 已链接`);
} catch (e) {
  results.push(`[失败] __TITLE__：${e.toString()}`);
}
