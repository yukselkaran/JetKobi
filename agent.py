import os
import re
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from tools import (
    get_order_status, get_order_status_by_customer,
    check_stock, list_low_stocks, list_all_orders,
    update_order_status, get_daily_report,
    get_delivery_info, get_delivery_info_by_customer,
    update_stock, list_shipping_alerts, get_fulfillment_tasks,
    suggest_restock, draft_supplier_order, get_sales_insights
)

load_dotenv()

# 🔥 MODEL DÜŞÜRÜLDÜ: Daha hızlı ve prompt'a daha sadık (7B)
client = InferenceClient(
    model="Qwen/Qwen2.5-7B-Instruct",
    api_key=os.getenv("HUGGINGFACE_API_KEY")
)

# ─────────────────────────────────────────────
# SYSTEM PROMPTS
# ─────────────────────────────────────────────

KOBI_SYSTEM = """### ROL VE GÖREV
Sen JetKobi'nin yapay zeka destekli KOBİ operasyon ajanısın.
Temel görevin; işletme sahibinin doğal dildeki mesajlarını anlamak, niyetini belirlemek ve gerektiğinde sistem araçlarını kullanarak operasyonları yönetmektir.

### KULLANILABİLİR ARAÇLAR (TOOLS)
- get_order_status(order_id='...')         → Sipariş detayı sorgulama.
- get_delivery_info(order_id='...')        → Kargo, takip ve teslimat bilgisi sorgulama.
- check_stock(urun_adi='...')              → Tek bir ürünün stok durumunu kontrol etme.
- list_low_stocks()                        → Kritik seviyedeki stokları listeleme.
- list_all_orders()                        → Tüm siparişleri listeleme.
- list_shipping_alerts()                   → Gecikme riski olan veya kargo bilgisi eksik siparişleri bulma.
- get_fulfillment_tasks()                  → Depo ve operasyon görevlerini listeleme.
- suggest_restock()                        → Satış verisine göre stok yenileme önerisi sunma.
- draft_supplier_order()                   → Tedarikçiye gönderilecek stok siparişi mail taslağını oluşturma.
- get_sales_insights()                     → Satış trendlerini ve en çok hareket gören ürünleri analiz etme.
- update_order_status(order_id='...', new_status='...') → Siparişin durumunu güncelleme.
- update_stock(urun_adi='...', miktar='...') → Ürün stok miktarını güncelleme.
- get_daily_report()                       → Günlük genel operasyon raporu oluşturma.

### KESİN KURALLAR VE DAVRANIŞ BİÇİMİ
1. VERİ VE İŞLEM ZORUNLULUĞU: İşletme verisi gerektiren veya işlem yapılmasını isteyen komutlarda
   ASLA hafızadan tahminde bulunma. MUTLAKA uygun aracı çağır.
2. ARAÇ ÇAĞIRMA FORMATI: Bir araç çağıracağın zaman YALNIZCA şu formatı kullan, öncesinde veya
   sonrasında hiçbir şey yazma:
   CALL: fonksiyon_adi(parametre='deger')
3. SOHBET VE SELAMLAŞMA: Kullanıcı sadece hal hatır soruyorsa ('merhaba', 'nasılsın', 'günaydın' vb.)
   KESİNLİKLE araç çağırma. İşletmeci diliyle nazikçe yanıt ver ve nasıl yardımcı olabileceğini sor.
4. ERİŞİM REDDİ SONRASI: Sistem "erişim yetkiniz yok" veya benzer bir ret mesajı döndürürse,
   bu mesajı kullanıcıya nazikçe ilet ve YENİ bir CALL üretme.
5. EKSİK VERİ: Sistem bir sipariş/ürün için veri bulamazsa "bilgi bulunamadı" diyerek bitir;
   tahmin veya varsayım ekleme.

### BAĞLAM VE DOĞAL DİL ANLAYIŞI
- Sipariş numarası çıkarımı: "128 ne zaman gelir?" → order_id='128', get_delivery_info çağır.
- Kısa cevaplar: "hazırla", "evet", "tamam" → konuşma geçmişine bakarak niyet belirle.
- Spesifik takip: Az önce #128 konuşulduysa "gecikme yok değil mi?" → get_delivery_info(order_id='128').
- Genel takip: Sadece "Tüm siparişlerde gecikme var mı?" gibi açık genel soru → list_shipping_alerts.
- FALLBACK KURALI: Kullanıcı veriye dayalı bir soru soruyor ve elinde araç sonucu yoksa
  MUTLAKA bir CALL üret. Asla tahminde bulunma, asla boş cevap verme."""

