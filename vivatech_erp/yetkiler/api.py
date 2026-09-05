import frappe
from frappe import _


VIVATECH_ROLES = {
    "Vivatech Yönetici": {
        "modules": ["Cari", "Ürün", "Stok", "IMEI", "Alış", "Satış", "Finans", "Raporlar", "Ayarlar"],
        "frappe_roles": ["System Manager", "Accounts Manager", "Stock Manager", "Sales Manager", "Purchase Manager"],
    },
    "Vivatech Finans": {
        "modules": ["Cari", "Alış", "Satış", "Finans", "Raporlar"],
        "frappe_roles": ["Accounts User"],
    },
    "Vivatech Satış": {
        "modules": ["Cari", "Ürün", "Stok", "IMEI", "Satış"],
        "frappe_roles": ["Sales User", "Stock User"],
    },
    "Vivatech Satınalma": {
        "modules": ["Cari", "Ürün", "Stok", "IMEI", "Alış"],
        "frappe_roles": ["Purchase User", "Stock User"],
    },
    "Vivatech Depo": {
        "modules": ["Ürün", "Stok", "IMEI"],
        "frappe_roles": ["Stock User"],
    },
}


@frappe.whitelist()
def get_vivatech_roles():
    return VIVATECH_ROLES


@frappe.whitelist()
def get_user_summary(user: str):
    if not frappe.db.exists("User", user):
        frappe.throw(_("Kullanıcı bulunamadı."))
    doc = frappe.get_doc("User", user)
    roles = sorted({r.role for r in doc.roles})
    matched_profiles = []
    for profile, config in VIVATECH_ROLES.items():
        if any(role in roles for role in config["frappe_roles"]):
            matched_profiles.append(profile)
    return {"name": doc.name, "full_name": doc.full_name, "enabled": doc.enabled, "user_type": doc.user_type, "roles": roles, "matched_profiles": matched_profiles}


@frappe.whitelist()
def list_users(limit: int = 200):
    return frappe.get_all("User", filters={"name": ["not in", ["Guest"]]}, fields=["name", "full_name", "enabled", "user_type", "last_login"], order_by="enabled desc, full_name asc", limit_page_length=min(max(int(limit or 200), 1), 500))


@frappe.whitelist()
def get_role_matrix():
    return [{"profile": profile, "modules": ", ".join(config["modules"]), "frappe_roles": ", ".join(config["frappe_roles"]), "finance_access": "Finans" in config["modules"]} for profile, config in VIVATECH_ROLES.items()]


@frappe.whitelist()
def apply_role_profile(user: str, profile: str):
    if profile not in VIVATECH_ROLES:
        frappe.throw(_("Geçersiz Vivatech rol profili."))
    if not frappe.db.exists("User", user):
        frappe.throw(_("Kullanıcı bulunamadı."))
    doc = frappe.get_doc("User", user)
    managed_roles = set()
    for config in VIVATECH_ROLES.values():
        managed_roles.update(config["frappe_roles"])
    current_roles = [r.role for r in doc.roles if r.role not in managed_roles]
    target_roles = current_roles + VIVATECH_ROLES[profile]["frappe_roles"]
    doc.set("roles", [])
    for role in sorted(set(target_roles)):
        doc.append("roles", {"role": role})
    doc.save(ignore_permissions=False)
    return {"user": user, "profile": profile, "roles": sorted(set(target_roles))}


FINANCE_NATIVE_ROLES = {"Accounts User", "Accounts Manager", "System Manager"}
STOCK_ONLY_NATIVE_ROLES = {"Stock User"}


def _user_roles(user: str):
    if not frappe.db.exists("User", user):
        frappe.throw(_("Kullanıcı bulunamadı."))
    doc = frappe.get_doc("User", user)
    return {row.role for row in doc.roles}


@frappe.whitelist()
def can_access_finance(user: str | None = None):
    user = user or frappe.session.user
    return bool(_user_roles(user) & FINANCE_NATIVE_ROLES)


@frappe.whitelist()
def assert_finance_access(user: str | None = None):
    user = user or frappe.session.user
    if not can_access_finance(user):
        frappe.throw(_("Bu kullanıcı Finans modülüne erişemez."), frappe.PermissionError)
    return True


@frappe.whitelist()
def audit_role_profile(profile: str):
    if profile not in VIVATECH_ROLES:
        frappe.throw(_("Rol profili bulunamadı."))
    config = VIVATECH_ROLES[profile]
    native = set(config.get("frappe_roles") or [])
    return {"profile": profile, "native_roles": sorted(native), "finance_access": bool(native & FINANCE_NATIVE_ROLES), "stock_only": native == STOCK_ONLY_NATIVE_ROLES}


VIVATECH_ROUTE_RULES = {
    "vivatech-ana-sayfa": {"System Manager", "Accounts User", "Stock User", "Sales User", "Purchase User"},
    "cari-karti": {"System Manager", "Accounts User", "Sales User", "Purchase User"},
    "urun-karti": {"System Manager", "Stock User", "Sales User", "Purchase User"},
    "stok-depo": {"System Manager", "Stock User"},
    "imei-seri": {"System Manager", "Stock User"},
    "alis-merkezi": {"System Manager", "Purchase User", "Accounts User"},
    "satis-merkezi": {"System Manager", "Sales User", "Accounts User"},
    "finans-merkezi": {"System Manager", "Accounts User", "Accounts Manager"},
    "raporlar-merkezi": {"System Manager", "Accounts User", "Stock User", "Sales User", "Purchase User"},
    "kullanicilar-yetkiler": {"System Manager"},
    "ayarlar-merkezi": {"System Manager"},
}


def _native_roles_for_user(user: str):
    if user == "Administrator":
        return {"System Manager"}
    if not frappe.db.exists("User", user):
        frappe.throw(_("Kullanıcı bulunamadı."))
    doc = frappe.get_doc("User", user)
    return {row.role for row in doc.roles}


@frappe.whitelist()
def can_access_route(route: str, user: str | None = None):
    user = user or frappe.session.user
    if route not in VIVATECH_ROUTE_RULES:
        return False
    return bool(_native_roles_for_user(user) & VIVATECH_ROUTE_RULES[route])


@frappe.whitelist()
def assert_route_access(route: str, user: str | None = None):
    user = user or frappe.session.user
    if not can_access_route(route, user):
        frappe.throw(_("Bu sayfaya erişim yetkiniz yok."), frappe.PermissionError)
    return True


@frappe.whitelist()
def get_visible_routes(user: str | None = None):
    user = user or frappe.session.user
    return [route for route in VIVATECH_ROUTE_RULES if can_access_route(route, user)]


@frappe.whitelist()
def get_permission_matrix():
    return {route: sorted(list(roles)) for route, roles in VIVATECH_ROUTE_RULES.items()}
