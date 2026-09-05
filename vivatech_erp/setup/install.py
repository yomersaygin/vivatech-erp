import json
import frappe

WORKSPACE_NAME = "Vivatech ERP"

SHORTCUTS = [
    ("Ana Sayfa", "Page", "vivatech-ana-sayfa"),
    ("Cari Kartları", "Page", "cari-karti"),
    ("Tedarikçiler", "DocType", "Supplier"),
    ("Cari Hareketleri", "Report", "General Ledger"),
    ("Finans", "Page", "finans-merkezi"),
    ("Raporlar", "Page", "raporlar-merkezi"),
    ("Kullanıcılar / Yetkiler", "Page", "kullanicilar-yetkiler"),
    ("Ayarlar", "Page", "ayarlar-merkezi"),
    ("Ürünler", "Page", "urun-karti"),
    ("Stok / Depo", "Page", "stok-depo"),
    ("IMEI / Seri No", "Page", "imei-seri"),
    ("Alış", "Page", "alis-merkezi"),
    ("Satış", "Page", "satis-merkezi"),
]

def _content():
    blocks = [
        {"id": "vivatech-title", "type": "header", "data": {"text": "Vivatech ERP", "col": 12}},
        {"id": "cari-head", "type": "header", "data": {"text": "Cari", "col": 12}},
        {"id": "cari-card", "type": "shortcut", "data": {"shortcut_name": "Cari Kartları", "col": 3}},
        {"id": "supplier-card", "type": "shortcut", "data": {"shortcut_name": "Tedarikçiler", "col": 3}},
        {"id": "cari-ledger", "type": "shortcut", "data": {"shortcut_name": "Cari Hareketleri", "col": 3}},
        {"id": "cari-payment", "type": "shortcut", "data": {"shortcut_name": "Finans", "col": 3}},
        {"id": "core-head", "type": "header", "data": {"text": "Operasyon", "col": 12}},
        {"id": "products", "type": "shortcut", "data": {"shortcut_name": "Ürünler", "col": 3}},
        {"id": "warehouses", "type": "shortcut", "data": {"shortcut_name": "Stok / Depo", "col": 3}},
        {"id": "sales", "type": "shortcut", "data": {"shortcut_name": "Satış", "col": 3}},
        {"id": "purchase", "type": "shortcut", "data": {"shortcut_name": "Alış", "col": 3}},
    ]
    return json.dumps(blocks, ensure_ascii=False)

def after_install():
    create_workspace()

def create_workspace():
    if frappe.db.exists("Workspace", WORKSPACE_NAME):
        ws = frappe.get_doc("Workspace", WORKSPACE_NAME)
    else:
        ws = frappe.new_doc("Workspace")
        ws.title = WORKSPACE_NAME
        ws.label = WORKSPACE_NAME

    ws.module = "Vivatech ERP"
    ws.public = 1
    ws.is_hidden = 0
    ws.content = _content()

    ws.set("shortcuts", [])
    for label, kind, target in SHORTCUTS:
        row = {
            "label": label,
            "type": kind,
            "link_to": target,
        }
        if kind == "DocType":
            row["doc_view"] = "List"
        ws.append("shortcuts", row)

    ws.save(ignore_permissions=True)
    frappe.db.commit()
    return ws.name
