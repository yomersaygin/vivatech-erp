import frappe
from frappe import _

@frappe.whitelist()
def get_product_summary(item_code: str):
    item = frappe.get_doc("Item", item_code)

    stock_rows = frappe.get_all(
        "Bin",
        filters={"item_code": item_code},
        fields=[
            "warehouse",
            "actual_qty",
            "projected_qty",
            "reserved_qty",
            "ordered_qty",
        ],
        order_by="warehouse asc",
    )

    total_stock = sum((row.actual_qty or 0) for row in stock_rows)

    barcode_rows = frappe.get_all(
        "Item Barcode",
        filters={"parent": item_code, "parenttype": "Item"},
        fields=["barcode", "barcode_type"],
        order_by="idx asc",
    )

    return {
        "item_code": item.item_code,
        "item_name": item.item_name,
        "item_group": item.item_group,
        "brand": getattr(item, "brand", None),
        "stock_uom": item.stock_uom,
        "has_serial_no": bool(getattr(item, "has_serial_no", 0)),
        "has_batch_no": bool(getattr(item, "has_batch_no", 0)),
        "is_stock_item": bool(getattr(item, "is_stock_item", 0)),
        "barcodes": barcode_rows,
        "total_stock": total_stock,
        "warehouses": stock_rows,
    }


@frappe.whitelist()
def get_price_summary(item_code: str):
    rows = frappe.get_all(
        "Item Price",
        filters={"item_code": item_code, "enabled": 1},
        fields=["price_list", "price_list_rate", "currency", "selling", "buying"],
        order_by="selling desc, buying desc, price_list asc",
        limit_page_length=50,
    )

    sales = [r for r in rows if r.selling]
    purchases = [r for r in rows if r.buying]

    return {
        "sales_prices": sales,
        "purchase_prices": purchases,
    }


@frappe.whitelist()
def get_serials(item_code: str, warehouse: str | None = None):
    filters = {
        "item_code": item_code,
        "status": "Active",
    }
    if warehouse:
        filters["warehouse"] = warehouse

    return frappe.get_all(
        "Serial No",
        filters=filters,
        fields=["name", "warehouse", "status", "purchase_document_no", "delivery_document_no"],
        order_by="creation desc",
        limit_page_length=100,
    )
