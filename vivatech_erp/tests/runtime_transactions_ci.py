import frappe

from vivatech_erp.tests import runtime_transactions


def _ensure_current_fiscal_year():
    today = frappe.utils.getdate(frappe.utils.nowdate())
    existing = frappe.db.get_value(
        "Fiscal Year",
        {
            "year_start_date": ("<=", today),
            "year_end_date": (">=", today),
            "disabled": 0,
        },
        "name",
    )
    if existing:
        return existing

    doc = frappe.new_doc("Fiscal Year")
    doc.year = str(today.year)
    doc.year_start_date = f"{today.year}-01-01"
    doc.year_end_date = f"{today.year}-12-31"
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return doc.name


def _ensure_test_defaults():
    # The CI site's seed defaults can use a currency different from the
    # dedicated Vivatech test company. Keep document defaults aligned with
    # the company's TRY ledgers so ERPNext v16 validates party accounts.
    frappe.db.set_single_value("Global Defaults", "default_currency", "TRY")
    frappe.db.commit()


def run():
    _ensure_current_fiscal_year()
    _ensure_test_defaults()
    return runtime_transactions.run()
