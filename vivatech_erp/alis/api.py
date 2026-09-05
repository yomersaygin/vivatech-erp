import frappe
from frappe import _

@frappe.whitelist()
def get_purchase_summary(purchase_invoice: str):
    doc = frappe.get_doc("Purchase Invoice", purchase_invoice)

    items = []
    for row in doc.items:
        items.append({
            "item_code": row.item_code,
            "item_name": row.item_name,
            "qty": row.qty,
            "rate": row.rate,
            "amount": row.amount,
            "warehouse": row.warehouse,
            "serial_no": getattr(row, "serial_no", None),
        })

    return {
        "name": doc.name,
        "supplier": doc.supplier,
        "supplier_name": doc.supplier_name,
        "posting_date": doc.posting_date,
        "due_date": doc.due_date,
        "status": doc.status,
        "currency": doc.currency,
        "grand_total": doc.grand_total,
        "outstanding_amount": doc.outstanding_amount,
        "items": items,
    }


@frappe.whitelist()
def prepare_purchase_invoice(supplier: str, warehouse: str | None = None):
    if not frappe.db.exists("Supplier", supplier):
        frappe.throw(_("Tedarikçi bulunamadı."))

    doc = frappe.new_doc("Purchase Invoice")
    doc.supplier = supplier
    doc.update_stock = 1
    if warehouse:
        doc.set_warehouse = warehouse

    return doc.as_dict()


@frappe.whitelist()
def prepare_supplier_payment(supplier: str, amount: float, reference_no: str | None = None):
    amount = float(amount or 0)
    if amount <= 0:
        frappe.throw(_("Ödeme tutarı sıfırdan büyük olmalıdır."))

    if not frappe.db.exists("Supplier", supplier):
        frappe.throw(_("Tedarikçi bulunamadı."))

    pe = frappe.new_doc("Payment Entry")
    pe.payment_type = "Pay"
    pe.party_type = "Supplier"
    pe.party = supplier
    pe.paid_amount = amount
    pe.received_amount = amount
    if reference_no:
        pe.reference_no = reference_no

    pe.flags.ignore_mandatory = True
    return pe.as_dict()


@frappe.whitelist()
def get_supplier_recent_purchases(supplier: str, limit: int = 50):
    return frappe.get_all(
        "Purchase Invoice",
        filters={"supplier": supplier, "docstatus": ["<", 2]},
        fields=[
            "name",
            "posting_date",
            "status",
            "currency",
            "grand_total",
            "outstanding_amount",
        ],
        order_by="posting_date desc, creation desc",
        limit_page_length=min(max(int(limit or 50), 1), 200),
    )
