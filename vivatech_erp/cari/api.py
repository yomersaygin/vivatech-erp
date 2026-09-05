import frappe
from frappe import _

@frappe.whitelist()
def get_cari_summary(party_type: str, party: str):
    if party_type not in ("Customer", "Supplier"):
        frappe.throw(_("Geçersiz cari türü."))

    doc = frappe.get_doc(party_type, party)

    if party_type == "Customer":
        account_field = "customer"
        party_label = doc.customer_name
    else:
        account_field = "supplier"
        party_label = doc.supplier_name

    balance = frappe.db.sql(
        """
        select coalesce(sum(debit - credit), 0)
        from `tabGL Entry`
        where party_type=%s and party=%s and is_cancelled=0
        """,
        (party_type, party),
    )[0][0] or 0

    last_movements = frappe.get_all(
        "GL Entry",
        filters={"party_type": party_type, "party": party, "is_cancelled": 0},
        fields=["posting_date", "voucher_type", "voucher_no", "debit", "credit", "remarks"],
        order_by="posting_date desc, creation desc",
        limit_page_length=20,
    )

    return {
        "party_type": party_type,
        "party": party,
        "name": party_label,
        "balance": balance,
        "movements": last_movements,
    }


@frappe.whitelist()
def create_payment_entry(party_type: str, party: str, amount: float, mode: str = "Receive"):
    amount = float(amount or 0)
    if amount <= 0:
        frappe.throw(_("Tutar sıfırdan büyük olmalıdır."))

    if party_type not in ("Customer", "Supplier"):
        frappe.throw(_("Geçersiz cari türü."))

    payment_type = "Receive" if mode == "Receive" else "Pay"

    pe = frappe.new_doc("Payment Entry")
    pe.payment_type = payment_type
    pe.party_type = party_type
    pe.party = party
    pe.paid_amount = amount
    pe.received_amount = amount
    pe.flags.ignore_mandatory = True

    return pe.as_dict()
