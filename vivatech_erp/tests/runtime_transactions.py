import frappe


COUNTRY = "Turkey"
COMPANY = "Vivatech CI"
ABBR = "VCI"
WAREHOUSE_NAME = "CI Depo"
CUSTOMER = "Vivatech CI Müşteri"
SUPPLIER = "Vivatech CI Tedarikçi"
ITEM = "VVT-CI-STOK-001"
QTY = 5.0
RATE = 100.0


def _ensure_country():
    if not frappe.db.exists("Country", COUNTRY):
        doc = frappe.new_doc("Country")
        doc.country_name = COUNTRY
        doc.code = "TR"
        doc.insert(ignore_permissions=True)
    if not frappe.db.exists("Country", COUNTRY):
        raise AssertionError("Test country was not created")
    return COUNTRY


def _ensure_warehouse_type():
    if not frappe.db.exists("Warehouse Type", "Transit"):
        doc = frappe.new_doc("Warehouse Type")
        doc.name = "Transit"
        doc.insert(ignore_permissions=True)
    if not frappe.db.exists("Warehouse Type", "Transit"):
        raise AssertionError("Transit Warehouse Type was not created")
    return "Transit"


def _ensure_company():
    if not frappe.db.exists("Company", COMPANY):
        doc = frappe.new_doc("Company")
        doc.company_name = COMPANY
        doc.abbr = ABBR
        doc.default_currency = "TRY"
        doc.country = COUNTRY
        doc.create_chart_of_accounts_based_on = "Standard Template"
        doc.chart_of_accounts = "Standard"
        doc.insert(ignore_permissions=True)
    return COMPANY


def _ensure_warehouse():
    existing = frappe.db.exists("Warehouse", {"warehouse_name": WAREHOUSE_NAME, "company": COMPANY})
    if existing:
        return existing
    doc = frappe.new_doc("Warehouse")
    doc.warehouse_name = WAREHOUSE_NAME
    doc.company = COMPANY
    doc.is_group = 0
    doc.insert(ignore_permissions=True)
    return doc.name


def _ensure_customer():
    if not frappe.db.exists("Customer", CUSTOMER):
        doc = frappe.new_doc("Customer")
        doc.customer_name = CUSTOMER
        doc.customer_type = "Company"
        doc.customer_group = "All Customer Groups"
        doc.territory = "All Territories"
        doc.insert(ignore_permissions=True)
    if not frappe.db.exists("Customer", CUSTOMER):
        raise AssertionError("Test customer was not created")
    return CUSTOMER


def _ensure_supplier():
    if not frappe.db.exists("Supplier", SUPPLIER):
        doc = frappe.new_doc("Supplier")
        doc.supplier_name = SUPPLIER
        doc.supplier_group = "All Supplier Groups"
        doc.insert(ignore_permissions=True)
    if not frappe.db.exists("Supplier", SUPPLIER):
        raise AssertionError("Test supplier was not created")
    return SUPPLIER


def _ensure_item():
    if not frappe.db.exists("Item", ITEM):
        doc = frappe.new_doc("Item")
        doc.item_code = ITEM
        doc.item_name = ITEM
        doc.item_group = "All Item Groups"
        doc.stock_uom = "Nos"
        doc.is_stock_item = 1
        doc.insert(ignore_permissions=True)
    return ITEM


def _stock(warehouse):
    return float(frappe.db.get_value("Bin", {"item_code": ITEM, "warehouse": warehouse}, "actual_qty") or 0)


def _assert_gl(voucher_type, voucher_no):
    count = frappe.db.count("GL Entry", {"voucher_type": voucher_type, "voucher_no": voucher_no, "is_cancelled": 0})
    if count <= 0:
        raise AssertionError(f"No GL Entry created for {voucher_type} {voucher_no}")
    return count


def _assert_party_gl(voucher_type, voucher_no, party_type, party):
    count = frappe.db.count("GL Entry", {
        "voucher_type": voucher_type,
        "voucher_no": voucher_no,
        "party_type": party_type,
        "party": party,
        "is_cancelled": 0,
    })
    if count <= 0:
        raise AssertionError(f"No party GL Entry for {party_type} {party} on {voucher_type} {voucher_no}")
    return count


def _cash_account():
    account = frappe.db.get_value("Account", {"company": COMPANY, "account_type": "Cash", "is_group": 0}, "name")
    if not account:
        raise AssertionError("No cash account found for test company")
    return account


def _party_account(party_type, party):
    from erpnext.accounts.party import get_party_account
    return get_party_account(party_type, party, COMPANY)


def _payment(payment_type, party_type, party, reference_doctype, reference_name, amount, cash):
    doc = frappe.new_doc("Payment Entry")
    doc.payment_type = payment_type
    doc.company = COMPANY
    doc.party_type = party_type
    doc.party = party
    if payment_type == "Receive":
        doc.paid_from = _party_account(party_type, party)
        doc.paid_to = cash
    else:
        doc.paid_from = cash
        doc.paid_to = _party_account(party_type, party)
    doc.paid_amount = amount
    doc.received_amount = amount
    doc.append("references", {
        "reference_doctype": reference_doctype,
        "reference_name": reference_name,
        "allocated_amount": amount,
    })
    doc.set_missing_values()
    doc.insert(ignore_permissions=True)
    doc.submit()
    frappe.db.commit()
    return doc


