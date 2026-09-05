import frappe
from frappe import _

@frappe.whitelist()
def get_sales_summary(sales_invoice: str):
    doc = frappe.get_doc("Sales Invoice", sales_invoice)

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
        "customer": doc.customer,
        "customer_name": doc.customer_name,
        "posting_date": doc.posting_date,
        "due_date": doc.due_date,
        "status": doc.status,
        "currency": doc.currency,
        "grand_total": doc.grand_total,
        "outstanding_amount": doc.outstanding_amount,
        "items": items,
    }


@frappe.whitelist()
def prepare_sales_invoice(customer: str, warehouse: str | None = None):
    if not frappe.db.exists("Customer", customer):
        frappe.throw(_("Müşteri bulunamadı."))

    doc = frappe.new_doc("Sales Invoice")
    doc.customer = customer
    doc.update_stock = 1
    if warehouse:
        doc.set_warehouse = warehouse

    return doc.as_dict()


@frappe.whitelist()
def prepare_customer_receipt(customer: str, amount: float, reference_no: str | None = None):
    amount = float(amount or 0)
    if amount <= 0:
        frappe.throw(_("Tahsilat tutarı sıfırdan büyük olmalıdır."))

    if not frappe.db.exists("Customer", customer):
        frappe.throw(_("Müşteri bulunamadı."))

    pe = frappe.new_doc("Payment Entry")
    pe.payment_type = "Receive"
    pe.party_type = "Customer"
    pe.party = customer
    pe.paid_amount = amount
    pe.received_amount = amount
    if reference_no:
        pe.reference_no = reference_no

    pe.flags.ignore_mandatory = True
    return pe.as_dict()


@frappe.whitelist()
def get_customer_recent_sales(customer: str, limit: int = 50):
    return frappe.get_all(
        "Sales Invoice",
        filters={"customer": customer, "docstatus": ["<", 2]},
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
