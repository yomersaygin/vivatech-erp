frappe.pages["vivatech-ana-sayfa"].on_page_load = function(wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "Vivatech ERP",
        single_column: true
    });

    const html = `
    <div class="vivatech-home">
      <div class="home-summary row">
        <div class="col-md-2"><div class="home-card"><span>Müşteri Bakiyesi</span><strong class="h-customer">-</strong></div></div>
        <div class="col-md-2"><div class="home-card"><span>Tedarikçi Bakiyesi</span><strong class="h-supplier">-</strong></div></div>
        <div class="col-md-2"><div class="home-card"><span>Toplam Stok</span><strong class="h-stock">-</strong></div></div>
        <div class="col-md-2"><div class="home-card"><span>Açık Satış</span><strong class="h-sales">-</strong></div></div>
        <div class="col-md-2"><div class="home-card"><span>Açık Alış</span><strong class="h-purchases">-</strong></div></div>
        <div class="col-md-2"><div class="home-card"><span>Aktif IMEI/Seri</span><strong class="h-serials">-</strong></div></div>
      </div>
      <hr>
      <h4>Modüller</h4>
      <div class="row module-grid">
        <div class="col-md-3" data-vivatech-route="cari-karti"><button class="btn btn-default btn-block m-cari">Cari</button></div>
        <div class="col-md-3" data-vivatech-route="urun-karti"><button class="btn btn-default btn-block m-urun">Ürünler</button></div>
        <div class="col-md-3" data-vivatech-route="stok-depo"><button class="btn btn-default btn-block m-stok">Stok / Depo</button></div>
        <div class="col-md-3" data-vivatech-route="imei-seri"><button class="btn btn-default btn-block m-imei">IMEI / Seri No</button></div>
        <div class="col-md-3" data-vivatech-route="alis-merkezi"><button class="btn btn-default btn-block m-alis">Alış</button></div>
        <div class="col-md-3" data-vivatech-route="satis-merkezi"><button class="btn btn-default btn-block m-satis">Satış</button></div>
        <div class="col-md-3" data-vivatech-route="finans-merkezi"><button class="btn btn-default btn-block m-finans">Finans</button></div>
        <div class="col-md-3" data-vivatech-route="raporlar-merkezi"><button class="btn btn-default btn-block m-raporlar">Raporlar</button></div>
        <div class="col-md-3" data-vivatech-route="kullanicilar-yetkiler"><button class="btn btn-default btn-block m-yetkiler">Kullanıcılar / Yetkiler</button></div>
        <div class="col-md-3" data-vivatech-route="ayarlar-merkezi"><button class="btn btn-default btn-block m-ayarlar">Ayarlar</button></div>
      </div>
      <hr>
      <h4>Hızlı İşlemler</h4>
      <div class="quick-actions">
        <button class="btn btn-primary q-new-customer">Yeni Cari</button>
        <button class="btn btn-primary q-new-item">Yeni Ürün</button>
        <button class="btn btn-primary q-new-purchase">Yeni Alış Faturası</button>
        <button class="btn btn-primary q-new-sale">Yeni Satış Faturası</button>
        <button class="btn btn-primary q-new-payment">Tahsilat / Ödeme</button>
        <button class="btn btn-default q-stock-entry">Stok Hareketi</button>
      </div>
      <hr>
      <h4>Son Hareketler</h4>
      <div class="table-responsive">
        <table class="table table-bordered table-hover home-activity-table">
          <thead><tr><th>Tür</th><th>Belge</th><th>Tarih</th><th>Cari</th><th>Tutar</th><th>Durum</th></tr></thead>
          <tbody></tbody>
        </table>
      </div>
    </div>`;

    $(html).appendTo(page.body);
    const body = $(page.body);
    const money = v => format_currency(v || 0);
    const route = pageName => frappe.set_route("app", pageName);

    const routes = {
        ".m-cari": "cari-karti",
        ".m-urun": "urun-karti",
        ".m-stok": "stok-depo",
        ".m-imei": "imei-seri",
        ".m-alis": "alis-merkezi",
        ".m-satis": "satis-merkezi",
        ".m-finans": "finans-merkezi",
        ".m-raporlar": "raporlar-merkezi",
        ".m-yetkiler": "kullanicilar-yetkiler",
        ".m-ayarlar": "ayarlar-merkezi"
    };
    Object.entries(routes).forEach(([selector, target]) => body.find(selector).on("click", () => route(target)));

    body.find(".q-new-customer").on("click", () => {
        frappe.prompt([{
            fieldname: "party_type",
            label: "Cari Türü",
            fieldtype: "Select",
            options: "Customer\nSupplier",
            default: "Customer",
            reqd: 1
        }], values => frappe.new_doc(values.party_type), "Yeni Cari", "Devam");
    });
    body.find(".q-new-item").on("click", () => frappe.new_doc("Item"));
    body.find(".q-new-purchase").on("click", () => frappe.new_doc("Purchase Invoice"));
    body.find(".q-new-sale").on("click", () => frappe.new_doc("Sales Invoice"));
    body.find(".q-new-payment").on("click", () => frappe.new_doc("Payment Entry"));
    body.find(".q-stock-entry").on("click", () => frappe.new_doc("Stock Entry"));

    frappe.call({
        method: "vivatech_erp.dashboard.api.get_home_summary",
        callback: r => {
            const d = r.message || {};
            body.find(".h-customer").text(money(d.customer_balance));
            body.find(".h-supplier").text(money(d.supplier_balance));
            body.find(".h-stock").text(format_number(d.stock_qty || 0, null, 2));
            body.find(".h-sales").text(d.open_sales || 0);
            body.find(".h-purchases").text(d.open_purchases || 0);
            body.find(".h-serials").text(d.active_serials || 0);
        }
    });

    frappe.call({
        method: "vivatech_erp.dashboard.api.get_recent_activity",
        args: {limit: 25},
        callback: r => {
            const tbody = body.find(".home-activity-table tbody").empty();
            (r.message || []).forEach(row => {
                const tr = $(`<tr style="cursor:pointer"><td>${frappe.utils.escape_html(row.type || "")}</td><td>${frappe.utils.escape_html(row.name || "")}</td><td>${frappe.utils.escape_html(String(row.posting_date || ""))}</td><td>${frappe.utils.escape_html(row.party || "")}</td><td>${money(row.amount || 0)}</td><td>${frappe.utils.escape_html(row.status || "")}</td></tr>`);
                tr.on("click", () => {
                    const map = {"Satış": "Sales Invoice", "Alış": "Purchase Invoice", "Finans": "Payment Entry"};
                    if (map[row.type] && row.name) frappe.set_route("Form", map[row.type], row.name);
                });
                tbody.append(tr);
            });
        }
    });

    vivatech_filter_module_buttons(body[0]);
};

async function vivatech_filter_module_buttons(wrapper) {
    try {
        const r = await frappe.call({method: "vivatech_erp.yetkiler.api.get_visible_routes"});
        const visible = new Set(r.message || []);
        wrapper.querySelectorAll("[data-vivatech-route]").forEach(el => {
            const route = el.getAttribute("data-vivatech-route");
            el.style.display = visible.has(route) ? "" : "none";
        });
    } catch (e) {
        console.warn("Vivatech route visibility could not be resolved", e);
    }
}
