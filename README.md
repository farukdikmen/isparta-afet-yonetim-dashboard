# Isparta Afet Yönetim ve Karar Destek Paneli

Etkileşimli Streamlit web uygulaması. Bu sürüm tek uygulama dosyası ve sabitlenmiş bağımlılıklarla hazırlanmıştır.

## Özellikler
- Genel bakış ve KPI kartları
- Afet türü ve risk seviyesi filtreleri
- Isparta çevresinde sentetik olay haritası
- Risk analizi, ekip karşılaştırması ve önceliklendirme
- Sistem mimarisi ve saha iş akışı açıklaması
- Veri üretim yöntemi, varsayımlar ve sınırlılıklar
- CSV indirme

## Önemli veri uyarısı
Uygulama 1.000 sentetik kayıt üretir. Koordinatlar ve olaylar gerçek değildir; AFAD veya başka bir kurumdan alınmış gerçek olay verisi içermez. Risk puanı yalnızca prototipte yöntemi göstermek içindir; resmî risk veya müdahale modeli değildir.

## GitHub'a yüklenecek dosyalar
Repository kök dizininde şu iki dosya bulunmalıdır:
- `app.py`
- `requirements.txt`

## Streamlit Community Cloud yayını
1. Dosyaları GitHub repository'sinin kök dizinine yükle.
2. https://share.streamlit.io adresine GitHub hesabıyla giriş yap.
3. **Create app** seç.
4. Repository, branch (`main`) ve ana dosya yolu (`app.py`) seç.
5. **Deploy** seç.
6. Uygulama açıldıktan sonra oluşan `https://....streamlit.app` adresini paylaş.

## Yerelde çalıştırma
```bash
pip install -r requirements.txt
streamlit run app.py
```