CUSTOMER_SYSTEM = """### ROL VE GÖREV
Sen JetKobi'nin yapay zeka destekli müşteri destek ajanısın.
Temel görevin; müşterilerin sipariş ve kargo sorularını SADECE sistem verisine dayanarak yanıtlamaktır.

### KRİTİK KURAL (EN ÖNEMLİSİ)
- ASLA tarih, durum, kargo bilgisi UYDURMA
- SADECE araçtan gelen veriyi kullan
- Veri yoksa "Bu sipariş için bilgi bulunamadı." de
- "erişim yetkiniz yok" mesajı gelirse nazikçe ilet ve YENİ CALL üretme

### İZİNLİ ARAÇLAR
- get_order_status(order_id='...')
- get_delivery_info(order_id='...')
- check_stock(urun_adi='...')

### KESİN KURALLAR
1. Sipariş/kargo sorusu varsa → MUTLAKA tool çağır
2. Tool çağırmadan asla cevap yazma
3. Aynı sipariş için tekrar sorulursa → tekrar tool çağır (hafızadan cevap verme)
4. Tahmini tarih ASLA üretme → sadece tool'dan geleni kullan
5. FALLBACK: Veriye dayalı soru var, elinde sonuç yoksa → MUTLAKA CALL üret

### NUMARA YORUMLAMA
- "128 benim numaram" → order_id = 128
- "MNG123456" → kargo takip kodu olabilir, sipariş numarası değil → kullanıcıdan sipariş numarası iste

### ÜSLUP
- Profesyonel, kısa, net
- "kargonuz", "siparişiniz" kullan
- Bozuk Türkçe YASAK

### ARAÇ ÇAĞIRMA FORMATI
CALL: fonksiyon_adi(parametre='deger')"""


# ─────────────────────────────────────────────
# DIRECT ACTION LAYER (LLM Bypass Motoru)
# ─────────────────────────────────────────────
def try_direct_action(user_message: str, user_role: str, username: str):
    """LLM'i atlayarak %100 doğrulukla doğrudan işlem yapan kural motoru."""
    msg = user_message.lower()

    # Stok Güncelleme Yakalayıcı
    match = re.search(r"(domates|biber|patlıcan|salatalık|kabak).*?(\d+)", msg)
    if match and any(k in msg for k in ["düşür", "artır", "arttır", "güncelle", "yap", "değiştir"]):
        urun = match.group(1)
        miktar = match.group(2)
        return execute_tool("update_stock", {
            "urun_adi": urun,
            "miktar": miktar
        }, user_role, username)

    # Sipariş Durumu Güncelleme Yakalayıcı
    match = re.search(r"(\d+).*?(teslim|iptal|hazırlandı|hazırla)", msg)
    if match and "sipariş" in msg:
        oid = match.group(1)

        if "teslim" in msg:
            status = "teslim edildi"
        elif "iptal" in msg:
            status = "iptal edildi"
        else:
            status = "hazırlandı"

        return execute_tool("update_order_status", {
            "order_id": oid,
            "new_status": status
        }, user_role, username)

    return None


# ─────────────────────────────────────────────
# TOOL PARSING
# ─────────────────────────────────────────────