def run():
    _ensure_country()
    _ensure_warehouse_type()
    _ensure_company()
    warehouse = _ensure_warehouse()
    _ensure_customer()
    _ensure_supplier()
    _ensure_item()
    frappe.db.commit()
    print("SETUP_OK")

    start_stock = _stock(warehouse)

    pi = frappe.new_doc("Purchase Invoice")
    pi.company = COMPANY
    pi.supplier = SUPPLIER
    pi.update_stock = 1
    pi.set_warehouse = warehouse
    pi.append("items", {"item_code": ITEM, "qty": QTY, "rate": RATE, "warehouse": warehouse})
    pi.set_missing_values()
    pi.insert(ignore_permissions=True)
    pi.submit()
    frappe.db.commit()

    if pi.docstatus != 1 or pi.supplier != SUPPLIER:
        raise AssertionError("Purchase Invoice did not submit against the expected supplier")
    after_purchase = _stock(warehouse)
    if abs(after_purchase - (start_stock + QTY)) > 0.001:
        raise AssertionError(f"Purchase stock mismatch: {start_stock} -> {after_purchase}")
    purchase_gl = _assert_gl("Purchase Invoice", pi.name)
    supplier_gl = _assert_party_gl("Purchase Invoice", pi.name, "Supplier", SUPPLIER)
    purchase_outstanding = float(pi.outstanding_amount or 0)
    if purchase_outstanding <= 0:
        raise AssertionError("Purchase Invoice outstanding amount did not increase")
    print(f"PURCHASE_OK invoice={pi.name} stock_before={start_stock} stock_after={after_purchase} supplier_gl={supplier_gl}")

    si = frappe.new_doc("Sales Invoice")
    si.company = COMPANY
    si.customer = CUSTOMER
    si.update_stock = 1
    si.set_warehouse = warehouse
    si.append("items", {"item_code": ITEM, "qty": QTY, "rate": RATE, "warehouse": warehouse})
    si.set_missing_values()
    si.insert(ignore_permissions=True)
    si.submit()
    frappe.db.commit()

    after_sale = _stock(warehouse)
    if abs(after_sale - start_stock) > 0.001:
        raise AssertionError(f"Sales stock mismatch: expected {start_stock}, got {after_sale}")
    sales_gl = _assert_gl("Sales Invoice", si.name)
    customer_gl = _assert_party_gl("Sales Invoice", si.name, "Customer", CUSTOMER)
    sales_outstanding = float(si.outstanding_amount or 0)
    if sales_outstanding <= 0:
        raise AssertionError("Sales Invoice outstanding amount did not increase")
    print(f"SALES_OK invoice={si.name} stock_after={after_sale} customer_gl={customer_gl}")

    cash = _cash_account()
    receipt = _payment("Receive", "Customer", CUSTOMER, "Sales Invoice", si.name, sales_outstanding, cash)
    supplier_payment = _payment("Pay", "Supplier", SUPPLIER, "Purchase Invoice", pi.name, purchase_outstanding, cash)

    si.reload()
    pi.reload()
    if abs(float(si.outstanding_amount or 0)) > 0.001:
        raise AssertionError(f"Sales Invoice payment allocation failed: {si.outstanding_amount}")
    if abs(float(pi.outstanding_amount or 0)) > 0.001:
        raise AssertionError(f"Purchase Invoice payment allocation failed: {pi.outstanding_amount}")
    receipt_gl = _assert_gl("Payment Entry", receipt.name)
    supplier_payment_gl = _assert_gl("Payment Entry", supplier_payment.name)
    print("PAYMENTS_OK")

    receipt.cancel()
    supplier_payment.cancel()
    si.cancel()
    pi.cancel()
    frappe.db.commit()

    final_stock = _stock(warehouse)
    if abs(final_stock - start_stock) > 0.001:
        raise AssertionError(f"Cancellation did not restore stock: {start_stock} -> {final_stock}")
    print(f"CANCEL_OK stock_final={final_stock}")

    return {
        "passed": True,
        "company": COMPANY,
        "warehouse": warehouse,
        "item": ITEM,
        "supplier": SUPPLIER,
        "customer": CUSTOMER,
        "purchase_invoice": pi.name,
        "sales_invoice": si.name,
        "customer_receipt": receipt.name,
        "supplier_payment": supplier_payment.name,
        "stock_before": start_stock,
        "stock_after_purchase": after_purchase,
        "stock_after_sale": after_sale,
        "stock_after_cancel": final_stock,
        "purchase_gl_entries": purchase_gl,
        "supplier_gl_entries": supplier_gl,
        "sales_gl_entries": sales_gl,
        "customer_gl_entries": customer_gl,
        "receipt_gl_entries": receipt_gl,
        "supplier_payment_gl_entries": supplier_payment_gl,
        "payments_allocated": True,
        "cancellation_restored_stock": True,
    }
