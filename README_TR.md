# Evka Position — WiFi Kullanıcı Kılavuzu

Bu kılavuz, Evka Position sistemine WiFi üzerinden bağlanmak ve konum verisini almak isteyen üçüncü taraf kullanıcılar içindir.

> English documentation: [README.md](README.md)

---

## 1. Sisteme Genel Bakış

ESP32 tabanlı küresel 3B konumlama sistemi. Üç encoder'dan (2 döner + 1 tel) okunan veriler küresel koordinatlara (r, θ, φ) dönüştürülür, ardından Kartezyen koordinata (X, Y, Z mm) çevrilir. Sistem 20 Hz'de veri yayınlar.

---

## 2. WiFi'ye Bağlanma

ESP32 açıldığında kendi WiFi erişim noktasını oluşturur:

| Ayar | Değer |
|------|-------|
| SSID (Ağ adı) | `CMDCNC_EVKA` |
| Şifre | `cmdcnc1234` |
| IP adresi | `192.168.1.50` |

**Bağlanma adımları:**
1. Cihazınızın WiFi ayarlarını açın
2. `CMDCNC_EVKA` ağını seçin
3. Şifre: `cmdcnc1234`
4. Tarayıcıda `http://192.168.1.50` adresine gidin

> **Önemli:** `192.168.1.x` aralığı çoğu ev/ofis yönlendiricisinde de kullanılır. Panele ulaşamıyorsanız önce ev/ofis WiFi'nızı devre dışı bırakın — işletim sisteminiz `192.168.1.50` adresini yönlendiriciye yönlendiriyor olabilir.

### WiFi LED Göstergesi (GPIO 2)

| LED durumu | Anlam |
|------------|-------|
| KAPALI | STA kimlik bilgisi tanımlı değil |
| YANIP SÖNER (500 ms) | STA tanımlı, bağlanıyor |
| SÜREKLI AÇIK | Yönlendiriciye bağlandı |

---

## 3. Web Kontrol Paneli

Bağlandıktan sonra tarayıcıda `http://192.168.1.50` adresini açın.

**Canlı Görünüm sekmesi:**
- 3B konum izi ve XY/XZ/YZ projeksiyonları
- X, Y, Z, R, θ, φ anlık değerleri
- Oturum verilerini CSV olarak dışa aktarma

**Kalibrasyon sekmesi:**
- Tel enkoderi çok denemeli kalibrasyon (ortalama PPR, yayılma %)
- Theta/Phi kalibrasyon (tur sayısı girişi)
- PPR değerlerini RAM'e veya kalıcı olarak NVS flash belleğe kaydetme

---

## 4. TCP Veri Protokolü (Port 8080)

`192.168.1.50:8080` adresine TCP bağlantısı açın. ESP32 en fazla 3 eş zamanlı istemciyi kabul eder.

**ESP32 → İstemci (20 Hz yayın):**

```
X123.45,Y-56.78,Z890.12
SENSOR,900.00,25.000,10.000,1,42
```

`SENSOR` alan sırası: `r_mm, theta_derece, phi_derece, gecerli, kare_sayisi`

**Python ile bağlantı örneği:**

```python
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("192.168.1.50", 8080))

buffer = ""
while True:
    buffer += sock.recv(256).decode("utf-8", errors="ignore")
    while "\n" in buffer:
        line, buffer = buffer.split("\n", 1)
        line = line.strip()
        if line.startswith("X") and "Y" in line and "Z" in line:
            # X123.45,Y-56.78,Z890.12
            parts = {p[0]: float(p[1:]) for p in line.split(",")}
            print(f"X={parts['X']:.2f}  Y={parts['Y']:.2f}  Z={parts['Z']:.2f}")
```

---

## 5. WebSocket Protokolü

`ws://192.168.1.50/ws` adresine bağlanın. Sistem 20 Hz'de DATA mesajı yayınlar:

```
DATA,123.45,-56.78,890.12,900.00,25.000,10.000,1,42,12345
```

Alan sırası: `x_mm, y_mm, z_mm, r_mm, theta_derece, phi_derece, gecerli, kare, zaman_ms`

Komut göndermek için metin çerçevesi olarak gönderin (aşağıdaki komut tablosuna bakın).

---

## 6. Temel Komutlar

Tüm komutlar serial (115200 baud), TCP ve WebSocket üzerinde çalışır. Komutlar sonuna `\n` (satır sonu) ekleyerek gönderilir.

