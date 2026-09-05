import frappe


COMPANY = "Vivatech CI"
ABBR = "VCI"
WAREHOUSE_NAME = "CI Depo"
CUSTOMER = "Vivatech CI Müşteri"
SUPPLIER = "Vivatech CI Tedarikçi"
ITEM = "VVT-CI-STOK-001"
QTY = 2.0
RATE = 100.0


def _ensure_company():
    if not frappe.db.exists("Company", COMPANY):
        doc = frappe.new_doc("Company")
        doc.company_name = COMPANY
        doc.abbr = ABBR
        doc.default_currency = "TRY"
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
    return CUSTOMER


def _ensure_supplier():
    if not frappe.db.exists("Supplier", SUPPLIER):
        doc = frappe.new_doc("Supplier")
        doc.supplier_name = SUPPLIER
        doc.supplier_group = "All Supplier Groups"
        doc.insert(ignore_permissions=True)
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


def run():
    _ensure_company()
    warehouse = _ensure_warehouse()
    _ensure_customer()
    _ensure_supplier()
    _ensure_item()
    frappe.db.commit()

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

    after_purchase = _stock(warehouse)
    if abs(after_purchase - (start_stock + QTY)) > 0.001:
        raise AssertionError(f"Purchase stock mismatch: {start_stock} -> {after_purchase}")
    purchase_gl = _assert_gl("Purchase Invoice", pi.name)
    if float(pi.outstanding_amount or 0) <= 0:
        raise AssertionError("Purchase Invoice outstanding amount did not increase")

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
    if float(si.outstanding_amount or 0) <= 0:
        raise AssertionError("Sales Invoice outstanding amount did not increase")

    return {
        "passed": True,
        "company": COMPANY,
        "warehouse": warehouse,
        "item": ITEM,
        "purchase_invoice": pi.name,
        "sales_invoice": si.name,
        "stock_before": start_stock,
        "stock_after_purchase": after_purchase,
        "stock_after_sale": after_sale,
        "purchase_gl_entries": purchase_gl,
        "sales_gl_entries": sales_gl,
        "purchase_outstanding": float(pi.outstanding_amount or 0),
        "sales_outstanding": float(si.outstanding_amount or 0),
    }
