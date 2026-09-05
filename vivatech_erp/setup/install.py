import json
import frappe

WORKSPACE_NAME = "Vivatech ERP"

SHORTCUTS = [
    ("Ana Sayfa", "Page", "vivatech-ana-sayfa"),
    ("Cari Kartları", "Page", "cari-karti"),
    ("Müşteriler", "DocType", "Customer"),
    ("Tedarikçiler", "DocType", "Supplier"),
    ("Cari Hareketleri", "Report", "General Ledger"),
    ("Tahsilat / Ödeme", "DocType", "Payment Entry"),
    ("Finans", "Page", "finans-merkezi"),
    ("Raporlar", "Page", "raporlar-merkezi"),
    ("Kullanıcılar / Yetkiler", "Page", "kullanicilar-yetkiler"),
    ("Ayarlar", "Page", "ayarlar-merkezi"),
    ("Ürünler", "Page", "urun-karti"),
    ("Ürün Kartları", "DocType", "Item"),
    ("Stok / Depo", "Page", "stok-depo"),
    ("Depolar", "DocType", "Warehouse"),
    ("IMEI / Seri No", "Page", "imei-seri"),
    ("Seri Numaraları", "DocType", "Serial No"),
    ("Alış", "Page", "alis-merkezi"),
    ("Alış Faturaları", "DocType", "Purchase Invoice"),
    ("Satış", "Page", "satis-merkezi"),
    ("Satış Faturaları", "DocType", "Sales Invoice"),
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

    # Save Workspace first. During install-app, some Frappe/ERPNext images can
    # fail while resolving the Workspace Shortcut child controller. Writing the
    # child rows directly avoids that controller-load path and keeps install
    # deterministic.
    ws.save(ignore_permissions=True)
    _replace_shortcuts_directly(ws.name)
    frappe.db.commit()
    return ws.name


def _replace_shortcuts_directly(workspace_name):
    frappe.db.sql(
        "DELETE FROM `tabWorkspace Shortcut` "
        "WHERE parent=%s AND parenttype='Workspace' AND parentfield='shortcuts'",
        (workspace_name,),
    )

    for idx, (label, kind, target) in enumerate(SHORTCUTS, start=1):
        frappe.db.sql(
            """
            INSERT INTO `tabWorkspace Shortcut`
                (name, parent, parenttype, parentfield, idx, label, type, link_to, doc_view)
            VALUES (%s, %s, 'Workspace', 'shortcuts', %s, %s, %s, %s, %s)
            """,
            (
                frappe.generate_hash(length=10),
                workspace_name,
                idx,
                label,
                kind,
                target,
                "List" if kind == "DocType" else None,
            ),
        )
