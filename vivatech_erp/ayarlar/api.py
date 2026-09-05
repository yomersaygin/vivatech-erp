import frappe
from frappe import _


@frappe.whitelist()
def get_general_settings():
    companies = frappe.get_all(
        "Company",
        fields=["name", "company_name", "abbr", "default_currency", "country"],
        order_by="company_name asc",
        limit_page_length=100,
    )

    warehouses = frappe.get_all(
        "Warehouse",
        filters={"disabled": 0},
        fields=["name", "warehouse_name", "company", "is_group"],
        order_by="warehouse_name asc",
        limit_page_length=300,
    )

    payment_modes = frappe.get_all(
        "Mode of Payment",
        filters={"enabled": 1},
        fields=["name", "type", "enabled"],
        order_by="name asc",
        limit_page_length=200,
    )

    currencies = frappe.get_all(
        "Currency",
        filters={"enabled": 1},
        fields=["name", "currency_name", "symbol"],
        order_by="name asc",
        limit_page_length=200,
    )

    return {
        "companies": companies,
        "warehouses": warehouses,
        "payment_modes": payment_modes,
        "currencies": currencies,
    }


@frappe.whitelist()
def get_company_defaults(company: str):
    if not frappe.db.exists("Company", company):
        frappe.throw(_("Şirket bulunamadı."))

    doc = frappe.get_doc("Company", company)

    return {
        "company": doc.name,
        "company_name": doc.company_name,
        "abbr": doc.abbr,
        "default_currency": doc.default_currency,
        "country": doc.country,
        "default_cash_account": getattr(doc, "default_cash_account", None),
        "default_bank_account": getattr(doc, "default_bank_account", None),
        "default_receivable_account": getattr(doc, "default_receivable_account", None),
        "default_payable_account": getattr(doc, "default_payable_account", None),
    }


@frappe.whitelist()
def update_company_defaults(
    company: str,
    default_currency: str | None = None,
    default_cash_account: str | None = None,
    default_bank_account: str | None = None,
):
    if not frappe.db.exists("Company", company):
        frappe.throw(_("Şirket bulunamadı."))

    doc = frappe.get_doc("Company", company)

    if default_currency:
        doc.default_currency = default_currency

    if default_cash_account is not None and hasattr(doc, "default_cash_account"):
        doc.default_cash_account = default_cash_account

    if default_bank_account is not None and hasattr(doc, "default_bank_account"):
        doc.default_bank_account = default_bank_account

    doc.save(ignore_permissions=False)

    return {
        "company": doc.name,
        "default_currency": doc.default_currency,
        "default_cash_account": getattr(doc, "default_cash_account", None),
        "default_bank_account": getattr(doc, "default_bank_account", None),
    }


@frappe.whitelist()
def get_vivatech_defaults():
    defaults = frappe.get_single("Global Defaults")
    return {
        "default_company": getattr(defaults, "default_company", None),
        "default_currency": getattr(defaults, "default_currency", None),
        "country": getattr(defaults, "country", None),
    }


@frappe.whitelist()
def set_global_defaults(default_company: str | None = None, default_currency: str | None = None):
    doc = frappe.get_single("Global Defaults")

    if default_company:
        if not frappe.db.exists("Company", default_company):
            frappe.throw(_("Şirket bulunamadı."))
        doc.default_company = default_company

    if default_currency:
        if not frappe.db.exists("Currency", default_currency):
            frappe.throw(_("Para birimi bulunamadı."))
        doc.default_currency = default_currency

    doc.save(ignore_permissions=False)

    return {
        "default_company": getattr(doc, "default_company", None),
        "default_currency": getattr(doc, "default_currency", None),
    }
