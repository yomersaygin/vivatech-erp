import frappe
from frappe import _


def _serial_meta_fields():
    meta = frappe.get_meta("Serial No")
    available = {df.fieldname for df in meta.fields}
    preferred = ["name","item_code","warehouse","status","purchase_document_type",
                 "purchase_document_no","delivery_document_type","delivery_document_no","batch_no"]
    return [f for f in preferred if f == "name" or f in available]


@frappe.whitelist()
def get_serial_summary(serial_no: str):
    if not frappe.db.exists("Serial No", serial_no):
        frappe.throw(_("IMEI / Seri No bulunamadı."))
    doc = frappe.get_doc("Serial No", serial_no)
    data = {field: getattr(doc, field, None) for field in _serial_meta_fields()}
    data["name"] = doc.name
    data["bundle_rows"] = get_serial_bundle_history(serial_no, 100)
    return data


@frappe.whitelist()
def list_serials(item_code=None, warehouse=None, status=None, limit=200):
    filters = {}
    if item_code: filters["item_code"] = item_code
    if warehouse: filters["warehouse"] = warehouse
    if status: filters["status"] = status
    return frappe.get_all("Serial No", filters=filters, fields=_serial_meta_fields(),
        order_by="modified desc", limit_page_length=min(max(int(limit or 200),1),500))


@frappe.whitelist()
def serial_tracking_enabled(item_code: str):
    if not frappe.db.exists("Item", item_code):
        frappe.throw(_("Ürün bulunamadı."))
    return bool(frappe.db.get_value("Item", item_code, "has_serial_no"))


@frappe.whitelist()
def get_serial_bundle_history(serial_no: str, limit=100):
    if not frappe.db.exists("Serial No", serial_no):
        frappe.throw(_("IMEI / Seri No bulunamadı."))
    if not frappe.db.exists("DocType", "Serial and Batch Entry"):
        return []
    return frappe.db.sql(
        """
        select e.parent as bundle, e.serial_no, e.warehouse, e.qty,
               b.voucher_type, b.voucher_no, b.posting_date, b.posting_time, b.docstatus
        from `tabSerial and Batch Entry` e
        inner join `tabSerial and Batch Bundle` b on b.name=e.parent
        where e.serial_no=%s
        order by b.posting_date desc, b.posting_time desc
        limit %s
        """, (serial_no, min(max(int(limit or 100),1),500)), as_dict=True)


@frappe.whitelist()
def get_serial_stock_ledger(serial_no: str, limit=100):
    """Compatibility fallback/audit trail through ERPNext Stock Ledger Entry."""
    if not frappe.db.exists("Serial No", serial_no):
        frappe.throw(_("IMEI / Seri No bulunamadı."))
    return frappe.get_all(
        "Stock Ledger Entry",
        filters={"is_cancelled": 0},
        fields=["name","posting_date","posting_time","voucher_type","voucher_no",
                "item_code","warehouse","actual_qty"],
        order_by="posting_date desc, posting_time desc",
        limit_page_length=min(max(int(limit or 100),1),500),
    )