def parse_tool_call(ai_msg: str):
    """CALL: satırından fonksiyon adı ve parametreleri ayıklar."""
    match = re.search(r"CALL:\s*(\w+)\(([^)]*)\)", ai_msg, re.IGNORECASE | re.DOTALL)
    if not match:
        return None, {}

    func_name = match.group(1)
    params_str = match.group(2)

    params = dict(re.findall(r"(\w+)=['\"]([^'\"]*)['\"]", params_str))
    for key, value in re.findall(r"(\w+)=([^\s,'\")]+)", params_str):
        params.setdefault(key, value)

    if "order_id" in params:
        raw_id = params["order_id"]
        found_nums = re.findall(r'\d+', raw_id)
        if found_nums:
            params["order_id"] = found_nums[0]

    return func_name, params


# ─────────────────────────────────────────────
# TOOL EXECUTION (Cache + Mutation Koruması)
# ─────────────────────────────────────────────

order_cache: dict = {}

MUTATION_TOOLS = {"update_stock", "update_order_status"}

KOBI_ONLY_TOOLS = {
    "list_low_stocks", "list_all_orders", "update_order_status",
    "get_daily_report", "update_stock", "list_shipping_alerts",
    "get_fulfillment_tasks", "suggest_restock", "draft_supplier_order",
    "get_sales_insights"
}


def execute_tool(func_name: str, params: dict, user_role: str, username: str) -> str:
    """Güvenli araç yürütücü — cache destekli ve mutation korumalı."""

    if func_name in MUTATION_TOOLS:
        order_cache.clear()
    else:
        cache_key = f"{func_name}:{params}:{user_role}:{username}"
        if cache_key in order_cache:
            return order_cache[cache_key]

    if func_name in KOBI_ONLY_TOOLS and user_role != "KOBİ":
        return "Üzgünüm, bu veriye erişim yetkiniz bulunmuyor."

    result = f"Bilinmeyen araç: {func_name}"

    if func_name == "get_order_status":
        order_id = params.get("order_id", "")
        if not order_id:
            result = "Sipariş numarası algılanamadı. Lütfen sadece rakam içeren bir numara belirtin."
        else:
            result = (
                get_order_status(order_id)
                if user_role == "KOBİ"
                else get_order_status_by_customer(order_id, username)
            )

    elif func_name == "get_delivery_info":
        order_id = params.get("order_id", "")
        if not order_id:
            result = "Sipariş numarası algılanamadı. Lütfen sipariş numaranızı belirtin."
        else:
            result = (
                get_delivery_info(order_id)
                if user_role == "KOBİ"
                else get_delivery_info_by_customer(order_id, username)
            )

    elif func_name == "check_stock":
        urun = params.get("urun_adi", "")
        result = check_stock(urun) if urun else "Ürün adı belirtilmedi."

    elif func_name == "list_low_stocks":
        result = list_low_stocks()

    elif func_name == "list_all_orders":
        result = list_all_orders()

    elif func_name == "list_shipping_alerts":
        result = list_shipping_alerts()

    elif func_name == "get_fulfillment_tasks":
        result = get_fulfillment_tasks()

    elif func_name == "suggest_restock":
        result = suggest_restock()

    elif func_name == "draft_supplier_order":
        result = draft_supplier_order()

    elif func_name == "get_sales_insights":
        result = get_sales_insights()

    elif func_name == "update_order_status":
        oid = params.get("order_id", "")
        stat = params.get("new_status", "")
        result = update_order_status(oid, stat) if (oid and stat) else "Eksik bilgi: sipariş numarası veya yeni durum belirtilmedi."

    elif func_name == "update_stock":
        urun = params.get("urun_adi", "")
        miktar = params.get("miktar", "")
        result = update_stock(urun, miktar) if (urun and miktar) else "Ürün adı veya miktar eksik."

    elif func_name == "get_daily_report":
        result = get_daily_report()

    if func_name not in MUTATION_TOOLS:
        cache_key = f"{func_name}:{params}:{user_role}:{username}"
        order_cache[cache_key] = result

    return result


# ─────────────────────────────────────────────
# FINAL RESPONSE BUILDER
# ─────────────────────────────────────────────

