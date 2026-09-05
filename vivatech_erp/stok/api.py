import frappe
from frappe import _

@frappe.whitelist()
def get_warehouse_summary(warehouse: str):
    wh = frappe.get_doc("Warehouse", warehouse)
    bins = frappe.get_all(
        "Bin",
        filters={"warehouse": warehouse},
        fields=["item_code","actual_qty","reserved_qty","ordered_qty","projected_qty"],
        order_by="item_code asc",
        limit_page_length=500,
    )
    return {
        "warehouse": wh.name,
        "warehouse_name": wh.warehouse_name,
        "company": wh.company,
        "is_group": bool(wh.is_group),
        "disabled": bool(wh.disabled),
        "total_qty": sum((r.actual_qty or 0) for r in bins),
        "item_count": sum(1 for r in bins if (r.actual_qty or 0) != 0),
        "items": bins,
    }

@frappe.whitelist()
def get_stock_movements(warehouse: str | None = None, item_code: str | None = None, limit: int = 100):
    filters = {}
    if warehouse:
        filters["warehouse"] = warehouse
    if item_code:
        filters["item_code"] = item_code
    return frappe.get_all(
        "Stock Ledger Entry",
        filters=filters,
        fields=["posting_date","posting_time","item_code","warehouse","actual_qty",
                "qty_after_transaction","voucher_type","voucher_no","batch_no","serial_no"],
        order_by="posting_date desc, posting_time desc, creation desc",
        limit_page_length=min(max(int(limit or 100),1),500),
    )

@frappe.whitelist()
def make_stock_entry(entry_type: str, source_warehouse: str | None = None, target_warehouse: str | None = None):
    if entry_type not in {"Material Receipt","Material Issue","Material Transfer"}:
        frappe.throw(_("Geçersiz stok işlem türü."))
    doc = frappe.new_doc("Stock Entry")
    doc.stock_entry_type = entry_type
    if source_warehouse:
        doc.from_warehouse = source_warehouse
    if target_warehouse:
        doc.to_warehouse = target_warehouse
    return doc.as_dict()
