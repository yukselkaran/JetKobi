# ⚡ JetKobi — Akıllı KOBİ Operasyon Asistanı

> Doğal dille yaz. AI yorumlasın. İşlem tamamlansın.

JetKobi; küçük ve orta ölçekli işletmelerin sipariş takibini, stok yönetimini, kargo kontrolünü ve günlük operasyonlarını **yapay zeka ajanı üzerinden** yönetmesini sağlayan çalışan bir prototiptir.

---

## 🧠 Nasıl Çalışır?

Kullanıcı doğal dille yazar. AI ajanı mesajın niyetini çözümler, doğru aracı seçip çağırır, gerçek veriye ulaşır ve bağlama uygun Türkçe bir yanıt üretir.

```
Kullanıcı  →  "128 numaralı siparişim ne zaman gelir?"
AI kararı  →  CALL: get_delivery_info(order_id='128')
Tool       →  Sipariş + kargo verisi döner
AI yanıtı  →  "Siparişiniz kargoda, MNG Kargo ile yolda. Tahmini teslimat: 13 Mayıs 2026."
```

Kod tarafı hiçbir cevap üretmez. Sadece AI'ın seçtiği aracı güvenle çalıştırır.

---

## 🗂️ Proje Yapısı

```
jetkobi/
├── main.py               # FastAPI — login, session, rol kontrolü
├── agent.py              # LLM tabanlı ajan orkestrasyonu
├── tools.py              # Sipariş, stok ve kargo araçları
├── templates/
│   └── index.html        # Web chat arayüzü
└── data/
    ├── orders.json       # Sipariş verileri
    ├── stocks.json       # Stok verileri
    └── users.json        # Kullanıcı verileri
```

---

## 🔐 Giriş Bilgileri

| Kullanıcı | Şifre | Rol    |
|-----------|-------|--------|
| `kobi`    | `123` | KOBİ yöneticisi |
| `ahmet`   | `456` | Müşteri |
| `ayse`    | `789` | Müşteri |
| `mehmet`  | `321` | Müşteri |
| `fatma`   | `654` | Müşteri |

> **KOBİ** hesabı tüm araçlara ve yönetim paneline erişebilir.  
> **Müşteri** hesapları yalnızca kendi siparişlerini görebilir.

---

## 🤖 AI Ajanının Kullanabileceği Araçlar

| Araç | Açıklama |
|------|----------|
| `get_order_status(order_id)` | Sipariş detayı sorgular |
| `get_delivery_info(order_id)` | Kargo, takip no ve teslimat bilgisi döner |
| `check_stock(urun_adi)` | Tek ürünün stok durumunu gösterir |
| `list_low_stocks()` | Kritik seviyedeki stokları listeler |
| `list_all_orders()` | Tüm siparişleri listeler |
| `list_shipping_alerts()` | Gecikme riski veya eksik kargo bilgisi olan siparişleri bulur |
| `get_fulfillment_tasks()` | Günün depo ve operasyon görevlerini çıkarır |
| `suggest_restock()` | Satış verisine göre stok yenileme önerir |
| `draft_supplier_order()` | Tedarikçiye gönderilecek sipariş maili taslağı oluşturur |
| `get_sales_insights()` | En çok satan ürünleri analiz eder |
| `update_order_status(order_id, new_status)` | Sipariş durumunu günceller |
| `update_stock(urun_adi, miktar)` | Stok miktarını günceller |
| `get_daily_report()` | Kapsamlı günlük operasyon raporu üretir |

---

## 💬 Demo Mesajları

### Müşteri olarak deneyin:
```
128 numaralı siparişim ne zaman gelir?
Siparişim nerede?
Domates stokta var mı?
```

### KOBİ olarak deneyin:
```
Sabah raporunu hazırla
Kargo gecikmesi olan siparişler var mı?
Bugün hangi operasyon görevleri var?
Domates stok miktarını 90 kg yap
Tedarikçiye stok yenileme maili hazırla
Satış içgörülerini göster
128 numaralı siparişi teslim edildi yap
```

---

## 🏆 Kapsanan Başlıklar

1. **Müşteri iletişiminin otomasyonu** — Sipariş ve stok sorularına doğal dille anında cevap
2. **Ürün ve sipariş takibi** — Sipariş durumu ve tüm sipariş listesi
3. **Kargo süreçlerinin yönetimi** — Takip numarası, gecikme riski, tahmini teslimat
4. **Stok ve envanter yönetimi** — Kritik stok tespiti, güncelleme, yenileme önerisi
5. **İş akışı ve görev yönetimi** — Günlük rapor ve operasyon görev listesi
6. **Analitik ve içgörü** — Satış trendleri ve en çok hareket eden ürünler

---

## ⚙️ Kurulum

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

`.env` dosyası oluşturun:

```env
HUGGINGFACE_API_KEY=your_key_here
```

---

## 🚀 Çalıştırma

```bash
uvicorn main:app --reload
```

Tarayıcıdan açın:

```
http://127.0.0.1:8000
```

---

## 🛠️ Teknoloji Yığını

- **Backend:** FastAPI + Python
- **AI Model:** Qwen/Qwen2.5-7B-Instruct (Hugging Face Inference API)
- **Ajan Mimarisi:** Tool-calling + 2-tur LLM pipeline (niyet tespiti → yanıt üretimi)
- **Veri Katmanı:** JSON dosyaları (orders, stocks, users)
- **Frontend:** Saf HTML/CSS/JS — çerçeve yok, bağımlılık yok