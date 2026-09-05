import frappe


@frappe.whitelist()
def get_home_summary():
    customer_balance = frappe.db.sql(
        '''
        select coalesce(sum(debit-credit), 0)
        from `tabGL Entry`
        where party_type='Customer' and is_cancelled=0
        '''
    )[0][0]

    supplier_balance = frappe.db.sql(
        '''
        select coalesce(sum(credit-debit), 0)
        from `tabGL Entry`
        where party_type='Supplier' and is_cancelled=0
        '''
    )[0][0]

    stock_qty = frappe.db.sql(
        '''
        select coalesce(sum(actual_qty), 0)
        from `tabBin`
        '''
    )[0][0]

    open_sales = frappe.db.count(
        "Sales Invoice",
        filters={"docstatus": ["<", 2], "outstanding_amount": [">", 0]}
    )

    open_purchases = frappe.db.count(
        "Purchase Invoice",
        filters={"docstatus": ["<", 2], "outstanding_amount": [">", 0]}
    )

    active_serials = frappe.db.count(
        "Serial No",
        filters={"status": "Active"}
    )

    return {
        "customer_balance": customer_balance,
        "supplier_balance": supplier_balance,
        "stock_qty": stock_qty,
        "open_sales": open_sales,
        "open_purchases": open_purchases,
        "active_serials": active_serials,
    }


@frappe.whitelist()
def get_recent_activity(limit: int = 25):
    limit = min(max(int(limit or 25), 1), 100)

    sales = frappe.get_all(
        "Sales Invoice",
        filters={"docstatus": ["<", 2]},
        fields=["name", "posting_date", "customer_name as party", "grand_total as amount", "status"],
        order_by="modified desc",
        limit_page_length=limit,
    )
    for row in sales:
        row["type"] = "Satış"

    purchases = frappe.get_all(
        "Purchase Invoice",
        filters={"docstatus": ["<", 2]},
        fields=["name", "posting_date", "supplier_name as party", "grand_total as amount", "status"],
        order_by="modified desc",
        limit_page_length=limit,
    )
    for row in purchases:
        row["type"] = "Alış"

    payments = frappe.get_all(
        "Payment Entry",
        filters={"docstatus": ["<", 2]},
        fields=["name", "posting_date", "party", "paid_amount as amount", "status"],
        order_by="modified desc",
        limit_page_length=limit,
    )
    for row in payments:
        row["type"] = "Finans"

    rows = sales + purchases + payments
    rows = sorted(rows, key=lambda x: (str(x.get("posting_date") or ""), str(x.get("name") or "")), reverse=True)
    return rows[:limit]
