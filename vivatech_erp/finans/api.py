import frappe
from frappe import _

@frappe.whitelist()
def get_finance_accounts(company: str | None = None):
    filters = {"is_group": 0, "disabled": 0}
    if company:
        filters["company"] = company

    accounts = frappe.get_all(
        "Account",
        filters=filters,
        fields=["name", "account_name", "account_type", "root_type", "company", "account_currency"],
        order_by="account_type asc, account_name asc",
        limit_page_length=500,
    )

    allowed_types = {"Cash", "Bank", "Receivable", "Payable"}
    return [a for a in accounts if a.account_type in allowed_types]


@frappe.whitelist()
def get_recent_payments(party_type: str | None = None, party: str | None = None, limit: int = 100):
    filters = {"docstatus": ["<", 2]}
    if party_type:
        filters["party_type"] = party_type
    if party:
        filters["party"] = party

    return frappe.get_all(
        "Payment Entry",
        filters=filters,
        fields=[
            "name",
            "posting_date",
            "payment_type",
            "party_type",
            "party",
            "paid_amount",
            "received_amount",
            "paid_from",
            "paid_to",
            "mode_of_payment",
            "status",
        ],
        order_by="posting_date desc, creation desc",
        limit_page_length=min(max(int(limit or 100), 1), 300),
    )


@frappe.whitelist()
def prepare_payment(
    payment_type: str,
    party_type: str,
    party: str,
    mode_of_payment: str | None = None,
    paid_from: str | None = None,
    paid_to: str | None = None,
):
    if payment_type not in {"Receive", "Pay"}:
        frappe.throw(_("Geçersiz ödeme tipi."))

    if party_type not in {"Customer", "Supplier"}:
        frappe.throw(_("Cari türü Customer veya Supplier olmalıdır."))

    if not frappe.db.exists(party_type, party):
        frappe.throw(_("Cari bulunamadı."))

    pe = frappe.new_doc("Payment Entry")
    pe.payment_type = payment_type
    pe.party_type = party_type
    pe.party = party

    if mode_of_payment:
        pe.mode_of_payment = mode_of_payment
    if paid_from:
        pe.paid_from = paid_from
    if paid_to:
        pe.paid_to = paid_to

    return pe.as_dict()


@frappe.whitelist()
def get_account_gl(account: str, limit: int = 100):
    if not frappe.db.exists("Account", account):
        frappe.throw(_("Hesap bulunamadı."))

    return frappe.get_all(
        "GL Entry",
        filters={"account": account, "is_cancelled": 0},
        fields=[
            "posting_date",
            "voucher_type",
            "voucher_no",
            "party_type",
            "party",
            "debit",
            "credit",
            "remarks",
        ],
        order_by="posting_date desc, creation desc",
        limit_page_length=min(max(int(limit or 100), 1), 300),
    )


def _company_defaults(company: str):
    if not frappe.db.exists("Company", company):
        frappe.throw(_("Şirket bulunamadı."))

    company_doc = frappe.get_doc("Company", company)
    return {
        "default_cash_account": getattr(company_doc, "default_cash_account", None),
        "default_bank_account": getattr(company_doc, "default_bank_account", None),
        "default_receivable_account": getattr(company_doc, "default_receivable_account", None),
        "default_payable_account": getattr(company_doc, "default_payable_account", None),
        "default_currency": getattr(company_doc, "default_currency", None),
    }


@frappe.whitelist()
def prepare_vivatech_payment(
    payment_type: str,
    party_type: str,
    party: str,
    company: str,
    amount: float,
    settlement_account: str | None = None,
    mode_of_payment: str | None = None,
):
    if payment_type not in ("Receive", "Pay"):
        frappe.throw(_("Ödeme tipi Receive veya Pay olmalıdır."))
    if party_type not in ("Customer", "Supplier"):
        frappe.throw(_("Cari tipi Customer veya Supplier olmalıdır."))
    if not frappe.db.exists(party_type, party):
        frappe.throw(_("Cari bulunamadı."))

    amount = float(amount or 0)
    if amount <= 0:
        frappe.throw(_("Tutar sıfırdan büyük olmalıdır."))

    defaults = _company_defaults(company)

    if not settlement_account:
        settlement_account = (
            defaults["default_cash_account"]
            or defaults["default_bank_account"]
        )

    if not settlement_account:
        frappe.throw(_("Şirket için varsayılan kasa veya banka hesabı tanımlı değil."))

    doc = frappe.new_doc("Payment Entry")
    doc.payment_type = payment_type
    doc.party_type = party_type
    doc.party = party
    doc.company = company
    doc.paid_amount = amount
    doc.received_amount = amount

    if mode_of_payment:
        doc.mode_of_payment = mode_of_payment

    if payment_type == "Receive":
        doc.paid_from = defaults["default_receivable_account"] or ""
        doc.paid_to = settlement_account
    else:
        doc.paid_from = settlement_account
        doc.paid_to = defaults["default_payable_account"] or ""

    return doc.as_dict()


PAYMENT_FLOW_TYPES = {
    "Nakit": "Cash",
    "Havale": "Bank",
    "Kart": "Bank",
}


@frappe.whitelist()
def resolve_payment_flow(
    company: str,
    flow_type: str,
    mode_of_payment: str | None = None,
    settlement_account: str | None = None,
):
    if flow_type not in PAYMENT_FLOW_TYPES:
        frappe.throw(_("Ödeme akışı Nakit, Havale veya Kart olmalıdır."))

    defaults = _company_defaults(company)
    account_type = PAYMENT_FLOW_TYPES[flow_type]

    if not settlement_account:
        if account_type == "Cash":
            settlement_account = defaults["default_cash_account"]
        else:
            settlement_account = defaults["default_bank_account"]

    if not settlement_account:
        frappe.throw(_("Bu ödeme akışı için uygun varsayılan hesap tanımlı değil."))

    account = frappe.get_doc("Account", settlement_account)
    if getattr(account, "is_group", 0):
        frappe.throw(_("Grup hesap ödeme hesabı olarak kullanılamaz."))

    if account_type == "Cash" and getattr(account, "account_type", None) != "Cash":
        frappe.throw(_("Nakit akışı için Cash tipinde hesap gerekir."))

    if account_type == "Bank" and getattr(account, "account_type", None) != "Bank":
        frappe.throw(_("Havale/Kart akışı için Bank tipinde hesap gerekir."))

    return {
        "flow_type": flow_type,
        "mode_of_payment": mode_of_payment,
        "settlement_account": settlement_account,
        "account_type": account_type,
    }


@frappe.whitelist()
def prepare_flow_payment(
    payment_type: str,
    party_type: str,
    party: str,
    company: str,
    amount: float,
    flow_type: str,
    mode_of_payment: str | None = None,
    settlement_account: str | None = None,
):
    flow = resolve_payment_flow(
        company=company,
        flow_type=flow_type,
        mode_of_payment=mode_of_payment,
        settlement_account=settlement_account,
    )

    doc = prepare_vivatech_payment(
        payment_type=payment_type,
        party_type=party_type,
        party=party,
        company=company,
        amount=amount,
        settlement_account=flow["settlement_account"],
        mode_of_payment=mode_of_payment,
    )

    doc["vivatech_flow_type"] = flow_type
    doc["vivatech_account_type"] = flow["account_type"]
    return doc