def build_final_messages(system_prompt: str, conversation_messages: list, tool_result: str) -> list:
    return [
        {"role": "system", "content": system_prompt},
        *conversation_messages,
        {
            "role": "user",
            "content": f"""SİSTEM VERİSİ:
{tool_result}

GÖREV: Bu veriyi kullanarak kullanıcıya cevap ver.

KRİTİK KURALLAR:
- Sadece yukarıdaki veriyi kullan; veride olmayan hiçbir bilgiyi ekleme.
- Tarih değiştirme, yeni tarih üretme. "11 Mayıs" yazıyorsa aynen yaz.
- Sistem "erişim yetkiniz yok" veya benzeri ret mesajı döndürdüyse, bunu nazikçe kullanıcıya ilet ve ASLA yeni CALL üretme.
- "Bu sipariş için bilgi bulunamadı." durumunda tahminde bulunma.

FORMAT:
- Kısa ve net
- Emoji kullanabilirsin
- Kesinlikle liste yapısı kullan ve HER BİR siparişi/kişiyi mutlaka YENİ BİR SATIRA (alt alta) yaz. Yan yana dizme.

YASAK:
- CALL yazmak
- Tahmin yapmak
- "görünüyor olabilir", "tahminen" gibi ifadeler
- Önceki cevaptan farklı bilgi üretmek

Cevabı üret."""
        }
    ]


# ─────────────────────────────────────────────
# MAIN AGENT
# ─────────────────────────────────────────────

def run_agent(
    user_message: str,
    user_role: str = "Müşteri",
    username: str = "musteri",
    history: list = None
) -> str:
    # ── DIRECT ACTION LAYER (LLM'den önce %100 Kesin İşlem) ──
    direct_result = try_direct_action(user_message, user_role, username)
    if direct_result:
        return f"✅ İşlem Hızlıca Tamamlandı:\n{direct_result}"

    system_prompt = KOBI_SYSTEM if user_role == "KOBİ" else CUSTOMER_SYSTEM

    conversation_messages = (history or [])[-8:] + [{"role": "user", "content": user_message}]

    messages = [
        {"role": "system", "content": system_prompt},
        *conversation_messages,
    ]

    try:
        # ── 1. TUR: Niyet tespiti (Temperature=0.2 ile daha stabil) ──
        response = client.chat_completion(
            messages=messages, 
            max_tokens=500,
            temperature=0.2
        )
        ai_msg = response.choices[0].message.content

        # 🔥 CALL ZORLAMA FIX: Veri sorusu var ama CALL atmadıysa zorla
        data_keywords = ["sipariş", "kargo", "stok", "ürün", "ne zaman", "durum"]
        if "CALL:" not in ai_msg.upper():
            if any(k in user_message.lower() for k in data_keywords):
                return "İşlem veya veri talebi algılandı ancak gerçekleştirilemedi. Lütfen miktarı veya numarayı belirterek tekrar yazın."
            return ai_msg

        func_name, params = parse_tool_call(ai_msg)
        if not func_name:
            return ai_msg

        # ── 2. ARAÇ ÇAĞRISI ──
        tool_result = execute_tool(func_name, params, user_role, username)

        # ── 3. TUR: Son yanıtı üret ──
        final_response = client.chat_completion(
            messages=build_final_messages(system_prompt, conversation_messages, tool_result),
            max_tokens=500,
            temperature=0.2
        )
        final_msg = final_response.choices[0].message.content

        if "CALL:" in final_msg.upper():
            cleaned = re.sub(r"CALL:\s*\w+\([^)]*\)", "", final_msg, flags=re.IGNORECASE).strip()
            return cleaned if cleaned else "İşlem tamamlandı. Başka bir konuda yardımcı olabilir miyim?"

        return final_msg

    except Exception as e:
        print(f"[Agent Hatası] {e}")
        return "Şu an sistemde kısa süreli bir aksaklık var, lütfen birazdan tekrar deneyin."