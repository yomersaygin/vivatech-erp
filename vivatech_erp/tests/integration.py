import frappe
from frappe.utils import nowdate

def run_all():
    """Explicit live smoke test. Requires a configured ERPNext site/company/accounts."""
    result = {
        "site": frappe.local.site,
        "customer_doctype": bool(frappe.db.exists("DocType", "Customer")),
        "supplier_doctype": bool(frappe.db.exists("DocType", "Supplier")),
        "item_doctype": bool(frappe.db.exists("DocType", "Item")),
        "warehouse_doctype": bool(frappe.db.exists("DocType", "Warehouse")),
        "serial_no_doctype": bool(frappe.db.exists("DocType", "Serial No")),
        "purchase_invoice_doctype": bool(frappe.db.exists("DocType", "Purchase Invoice")),
        "sales_invoice_doctype": bool(frappe.db.exists("DocType", "Sales Invoice")),
        "payment_entry_doctype": bool(frappe.db.exists("DocType", "Payment Entry")),
        "gl_entry_doctype": bool(frappe.db.exists("DocType", "GL Entry")),
        "stock_ledger_doctype": bool(frappe.db.exists("DocType", "Stock Ledger Entry")),
    }
    missing=[k for k,v in result.items() if k!="site" and not v]
    result["passed"] = not missing
    result["missing"] = missing
    print(frappe.as_json(result, indent=2))
    return result
