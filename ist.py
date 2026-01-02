import requests
from bs4 import BeautifulSoup
import folium
from folium.plugins import HeatMap
import sqlite3
import random
import time
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

# --- 1. VERİTABANI ---
def veritabani_hazirla():
    conn = sqlite3.connect('istanbul_mega_v15.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS olaylar 
                      (baslik TEXT PRIMARY KEY, ilce TEXT, kategori TEXT, lat REAL, lng REAL, zaman TEXT, timestamp DATETIME)''')
    conn.commit()
    return conn

# İSTANBUL 39 İLÇE TAM LİSTE
konum_rehberi = {
    "Adalar": [40.8732, 29.1287], "Arnavutköy": [41.1833, 28.7333], "Ataşehir": [40.9847, 29.1067],
    "Avcılar": [40.9801, 28.7175], "Bağcılar": [41.0344, 28.8333], "Bahçelievler": [40.9958, 28.8611],
    "Bakırköy": [40.9781, 28.8744], "Başakşehir": [41.0981, 28.8033], "Bayrampaşa": [41.0471, 28.8984],
    "Beşiktaş": [41.0428, 29.0075], "Beykoz": [41.1177, 29.0985], "Beylikdüzü": [41.0039, 28.6375],
    "Beyoğlu": [41.0333, 28.9667], "Büyükçekmece": [41.0225, 28.5900], "Çatalca": [41.1436, 28.4611],
    "Çekmeköy": [41.0353, 29.2061], "Esenler": [41.0392, 28.8911], "Esenyurt": [41.0343, 28.6801],
    "Eyüpsultan": [41.0478, 28.9328], "Fatih": [41.0167, 28.9333], "Gaziosmanpaşa": [41.0583, 28.9142],
    "Güngören": [41.0253, 28.8725], "Kadıköy": [40.9911, 29.0272], "Kağıthane": [41.0833, 28.9833],
    "Kartal": [40.8894, 29.1844], "Küçükçekmece": [41.0017, 28.7733], "Maltepe": [40.9250, 29.1333],
    "Pendik": [40.8769, 29.2347], "Sancaktepe": [40.9903, 29.2333], "Sarıyer": [41.1667, 29.0500],
    "Silivri": [41.0744, 28.2481], "Sultanbeyli": [40.9669, 29.2667], "Sultangazi": [41.1042, 28.8617],
    "Şile": [41.1750, 29.6133], "Şişli": [41.0606, 28.9878], "Tuzla": [40.8167, 29.3000],
    "Ümraniye": [41.0333, 29.1000], "Üsküdar": [41.0267, 29.0150], "Zeytinburnu": [40.9833, 28.9000]
}

suc_rehberi = {
    "Cinayet": {"label": "💀", "color": "#FF0000", "desc": "Şiddetli Suçlar"},
    "Hırsızlık": {"label": "💰", "color": "#FFA500", "desc": "Mülkiyet Suçları"},
    "Saldırı": {"label": "👊", "color": "#FF4500", "desc": "Kavga / Yaralama"},
    "Kaza": {"label": "💥", "color": "#00BFFF", "desc": "Trafik Kazaları"},
    "Narkotik": {"label": "💊", "color": "#A020F0", "desc": "Narkotik Operasyonları"},
    "Asayiş": {"label": "🚨", "color": "#4682B4", "desc": "Genel Asayiş / Haber"}
}

def analiz_et(baslik):
    m = baslik.lower()
    if any(y in m for y in ["devriye", "denetim", "ziyaret", "ziyareti", "tebrik", "başarı", "atama"]): return None
    if any(k in m for k in ["cinayet", "ceset", "öldürüldü", "infaz"]): return "Cinayet"
    if any(k in m for k in ["hırsız", "soygun", "çaldı", "gasp", "kapkaç", "soyuldu", "hırsızlık"]): return "Hırsızlık"
    if any(k in m for k in ["kavga", "yaralandı", "silahlı", "vurdu", "çatışma", "kurşun", "saldırı"]): return "Saldırı"
    if any(k in m for k in ["kaza", "zincirleme", "trafik", "çarpıştı", "devrildi", "yaralı kaza"]): return "Kaza"
    if any(k in m for k in ["uyuşturucu", "narkotik", "operasyon", "şafak", "torbacı", "ele geçirildi"]): return "Narkotik"
    return "Asayiş"

def veri_cek():
    conn = veritabani_hazirla()
    cursor = conn.cursor()
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # Tüm İstanbul geneli tarama kelimeleri
    sorgular = ["istanbul+asayiş", "istanbul+son+dakika+haber", "istanbul+hırsızlık", "istanbul+silahlı+kavga"]
    
    for s in sorgular:
        try:
            url = f"https://news.google.com/rss/search?q={s}+when:72h&hl=tr&gl=TR&ceid=TR:tr"
            res = requests.get(url, headers=headers, timeout=12)
            soup = BeautifulSoup(res.content, "lxml-xml")
            for item in soup.find_all('item'):
                baslik = item.title.text
                kat = analiz_et(baslik)
                if kat:
                    for ilce, koord in konum_rehberi.items():
                        if ilce.lower() in baslik.lower():
                            try:
                                lat, lng = koord[0] + random.uniform(-0.015, 0.015), koord[1] + random.uniform(-0.015, 0.015)
                                # Kaydedirken tam zamanı ve o anki saati alıyoruz
                                cursor.execute("INSERT INTO olaylar (baslik, ilce, kategori, lat, lng, zaman, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                             (baslik, ilce, kat, lat, lng, datetime.now().strftime('%H:%M'), datetime.now()))
                            except: continue
        except: continue
    
    conn.commit()
    conn.close()

def harita_yap():
    conn = sqlite3.connect('istanbul_mega_v15.db')
    cursor = conn.cursor()
    
    # 72 SAATLİK FİLTRELEME (3 GÜN)
    zaman_siniri = datetime.now() - timedelta(hours=72)
    cursor.execute("SELECT * FROM olaylar WHERE timestamp > ?", (zaman_siniri,))
    veriler = cursor.fetchall()
    
    m = folium.Map(location=[41.0082, 28.9784], zoom_start=11, tiles="CartoDB dark_matter")
    
    # Isı Haritası
    if veriler:
        HeatMap([[v[3], v[4]] for v in veriler], radius=22, blur=18, min_opacity=0.35).add_to(m)

    # SAĞ ÜST MODERN PANEL
    lejant_html = f'''
    <div style="position: fixed; top: 20px; right: 20px; width: 250px; z-index:9999; 
                background: rgba(10,10,10,0.9); color: white; padding: 15px; border-radius: 15px; 
                border: 2px solid #e74c3c; font-family: sans-serif; box-shadow: 0 0 20px rgba(231,76,60,0.3);">
        <h4 style="margin:0 0 10px 0; text-align:center; color:#e74c3c;">🚨 Mega City 72H Report</h4>
        <div style="background:#222; text-align:center; padding:8px; border-radius:10px; margin-bottom:12px; border: 1px solid #444;">
            <b style="font-size:16px;">Aktif Vaka: {len(veriler)}</b><br>
            <small style="color:#aaa;">Son 3 Günlük Analiz</small>
        </div>
    '''
    for k, v in suc_rehberi.items():
        lejant_html += f'<div style="margin:6px 0; font-size:11px;">{v["label"]} <b>{k}:</b> {v["desc"]}</div>'
    lejant_html += '</div>'
    m.get_root().html.add_child(folium.Element(lejant_html))

    for v in veriler:
        baslik, ilce, kat, lat, lng, saat, _ = v
        stil = suc_rehberi.get(kat, {"label": "🚨", "color": "white"})
        
        popup_content = f'''
        <div style="width: 320px; font-family: sans-serif; display: flex; align-items: center; gap: 12px; padding: 8px;">
            <div style="font-size: 40px; filter: drop-shadow(0 0 5px {stil['color']});">{stil['label']}</div>
            <div style="flex: 1;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h4 style="margin: 0; color: {stil['color']}; font-size: 15px;">{kat}</h4>
                    <span style="font-size: 10px; color: #888;">🕒 {saat}</span>
                </div>
                <p style="margin: 3px 0; font-size: 12px; font-weight: bold; color: #333;">{ilce}</p>
                <p style="margin: 0; font-size: 11px; line-height: 1.3; color: #555;">{baslik}</p>
                <div style="margin-top: 8px; font-size: 9px; color: #e74c3c; text-align: right; font-weight:bold;">LIVE TRACKING</div>
            </div>
        </div>
        '''
        
        icon_html = f'''<div style="font-size: 24px; filter: drop-shadow(0 0 8px {stil['color']}); cursor: pointer;">{stil['label']}</div>'''
        
        folium.Marker(
            location=[lat, lng],
            popup=folium.Popup(popup_content, max_width=350),
            icon=folium.DivIcon(html=icon_html)
        ).add_to(m)

    m.save("istanbul_mega_city_72h.html")
    print(f"📊 72 Saatlik Mega Analiz Hazır! ({len(veriler)} Vaka)")
    conn.close()

# ANA ÇALIŞTIRICI (GitHub Actions için uyumlu hale getirildi)
if __name__ == "__main__":
    print("🚀 Veri toplama başlatıldı...")
    veri_cek()  # İsmin tam olarak böyle olduğundan emin ol
    print("📊 Harita üretiliyor...")
    harita_yap()
    print("✅ İşlem tamamlandı.")

