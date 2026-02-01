import requests


def sync_to_zotero_auto(self, book_id):
    db = self.gui.current_db.new_api
    meta = db.get_metadata(book_id)
    pdf_path = db.format_abspath(book_id, "PDF")

    url = "http://127.0.0.1:23119/connector/saveItems"
    payload = {
        "items": [
            {
                "itemType": "book",
                "title": meta.title,
                "creators": [
                    {"firstName": "", "lastName": a, "creatorType": "author"}
                    for a in meta.authors
                ],
                "date": meta.pubdate.strftime("%Y") if meta.pubdate else "",
                "attachments": [
                    {
                        "path": pdf_path,
                        "title": meta.title + ".pdf",
                        "contentType": "application/pdf",
                    }
                ]
                if pdf_path
                else [],
            }
        ]
    }

    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            # 导入成功，立刻在 Calibre 里做标记
            db.set_field("#zotero_synced", {book_id: True})
            self.gui.library_view.model().refresh_ids([book_id])
            return True
        else:
            print(f"同步失败: {res.text}")
            return False
    except Exception as e:
        print(f"连接失败: {e}")
        return False