| Komut | Yanıt | Açıklama |
|-------|-------|----------|
| `PING` | `ACK:PONG` | Bağlantı testi |
| `ZERO` | `ACK:ZERO` | Tüm encoder sıfır noktasını sıfırla |
| `ZERO_T` | `ACK:ZERO_T` | Yalnızca theta encoder'ı sıfırla |
| `ZERO_P` | `ACK:ZERO_P` | Yalnızca phi encoder'ı sıfırla |
| `ZERO_W` | `ACK:ZERO_W` | Yalnızca tel encoder'ı sıfırla |
| `STATUS` | `STATUS,<alanlar>` | Anlık durum özeti |
| `CONSTANTS` | `CONSTANTS,<alanlar>` | Kalibrasyon sabitleri |
| `GET_IP` | `STA_IP:<ip>` | Yönlendirici IP'sini sorgula |
| `SYSINFO` | `SYSINFO,<rssi>,<heap>,<uptime>,<tcp>` | Sistem bilgisi |
| *(bilinmeyen)* | `ERR:UNKNOWN_CMD` | Tanınmayan komut |

---

## 7. Kablosuz Uzaktan Kumanda (ESP-NOW)

2 düğmeli ESP32-C3 SuperMini kolye, ana ESP32 ile ESP-NOW protokolü üzerinden iletişim kurar. Eşleştirme gerekmez — AP ile aynı WiFi kanalında yayın yapar.

| Düğme | GPIO | Renk | Komut | İşlev |
|-------|------|------|-------|-------|
| 0 | 4 | Yeşil | `SAVE_POINT` | Mevcut konumu kaydet |
| 1 | 5 | Kırmızı | `DEL_POINT` | Son kayıtlı noktayı sil |

**Uzaktan kumanda firmware'ini derle ve yükle:**
```bash
pio run -e button_remote --target upload
pio device monitor -e button_remote
```

Donanım: ESP32-C3 SuperMini + genişletme kartı (LiPo 500 mAh, USB-C şarj).
Ana kart önce açılmalı — uzaktan kumanda `CMDCNC_EVKA` SSID'sini tarayarak WiFi kanalını bulur.
Şema, BOM ve kart teknik özellikleri: `docs/hardware_design/remote/`

---

## 8. Router Modunda Kullanım (STA)

ESP32, kendi AP'si ile aynı anda bir WiFi yönlendiricisine de bağlanabilir (AP+STA modu).

1. Web panelindeki **WiFi Settings** alanına SSID ve şifreyi girin → **Kaydet ve Yeniden Başlat**
2. Yeniden başlatma sonrası `GET_IP` komutunu gönderin → `STA_IP:10.x.x.x` yanıtını alın
3. Bu IP üzerinden TCP port `8080` ile bağlanabilirsiniz
4. Doğrudan bağlantı için `192.168.1.50` hâlâ çalışır

Not: Firmware, STA bağlantısı koptuğunda AP erişilebilirliğini korumak için olay-tabanlı WiFi toparlanması kullanır (AP yeniden doğrulama + kontrollü STA yeniden deneme bekleme süresi).

---

## 9. Sorun Giderme

- **Panele ulaşamıyorum:** Cihazınızda başka bir WiFi bağlantısı aktif olabilir; ev/ofis WiFi'nizi devre dışı bırakın.
- **Veri gelmiyor:** `PING` komutu gönderin; `ACK:PONG` yanıtı geliyorsa bağlantı sağlıklıdır.
- **Veriler 0,0,0:** Sistem henüz sıfır noktasını almamış olabilir; `ZERO` komutunu gönderin (cihaz mekanik ev konumundayken).
- **TCP bağlantısı düşüyor:** Maksimum 3 eş zamanlı istemci desteklenir; fazlası `ERR:MAX_CLIENTS` hatası alır.
- **LED yanmıyor:** `ENABLE_WIFI=0` ile derlenmiş olabilir; `SphericalSensor.h` dosyasını kontrol edin.

Ayrıntılı WiFi teşhis kaydı: `docs/WIFI_PERFORMANCE_ISSUES_LOG.md`  
CMD yazılım entegrasyonu: `docs/integration/CMD_SOFTWARE_INTEGRATION.md`

---

## 10. Firmware Güvenilirlik Durumu (2026-04-09)

2026-04-09 tarihinde Gemini + Copilot ile tam kod incelemesi yapıldı, bu oturumda tespit edilen kod sorunları giderildi:

- **`normalizeAngle()` O(1) hale getirildi** — while döngüleri `fmodf` ile değiştirildi
- **STA bağlantı watchdog eklendi** — IDF DISCONNECTED olayını kaçırırsa 15 s sonra otomatik kurtarma
- **Küresel koordinatlar için NaN/Inf koruması** — `validateLimits()` içine eklendi
- **Float aritmetik optimize edildi** — tüm trigonometri ve EMA filtresi double yerine float kullanıyor (`sinf/cosf/sqrtf`); ESP32'de double için donanım FPU yok
- **6 WiFi kurtarma hatası** düzeltildi (volatile bayraklar, millis() taşma, backoff tekrarı, vb.)

Tam değişiklik günlüğü ve bekleyen fiziksel doğrulama adımları: `docs/WIFI_PERFORMANCE_ISSUES_LOG.md` (2026-04-09 bölümü + Open Items)
