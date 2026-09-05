import frappe


@frappe.whitelist()
def get_dashboard_summary():
    customer_balance = frappe.db.sql("select coalesce(sum(debit - credit), 0) from `tabGL Entry` where party_type='Customer' and is_cancelled=0")[0][0]
    supplier_balance = frappe.db.sql("select coalesce(sum(credit - debit), 0) from `tabGL Entry` where party_type='Supplier' and is_cancelled=0")[0][0]
    stock_qty = frappe.db.sql("select coalesce(sum(actual_qty), 0) from `tabBin`")[0][0]
    sales_total = frappe.db.sql("select coalesce(sum(grand_total), 0) from `tabSales Invoice` where docstatus=1")[0][0]
    purchase_total = frappe.db.sql("select coalesce(sum(grand_total), 0) from `tabPurchase Invoice` where docstatus=1")[0][0]
    return {"customer_balance": customer_balance, "supplier_balance": supplier_balance, "stock_qty": stock_qty, "sales_total": sales_total, "purchase_total": purchase_total}


@frappe.whitelist()
def get_customer_balances(limit: int = 200):
    return frappe.db.sql("""select party as customer, sum(debit) as debit, sum(credit) as credit, sum(debit-credit) as balance from `tabGL Entry` where party_type='Customer' and party is not null and is_cancelled=0 group by party order by abs(sum(debit-credit)) desc limit %s""", (min(max(int(limit or 200), 1), 500),), as_dict=True)


@frappe.whitelist()
def get_supplier_balances(limit: int = 200):
    return frappe.db.sql("""select party as supplier, sum(debit) as debit, sum(credit) as credit, sum(credit-debit) as balance from `tabGL Entry` where party_type='Supplier' and party is not null and is_cancelled=0 group by party order by abs(sum(credit-debit)) desc limit %s""", (min(max(int(limit or 200), 1), 500),), as_dict=True)


@frappe.whitelist()
def get_stock_report(warehouse: str | None = None, limit: int = 300):
    filters = {"warehouse": warehouse} if warehouse else {}
    return frappe.get_all("Bin", filters=filters, fields=["item_code", "warehouse", "actual_qty", "reserved_qty", "ordered_qty", "projected_qty"], order_by="item_code asc, warehouse asc", limit_page_length=min(max(int(limit or 300), 1), 500))


def _date_filters(from_date=None, to_date=None):
    filters = {"docstatus": 1}
    if from_date and to_date:
        filters["posting_date"] = ["between", [from_date, to_date]]
    elif from_date:
        filters["posting_date"] = [">=", from_date]
    elif to_date:
        filters["posting_date"] = ["<=", to_date]
    return filters


@frappe.whitelist()
def get_sales_report(from_date=None, to_date=None, limit: int = 200):
    return frappe.get_all("Sales Invoice", filters=_date_filters(from_date, to_date), fields=["name", "posting_date", "customer", "customer_name", "currency", "grand_total", "outstanding_amount", "status"], order_by="posting_date desc, creation desc", limit_page_length=min(max(int(limit or 200), 1), 500))


@frappe.whitelist()
def get_purchase_report(from_date=None, to_date=None, limit: int = 200):
    return frappe.get_all("Purchase Invoice", filters=_date_filters(from_date, to_date), fields=["name", "posting_date", "supplier", "supplier_name", "currency", "grand_total", "outstanding_amount", "status"], order_by="posting_date desc, creation desc", limit_page_length=min(max(int(limit or 200), 1), 500))


@frappe.whitelist()
def get_finance_report(limit: int = 200):
    return frappe.get_all("Payment Entry", filters={"docstatus": 1}, fields=["name", "posting_date", "payment_type", "party_type", "party", "mode_of_payment", "paid_amount", "received_amount", "paid_from", "paid_to", "status"], order_by="posting_date desc, creation desc", limit_page_length=min(max(int(limit or 200), 1), 500))


@frappe.whitelist()
def get_serial_report(item_code=None, warehouse=None, limit: int = 300):
    filters = {}
    if item_code:
        filters["item_code"] = item_code
    if warehouse:
        filters["warehouse"] = warehouse
    fields = ["name", "item_code", "warehouse", "status"]
    meta = frappe.get_meta("Serial No")
    for fieldname in ("purchase_document_no", "delivery_document_no"):
        if meta.has_field(fieldname):
            fields.append(fieldname)
    return frappe.get_all("Serial No", filters=filters, fields=fields, order_by="modified desc", limit_page_length=min(max(int(limit or 300), 1), 500))
