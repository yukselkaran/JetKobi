import json
import os
from datetime import datetime
import re

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def load_orders():
    with open(os.path.join(DATA_DIR, "orders.json"), "r", encoding="utf-8") as f:
        return json.load(f)

def save_orders(orders):
    with open(os.path.join(DATA_DIR, "orders.json"), "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

def load_stocks():
    with open(os.path.join(DATA_DIR, "stocks.json"), "r", encoding="utf-8") as f:
        return json.load(f)

def save_stocks(stocks):
    with open(os.path.join(DATA_DIR, "stocks.json"), "w", encoding="utf-8") as f:
        json.dump(stocks, f, ensure_ascii=False, indent=2)

def load_users():
    with open(os.path.join(DATA_DIR, "users.json"), "r", encoding="utf-8") as f:
        return json.load(f)

# Türkçe karakter normalize etme
def normalize(text: str) -> str:
    replacements = {
        'ı': 'i', 'İ': 'I', 'ğ': 'g', 'Ğ': 'G',
        'ü': 'u', 'Ü': 'U', 'ş': 's', 'Ş': 'S',
        'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C'
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.lower()

def parse_order_item(item: str):
    match = re.match(r"(.+?)\s+(\d+(?:[.,]\d+)?)\s*([a-zA-ZçğıöşüÇĞİÖŞÜ]+)", item.strip())
    if not match:
        return normalize(item), 1.0, "adet"

    product = normalize(match.group(1).strip())
    amount = float(match.group(2).replace(",", "."))
    unit = match.group(3)
    return product, amount, unit

def get_order_status(order_id: str) -> str:
    orders = load_orders()
    order_id = str(order_id).strip()

    if order_id in orders:
        o = orders[order_id]
        takip = f"Takip No: {o['takip_no']}" if o.get('takip_no') else "Henüz kargo atanmadı."
        return (
            f"Sipariş #{order_id}\n"
            f"Müşteri: {o['musteri']}\n"
            f"Ürünler: {', '.join(o['urunler'])}\n"
            f"Durum: {o['durum']}\n"
            f"Kargo: {o.get('kargo_firmasi') or 'Atanmadı'}\n"
            f"{takip}\n"
            f"Tarih: {o['tarih']}"
        )

    for oid, o in orders.items():
        if o.get('takip_no') and o['takip_no'].upper() == order_id.upper():
            takip = f"Takip No: {o['takip_no']}"
            return (
                f"Sipariş #{oid}\n"
                f"Müşteri: {o['musteri']}\n"
                f"Ürünler: {', '.join(o['urunler'])}\n"
                f"Durum: {o['durum']}\n"
                f"Kargo: {o.get('kargo_firmasi') or 'Atanmadı'}\n"
                f"{takip}\n"
                f"Tarih: {o['tarih']}"
            )

    return f"'{order_id}' ile eşleşen sipariş bulunamadı. Lütfen sipariş numaranızı (örn: 128) kontrol edin."

def get_order_status_by_customer(order_id: str, username: str) -> str:
    orders = load_orders()
    users = load_users()
    order_id = str(order_id).strip()

    target_oid = None
    if order_id in orders:
        target_oid = order_id
    else:
        for oid, o in orders.items():
            if o.get('takip_no') and o['takip_no'].upper() == order_id.upper():
                target_oid = oid
                break

    if not target_oid:
        return f"'{order_id}' ile eşleşen sipariş bulunamadı. Lütfen sipariş numaranızı (örn: 128) kontrol edin."

    o = orders[target_oid]
    user_order_ids = users.get(username, {}).get("order_ids", [])
    if o.get("musteri_id") != username and target_oid not in user_order_ids:
        return "Bu siparişe erişim yetkiniz bulunmuyor. Lütfen kendi sipariş numaranızı girin."
    takip = f"Takip No: {o['takip_no']}" if o.get('takip_no') else "Henüz kargo atanmadı."
    return (
        f"Sipariş #{target_oid}\n"
        f"Ürünler: {', '.join(o['urunler'])}\n"
        f"Durum: {o['durum']}\n"
        f"Kargo: {o.get('kargo_firmasi') or 'Atanmadı'}\n"
        f"{takip}\n"
        f"Tarih: {o['tarih']}"
    )

def customer_can_access_order(order_id: str, username: str, order: dict) -> bool:
    users = load_users()
    user_order_ids = users.get(username, {}).get("order_ids", [])
    return order.get("musteri_id") == username or order_id in user_order_ids

def get_delivery_info(order_id: str) -> str:
    orders = load_orders()
    order_id = str(order_id).strip()
    if order_id not in orders:
        return f"'{order_id}' ile eşleşen sipariş bulunamadı."

    o = orders[order_id]
    durum = o.get("durum")
    kargo_durum = o.get("kargo_durum")
    kargo = o.get("kargo_firmasi") or "Henüz kargo firması atanmadı"
    takip = o.get("takip_no") or "Henüz takip numarası yok"
    tahmini_teslimat = o.get("tahmini_teslimat") or "Henüz netleşmedi"
    readable_shipping_status = {
        "yolda": "Sipariş yolda",
        "gecikme_riski": "Gecikme riski var",
        "teslim_edildi": "Teslim edildi",
        "iptal": "İptal edildi",
    }.get(kargo_durum, "Bilinmiyor")

    if durum == "iptal":
        return f"Sipariş #{order_id} iptal edildiği için teslimat beklenmiyor."
    if durum == "teslim edildi":
        return f"Sipariş #{order_id} teslim edilmiş görünüyor.\nTeslim tarihi: {tahmini_teslimat}"

    return (
        f"Sipariş #{order_id}\n"
        f"Not: {order_id} sayısal sipariş numarasıdır; kargo takip numarası aşağıdadır.\n"
        f"Durum: {durum}\n"
        f"Kargo durumu: {readable_shipping_status}\n"
        f"Kargo firması: {kargo}\n"
        f"Kargo takip no: {takip}\n"
        f"Tahmini teslimat: {tahmini_teslimat}"
    )

def get_delivery_info_by_customer(order_id: str, username: str) -> str:
    orders = load_orders()
    order_id = str(order_id).strip()
    if order_id not in orders:
        return f"'{order_id}' ile eşleşen sipariş bulunamadı."

    order = orders[order_id]
    if not customer_can_access_order(order_id, username, order):
        return "Bu siparişe erişim yetkiniz bulunmuyor. Lütfen kendi sipariş numaranızı girin."

    return get_delivery_info(order_id)

def check_stock(urun_adi: str) -> str:
    stocks = load_stocks()
    key = normalize(urun_adi.strip())
    found_key = None
    for k in stocks:
        if normalize(k) == key or k == urun_adi.lower():
            found_key = k
            break
    if not found_key:
        return f"'{urun_adi}' adlı ürün stokta bulunamadı. Mevcut ürünler: {', '.join(stocks.keys())}"
    s = stocks[found_key]
    durum = "⚠️ KRİTİK SEVİYE" if s['miktar'] <= s['esik'] else "✅ Yeterli"
    return (
        f"Ürün: {found_key}\n"
        f"Miktar: {s['miktar']} {s['birim']}\n"
        f"Eşik: {s['esik']} {s['birim']}\n"
        f"Fiyat: {s['fiyat']} TL/{s['birim']}\n"
        f"Durum: {durum}"
    )

def update_stock(urun_adi: str, miktar: str) -> str:
    stocks = load_stocks()
    key = normalize(urun_adi.strip())
    found_key = None
    for k in stocks:
        if normalize(k) == key:
            found_key = k
            break

    if not found_key:
        return f"'{urun_adi}' adlı ürün bulunamadı. Mevcut ürünler: {', '.join(stocks.keys())}"

    number_match = re.search(r"\d+(?:[.,]\d+)?", str(miktar))
    if not number_match:
        return "Stok miktarı sayı olmalı. Örn: 90"

    new_amount = float(number_match.group(0).replace(",", "."))
    old_amount = stocks[found_key]["miktar"]
    stocks[found_key]["miktar"] = int(new_amount) if new_amount.is_integer() else new_amount
    save_stocks(stocks)
    return f"{found_key} stoğu güncellendi: {old_amount} {stocks[found_key]['birim']} → {stocks[found_key]['miktar']} {stocks[found_key]['birim']}"

def list_low_stocks() -> str:
    stocks = load_stocks()
    kritik = [
        f"• {urun}: {s['miktar']} {s['birim']} (eşik: {s['esik']} {s['birim']}) — {s['fiyat']} TL"
        for urun, s in stocks.items()
        if s['miktar'] <= s['esik']
    ]
    if not kritik:
        return "✅ Tüm stoklar yeterli seviyede."
    return "⚠️ Kritik Stok Uyarısı:\n" + "\n".join(kritik)

def list_all_orders() -> str:
    orders = load_orders()
    durum_emoji = {
        "kargoda": "🚚",
        "hazırlanıyor": "📦",
        "teslim edildi": "✅",
        "iptal": "❌"
    }
    sonuc = []
    for oid, o in orders.items():
        emoji = durum_emoji.get(o['durum'], "•")
        urunler_str = ", ".join(o.get('urunler', []))
        sonuc.append(f"#{oid} {emoji} {o['musteri']} — İçerik: ({urunler_str}) — {o['durum']} ({o['tarih']})")
    
    return "📋 Tüm Siparişler:\n" + "\n".join(sonuc)

def list_shipping_alerts() -> str:
    orders = load_orders()
    alerts = []
    today = datetime.now().date()

    for oid, o in orders.items():
        if o.get("durum") in {"teslim edildi", "iptal"}:
            continue

        reasons = []
        if o.get("kargo_durum") == "gecikme_riski":
            reasons.append("gecikme riski")
        if o.get("durum") == "kargoda" and (not o.get("kargo_firmasi") or not o.get("takip_no")):
            reasons.append("kargo firma/takip bilgisi eksik")
        if o.get("tahmini_teslimat"):
            eta = datetime.strptime(o["tahmini_teslimat"], "%Y-%m-%d").date()
            if eta < today:
                reasons.append("tahmini teslim tarihi geçmiş")

        if reasons:
            alerts.append(f"#{oid} {o['musteri']} — {', '.join(reasons)}")

    if not alerts:
        return "Kargo tarafında acil uyarı görünmüyor."
    return "Kargo Uyarıları:\n" + "\n".join(alerts)

def get_fulfillment_tasks() -> str:
    orders = load_orders()
    tasks = []

    for oid, o in orders.items():
        if o.get("durum") == "hazırlanıyor":
            tasks.append(f"#{oid} depo: paket hazırlanacak ({', '.join(o['urunler'])})")
        elif o.get("durum") == "kargoda" and (not o.get("kargo_firmasi") or not o.get("takip_no")):
            tasks.append(f"#{oid} operasyon: kargo firma/takip bilgisi tamamlanacak ({o['musteri']})")

    if not tasks:
        return "Bugün için açık operasyon görevi görünmüyor."
    return "Bugünkü Operasyon Görevleri:\n" + "\n".join(tasks)

def suggest_restock() -> str:
    stocks = load_stocks()
    orders = load_orders()
    demand = {}

    for o in orders.values():
        if o.get("durum") == "iptal":
            continue
        for item in o.get("urunler", []):
            product, amount, unit = parse_order_item(item)
            demand.setdefault(product, {"amount": 0, "unit": unit})
            demand[product]["amount"] += amount

    suggestions = []
    for product, stock in stocks.items():
        normalized_product = normalize(product)
        sold_amount = demand.get(normalized_product, {"amount": 0})["amount"]
        
        if stock["miktar"] <= stock["esik"]:
            reorder_amount = max(stock["esik"] * 2 - stock["miktar"], sold_amount)
            suggestions.append(
                f"{product}: {stock['miktar']} {stock['birim']} kaldı, eşik {stock['esik']} {stock['birim']}. Önerilen yenileme: {round(reorder_amount, 1)} {stock['birim']}."
            )

    if not suggestions:
        return "Stoklar kritik eşiklerin üzerinde. Şu an acil yenileme önerisi yok."
    return "Stok Yenileme Önerileri:\n" + "\n".join(suggestions)

def draft_supplier_order() -> str:
    restock = suggest_restock()
    if "Önerilen yenileme" not in restock:
        return "Tedarikçiye gönderilecek acil sipariş taslağı oluşturulmadı; kritik yenileme ihtiyacı görünmüyor."

    return (
        "Tedarikçi Mail Taslağı:\n"
        "Merhaba,\n\n"
        "Aşağıdaki ürünler için stok yenileme talep ediyoruz:\n"
        f"{restock}\n\n"
        "Uygun teslim tarihi ve fiyat bilgisini paylaşabilir misiniz?\n\n"
        "Teşekkürler,\nJetKobi Operasyon"
    )

def get_sales_insights() -> str:
    orders = load_orders()
    stocks = load_stocks()
    totals = {}

    for o in orders.values():
        if o.get("durum") == "iptal":
            continue
        for item in o.get("urunler", []):
            product, amount, unit = parse_order_item(item)
            totals.setdefault(product, {"amount": 0, "unit": unit})
            totals[product]["amount"] += amount

    display_totals = {}
    for orig_name, stock_data in stocks.items():
        norm_name = normalize(orig_name)
        if norm_name in totals:
            display_totals[orig_name] = totals[norm_name]

    top = sorted(display_totals.items(), key=lambda row: row[1]["amount"], reverse=True)[:5]
    if not top:
        return "Analiz için yeterli satış verisi bulunamadı."

    lines = [f"{product}: {round(data['amount'], 1)} {data['unit']}" for product, data in top]
    return "Satış İçgörüleri:\nEn çok hareket gören ürünler:\n" + "\n".join(lines)

def update_order_status(order_id: str, new_status: str) -> str:
    valid_statuses = ["hazırlanıyor", "kargoda", "teslim edildi", "iptal"]
    if new_status not in valid_statuses:
        return f"Geçersiz durum. Kabul edilen değerler: {', '.join(valid_statuses)}"
    orders = load_orders()
    order_id = str(order_id).strip()
    if order_id not in orders:
        return f"{order_id} numaralı sipariş bulunamadı."
    old_status = orders[order_id]['durum']
    orders[order_id]['durum'] = new_status
    save_orders(orders)
    return f"✅ Sipariş #{order_id} durumu güncellendi: '{old_status}' → '{new_status}'"

def get_daily_report() -> str:
    orders = load_orders()
    stocks = load_stocks()
    today = datetime.now().strftime("%Y-%m-%d")

    total = len(orders)
    kargoda = sum(1 for o in orders.values() if o['durum'] == 'kargoda')
    hazirlaniyor = sum(1 for o in orders.values() if o['durum'] == 'hazırlanıyor')
    teslim = sum(1 for o in orders.values() if o['durum'] == 'teslim edildi')
    iptal = sum(1 for o in orders.values() if o['durum'] == 'iptal')

    kritik = [f"{urun} ({s['miktar']}/{s['esik']} {s['birim']})" 
              for urun, s in stocks.items() if s['miktar'] <= s['esik']]

    rapor = f"""📊 GÜNLÜK RAPOR — {today}
━━━━━━━━━━━━━━━━━━━━
📦 SİPARİŞ ÖZETI
Toplam: {total} sipariş
🚚 Kargoda: {kargoda}
📦 Hazırlanıyor: {hazirlaniyor}
✅ Teslim Edildi: {teslim}
❌ İptal: {iptal}

🌿 STOK DURUMU
Toplam ürün: {len(stocks)}
Kritik seviye: {len(kritik)} ürün"""

    if kritik:
        rapor += "\n⚠️ Acil: " + ", ".join(kritik)
    else:
        rapor += "\n✅ Tüm stoklar yeterli"

    rapor += "\n\n🚚 KARGO KONTROLÜ\n" + list_shipping_alerts()
    rapor += "\n\n🧾 GÖREVLER\n" + get_fulfillment_tasks()
    rapor += "\n\n🌱 STOK ÖNERİSİ\n" + suggest_restock()

    return rapor