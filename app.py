import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone

st.set_page_config(
    page_title="Isparta Afet Yönetim ve Karar Destek Paneli",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# Theme / presentation
# -----------------------------
st.markdown("""
<style>
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    .hero {
        padding: 1.4rem 1.6rem; border-radius: 16px;
        background: linear-gradient(115deg,#10243a,#1d4962);
        color: white; margin-bottom: 1rem;
    }
    .hero h1 {color:white; margin:0 0 .35rem 0; font-size:2rem;}
    .hero p {color:#d8e7f1; margin:0; font-size:1rem;}
    .small-note {color:#64748b; font-size:.85rem;}
    div[data-testid="stMetric"] {
        background:#f6f8fb; border:1px solid #e5eaf0;
        padding:12px 14px; border-radius:12px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Synthetic dataset
# -----------------------------
@st.cache_data
def create_data(n=1000, seed=42):
    rng = np.random.default_rng(seed)
    categories = np.array(["Deprem", "Sel", "Heyelan", "Orman Yangını", "Altyapı"])
    probs = [0.30, 0.22, 0.14, 0.14, 0.20]
    cat = rng.choice(categories, size=n, p=probs)
    severity = rng.choice([1,2,3,4,5], size=n, p=[.08,.17,.30,.28,.17])
    lat = np.clip(rng.normal(37.7648, .085, n), 37.35, 38.15)
    lon = np.clip(rng.normal(30.5566, .105, n), 29.95, 31.25)
    pop = np.clip(rng.lognormal(4.7, 1.0, n).astype(int), 5, 5000)
    infra = rng.choice([0,1,2,3,4,5], size=n, p=[.10,.15,.20,.25,.20,.10])
    teams = np.array(["Saha Ekibi Alpha","Saha Ekibi Bravo",
                      "Saha Ekibi Charlie","Saha Ekibi Delta"])
    device = rng.choice(teams, size=n)
    now = datetime.now(timezone.utc)
    age_h = rng.uniform(0, 72, n)
    timestamps = [now - timedelta(hours=float(x)) for x in age_h]
    descriptions = {
        "Deprem":"Deprem sonrası yapı ve çevre gözlemi",
        "Sel":"Su baskını ve ulaşım etkisi gözlemi",
        "Heyelan":"Zemin hareketi ve yol güvenliği gözlemi",
        "Orman Yangını":"Yangın ve çevresel etki gözlemi",
        "Altyapı":"Enerji, su veya iletişim altyapısı gözlemi"
    }
    df = pd.DataFrame({
        "record_id":[f"ISPARTA-{i+1:05d}" for i in range(n)],
        "timestamp":timestamps,
        "device_id":device,
        "latitude":lat,
        "longitude":lon,
        "category":cat,
        "severity":severity,
        "population_affected":pop,
        "infrastructure_damage":infra,
        "description":[descriptions[x] for x in cat],
        "evidence_status":rng.choice(["Fotoğraf var","Fotoğraf yok"], n, p=[.72,.28]),
        "sync_status":rng.choice(["Senkronize","Bekliyor"], n, p=[.94,.06])
    })
    # Calibrated illustrative 0-100 score: severity max 50, population max 30,
    # infrastructure max 20. This avoids saturating almost every record at 100.
    df["risk_score"] = (
        df["severity"]*10
        + np.minimum(df["population_affected"]/1000,1)*30
        + df["infrastructure_damage"]*4
    ).clip(0,100).round(1)
    df["risk_level"] = pd.cut(
        df["risk_score"], [-1,40,60,80,101],
        labels=["Düşük","Orta","Yüksek","Kritik"]
    ).astype(str)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df

data = create_data()

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("🛰️ Afet Yönetim Paneli")
st.sidebar.caption("Isparta • Eğitim ve prototip ortamı")
page = st.sidebar.radio(
    "Bölüm seç",
    ["Genel Bakış", "Harita ve Olaylar", "Risk Analizi",
     "Sistem Nasıl Çalışır?", "Veri ve Varsayımlar"]
)
st.sidebar.divider()
st.sidebar.subheader("Filtreler")
selected_categories = st.sidebar.multiselect(
    "Afet türü", sorted(data["category"].unique()),
    default=sorted(data["category"].unique())
)
selected_risks = st.sidebar.multiselect(
    "Risk seviyesi", ["Kritik","Yüksek","Orta","Düşük"],
    default=["Kritik","Yüksek","Orta","Düşük"]
)
min_severity, max_severity = st.sidebar.slider(
    "Şiddet aralığı", 1, 5, (1,5)
)
filtered = data[
    data["category"].isin(selected_categories)
    & data["risk_level"].isin(selected_risks)
    & data["severity"].between(min_severity,max_severity)
].copy()

st.sidebar.divider()
st.sidebar.caption("Veri kümesi: 1.000 sentetik kayıt")
st.sidebar.caption("Konum: Isparta çevresi (yaklaşık koordinatlar)")

# -----------------------------
# Shared helpers
# -----------------------------
def metric_row(frame):
    total = len(frame)
    critical = int((frame["risk_level"]=="Kritik").sum())
    high = int((frame["risk_level"]=="Yüksek").sum())
    affected = int(frame["population_affected"].sum())
    avg = float(frame["risk_score"].mean()) if total else 0
    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Filtrelenmiş kayıt", f"{total:,}")
    c2.metric("Kritik olay", f"{critical:,}")
    c3.metric("Yüksek risk", f"{high:,}")
    c4.metric("Etkilenen nüfus*", f"{affected:,}")
    c5.metric("Ortalama risk", f"{avg:.1f}/100")

def risk_color_map():
    return {"Kritik":"#b91c1c","Yüksek":"#ea580c",
            "Orta":"#d4a017","Düşük":"#15803d"}

# -----------------------------
# Header
# -----------------------------
st.markdown("""
<div class="hero">
  <h1>ISPARTA AFET YÖNETİM VE KARAR DESTEK PANELİ</h1>
  <p>Çevrimdışı saha veri toplama • Senkronizasyon • Coğrafi risk analizi • Önceliklendirme</p>
</div>
""", unsafe_allow_html=True)

st.warning(
    "PROTOTİP UYARISI — Bu panel sentetik/test verileri kullanır. "
    "Gerçek afet bildirimi, AFAD verisi veya operasyonel karar sistemi değildir. "
    "Haritadaki noktalar gerçek olay konumlarını göstermez."
)

if page == "Genel Bakış":
    st.subheader("Yönetici Özeti")
    st.write(
        "Bu prototip, afet sahasındaki ekiplerin internet bağlantısı olmadan "
        "kayıt oluşturabilmesini; bağlantı geldiğinde kayıtların merkezi sisteme "
        "aktarılmasını ve karar vericilerin olayları risk önceliğine göre "
        "inceleyebilmesini göstermek amacıyla hazırlanmıştır."
    )
    metric_row(filtered)
    left,right = st.columns([1.15,1])
    with left:
        counts = filtered["category"].value_counts().rename_axis("Afet türü").reset_index(name="Kayıt")
        fig = px.bar(counts, x="Afet türü", y="Kayıt", color="Afet türü",
                     title="Afet Türlerine Göre Kayıt Dağılımı")
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        risk_counts = filtered["risk_level"].value_counts().reindex(
            ["Kritik","Yüksek","Orta","Düşük"], fill_value=0
        ).rename_axis("Risk").reset_index(name="Kayıt")
        fig = px.pie(risk_counts, names="Risk", values="Kayıt",
                     hole=.48, title="Risk Seviyesi Dağılımı",
                     color="Risk", color_discrete_map=risk_color_map())
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Öncelikli İnceleme Gerektiren Kayıtlar")
    top = filtered.sort_values("risk_score", ascending=False).head(10)
    st.dataframe(
        top[["record_id","category","risk_level","risk_score","severity",
             "population_affected","infrastructure_damage","device_id"]],
        use_container_width=True, hide_index=True
    )
    st.caption("*Etkilenen nüfus alanı sentetik kayıtların toplamıdır; benzersiz kişi sayısı değildir.")

elif page == "Harita ve Olaylar":
    st.subheader("Coğrafi Olay Görünümü")
    st.write("Harita noktaları sentetik koordinatlardan üretilmiştir; gerçek olay yeri değildir.")
    if len(filtered):
        fig = px.scatter_map(
            filtered, lat="latitude", lon="longitude",
            color="risk_level", size="severity",
            hover_name="record_id",
            hover_data=["category","risk_score","population_affected",
                        "infrastructure_damage","device_id"],
            color_discrete_map=risk_color_map(),
            zoom=8, height=650,
            map_style="open-street-map",
            title="Isparta Çevresi — Sentetik Olay Noktaları"
        )
        fig.update_layout(margin=dict(l=0,r=0,t=45,b=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Seçilen filtrelere uygun kayıt bulunamadı.")
    st.subheader("Olay Kayıtları")
    st.dataframe(
        filtered.sort_values("timestamp",ascending=False),
        use_container_width=True, hide_index=True
    )
    csv = filtered.to_csv(index=False).encode("utf-8-sig")
    st.download_button("Filtrelenmiş kayıtları CSV indir",
                       csv, "isparta_filtrelenmis_kayitlar.csv", "text/csv")

elif page == "Risk Analizi":
    st.subheader("Risk Analizi ve Kaynak Önceliklendirme")
    metric_row(filtered)
    left,right = st.columns(2)
    with left:
        fig = px.box(filtered, x="category", y="risk_score",
                     color="category", title="Afet Türüne Göre Risk Puanı")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.scatter(filtered, x="population_affected", y="risk_score",
                         color="risk_level", size="severity",
                         color_discrete_map=risk_color_map(),
                         title="Etkilenen Nüfus ve Risk İlişkisi")
        st.plotly_chart(fig, use_container_width=True)
    st.subheader("Ekip Bazında İş Yükü")
    team = filtered.groupby("device_id",as_index=False).agg(
        kayıt=("record_id","count"),
        ortalama_risk=("risk_score","mean"),
        nüfus_etkisi=("population_affected","sum")
    )
    fig = px.bar(team, x="device_id", y="kayıt", color="ortalama_risk",
                 title="Saha Ekiplerine Göre Kayıt Sayısı")
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Önceliklendirme Mantığı")
    st.markdown("""
    Örnek risk puanı 0–100 aralığına sınırlandırılır:
    - **Şiddet etkisi:** şiddet seviyesi × 10 (en fazla 50 puan)
    - **Nüfus etkisi:** min(etkilenen nüfus / 1.000, 1) × 30 (en fazla 30 puan)
    - **Altyapı etkisi:** altyapı hasar seviyesi × 4 (en fazla 20 puan)

    Bu ağırlıklar yalnızca prototipi açıklamak için seçilmiştir. Bilimsel olarak
    kalibre edilmiş bir afet risk modeli veya resmî müdahale kriteri değildir.
    """)

elif page == "Sistem Nasıl Çalışır?":
    st.subheader("Uçtan Uca Sistem Mimarisi")
    st.markdown("""
    <div style="border:1px solid #dbe3ec;border-radius:12px;padding:18px;background:#f8fafc">
      <div style="text-align:center;padding:12px;background:#dbeafe;border-radius:9px">
        <b>1 — SAHA / MOBİL CİHAZ</b><br>
        Form • GPS • Zaman damgası • Fotoğraf kanıtı • Yerel SQLite
      </div>
      <div style="text-align:center;font-size:24px;padding:5px">↓</div>
      <div style="text-align:center;padding:12px;background:#e0f2fe;border-radius:9px">
        <b>2 — ÇEVRİMDIŞI ÇALIŞMA</b><br>
        İnternet olmasa da kayıt cihazda saklanır • Kuyrukta bekletilir
      </div>
      <div style="text-align:center;font-size:24px;padding:5px">↓ Bağlantı geldiğinde</div>
      <div style="text-align:center;padding:12px;background:#dcfce7;border-radius:9px">
        <b>3 — SENKRONİZASYON API'Sİ</b><br>
        JSON aktarımı • SHA-256 bütünlük kontrolü • Tekrar deneme • Mükerrer kayıt kontrolü
      </div>
      <div style="text-align:center;font-size:24px;padding:5px">↓</div>
      <div style="text-align:center;padding:12px;background:#fef3c7;border-radius:9px">
        <b>4 — BÖLGESEL / MERKEZİ VERİ KATMANI</b><br>
        Veri doğrulama • Birleştirme • Coğrafi veri tabanı (üretim mimarisinde PostgreSQL/PostGIS)
      </div>
      <div style="text-align:center;font-size:24px;padding:5px">↓</div>
      <div style="text-align:center;padding:12px;background:#fce7f3;border-radius:9px">
        <b>5 — KARAR DESTEK PANELİ</b><br>
        Harita • Risk puanı • Öncelik listesi • Raporlama
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Saha Ekibinin İş Akışı")
    st.markdown("""
    1. Ekip mobil uygulamada olay kaydı açar.
    2. Cihaz GPS konumu ve zaman damgasını ekler.
    3. Fotoğraf ve açıklama çevrimdışı olarak cihazda tutulur.
    4. İnternet yoksa kayıt **gönderim kuyruğunda** bekler.
    5. Bağlantı geldiğinde uygulama yalnızca gönderilmemiş kayıtları aktarır.
    6. Sunucu kayıt bütünlüğünü kontrol eder ve mükerrer kayıtları engeller.
    7. Merkezi panel yeni kayıtları analiz ederek karar vericilere sunar.
    """)
    st.info(
        "Bu web paneli, mimarinin analiz ve sunum katmanını gösterir. "
        "Gerçek Android uygulaması, gerçek çevrimdışı cihaz veritabanı ve "
        "canlı sunucu entegrasyonu bu prototipte kurulmuş değildir."
    )

elif page == "Veri ve Varsayımlar":
    st.subheader("Veri Setinin Nasıl Üretildiği")
    st.markdown("""
    Bu prototipteki 1.000 kayıt gerçek olaylardan alınmamıştır. Kod her açıldığında
    sabit rastgelelik tohumu ile benzer sentetik test verileri üretir.

    **Konum:** Isparta merkez çevresinde yaklaşık koordinat dağılımı.

    **Afet türü dağılımı (üretim olasılıkları):**
    - Deprem: %30
    - Sel: %22
    - Heyelan: %14
    - Orman yangını: %14
    - Altyapı: %20

    **Diğer alanlar:**
    - Şiddet: 1–5 ölçeğinde olasılıksal seçim
    - Etkilenen nüfus: log-normal dağılımdan türetilmiş sentetik sayı
    - Altyapı hasarı: 0–5 ölçeği
    - Zaman: son 72 saat içinde rastgele zaman damgası
    - Saha ekibi: dört sentetik ekipten biri
    - Fotoğraf durumu ve senkronizasyon durumu: test amaçlı rastgele atanır
    """)
    st.subheader("Veri Kalitesi ve Sınırlılıklar")
    q1,q2,q3 = st.columns(3)
    q1.metric("Toplam kayıt", f"{len(data):,}")
    q2.metric("Fotoğraf referansı olan", f"{(data.evidence_status=='Fotoğraf var').sum():,}")
    q3.metric("Senkronize işaretli", f"{(data.sync_status=='Senkronize').sum():,}")
    st.markdown("""
    **Gerçek saha uygulamasına geçiş için gerekenler**
    - Android/Kotlin veya Flutter mobil uygulaması
    - Room/SQLite yerel veri saklama ve çevrimdışı harita paketi
    - Kimlik doğrulamalı, TLS kullanan API
    - PostgreSQL + PostGIS merkezi veri tabanı
    - Rol bazlı erişim, denetim kayıtları ve yedekleme
    - AFAD/belediye/ilgili kurumlardan doğrulanmış veri ve onaylı risk metodolojisi
    - KVKK, kişisel veri minimizasyonu ve hassas konum verisi güvenliği
    """)
    st.subheader("Örnek Ham Kayıtlar")
    st.dataframe(data.head(30), use_container_width=True, hide_index=True)
    csv_all = data.to_csv(index=False).encode("utf-8-sig")
    st.download_button("Tüm sentetik veri setini CSV indir",
                       csv_all, "isparta_sentinel_synthetic_data.csv", "text/csv")

st.divider()
st.caption(
    "Isparta Afet Yönetim ve Karar Destek Prototipi • "
    "Eğitim, akademik sunum ve mimari gösterim amacıyla hazırlanmıştır. "
    "Gerçek olay veya resmî afet verisi içermez."
)
