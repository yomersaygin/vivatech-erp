import frappe


CORE_DOCTYPES = [
    "Customer",
    "Supplier",
    "Item",
    "Warehouse",
    "Purchase Invoice",
    "Sales Invoice",
    "Payment Entry",
    "Serial No",
]


def verify_core_doctypes():
    missing = [doctype for doctype in CORE_DOCTYPES if not frappe.db.exists("DocType", doctype)]
    if missing:
        raise AssertionError(f"Missing core ERP DocTypes: {missing}")
    return {"ok": True, "doctypes": CORE_DOCTYPES}
