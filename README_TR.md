# Evka Position v4 Prototip Operator Kılavuzu

> İngilizce ana belge: [README.md](README.md)

Evka Position, iki döner enkoder ve bir çekme-teli enkoderinden aldığı sayımları küresel
koordinatlara, ardından sensör referansında X/Y/Z milimetre değerlerine dönüştürür.

## Mevcut Durum

- v4 ESP32-S3 kartı mevcut prototiptir; üretim onayı verilmiş bir ürün değildir.
- Önceki çalışmalarda 20 Hz canlı veri görülmüştür; bu son dokümantasyon geçişinde fiziksel test,
  yükleme veya kablo doğrulaması yapılmamıştır.
- Theta ekseninde sayım kaybı/geri dönüş hatası çözülmemiştir. Kaydedilen en kötü değer yaklaşık
  1,1 derece, 2 m mesafede yaklaşık 35 mm'dir.
- Kabul edilmiş endpoint/dünya dönüşümü yoktur.
- `tools/evka_gui` standart operatör arayüzüdür ve yalnızca sensör referansını gösterir.
- Eski tedarikçi C# uygulaması depodan silinmiştir; TCP protokolü korunur.

Theta hatasını PPR değiştirerek veya dünya dönüşümüne yedirerek gizlemeyin.

## v4 Konnektör Sırası

| Konnektör | Eksen | PCB'den türetilen sıra | GPIO |
|---|---|---|---|
| J1 | Çekme teli | `1=A, 2=GND, 3=B, 4=+5V` | A=7, B=8 |
| J2 | Phi | `1=+5V, 2=A, 3=GND, 4=B` | A=4, B=5 |
| J3 | Theta | `1=A, 2=GND, 3=B, 4=+5V` | A=9, B=10 |

J2 sırası J1/J3'ten farklıdır. Bu bilgi KiCad PCB/pad netlerinden ve firmware pin haritasından
türetilmiştir; **bu son geçişte fiziksel olarak yeniden doğrulanmamıştır**. Güç vermeden önce gerçek
kart, kablo renkleri, süreklilik ve polariteyi doğrulayın.

| Enkoder | A | B | +5V | GND |
|---|---|---|---|---|
| Theta/Phi E40S6 | Siyah | Beyaz | Kahverengi | Mavi |
| DWEM2 çekme teli | Sarı | Yeşil | Kahverengi | Beyaz |

## WiFi Bağlantısı

Mevcut bilgiler değiştirilmemiştir:

| Ayar | Değer |
|---|---|
| AP ağ adı | `CMDCNC_EVKA` |
| AP şifresi | `cmdcnc1234` |
| Web paneli | `http://192.168.1.50` |
| TCP | `192.168.1.50:8080` |
| WebSocket | `ws://192.168.1.50/ws` |
| STA statik adresi | `192.168.1.84/24`, ağ geçidi `192.168.1.254` |

Bağlanmak için:

1. Bilgisayarı/telefonu `CMDCNC_EVKA` ağına bağlayın.
2. Şifre olarak `cmdcnc1234` girin.
3. Tarayıcıda `http://192.168.1.50` adresini açın veya `evka_gui` kullanın.
4. `192.168.1.50` açılmıyorsa ev/ofis WiFi bağlantısını kapatıp yalnızca EVKA AP'ye bağlanın.

Sabit şifreler ve TCP/WebSocket komutları uygulama seviyesinde kimlik doğrulaması sağlamaz. Sistemi
yalnızca izole, güvenilir laboratuvar ağında kullanın. Port 80/8080'i internete veya güvenilmeyen bir
LAN'a açmayın.

## Firmware Derleme ve Yükleme

Desteklenen araç zinciri PlatformIO'dur. Yalnızca derleme:

```bash
pio run -e esp32s3_v4
pio run -e wemos_d1_r32
pio run -e button_remote
```

Kablo ve güvenlik kontrolünden sonra yükleyin. `/dev/ttyACM0` yerine doğru portu kullanın
(bazı kartlarda `/dev/ttyUSB0`, Windows'ta `COMx`). Aynı portu iki uygulamada birden açmayın.

**Ana cihaz** (ESP32-S3 v4 taşıyıcı — mevcut prototip):

```bash
pio run -e esp32s3_v4 --target upload --upload-port /dev/ttyACM0
pio device monitor -e esp32s3_v4
```

Klasik Wemos uyumluluk hedefi (v4 taşıyıcıya yüklenmez):

```bash
pio run -e wemos_d1_r32 --target upload --upload-port /dev/ttyUSB0
```

**Uzaktan kumanda** (ESP32-C3 pendant, ESP-NOW):

```bash
pio run -e button_remote --target upload --upload-port /dev/ttyACM0
pio device monitor -e button_remote
```

Tezgah test firmware'i (kendi AP'si `REMOTE_TEST`, ESP-NOW yok — bkz.
[`tools/remote_tester/README.md`](tools/remote_tester/README.md)):

```bash
pio run -e button_remote_test --target upload --upload-port /dev/ttyACM0
```

`test_*` ortamları klasik Wemos pin haritasını kullanır; v4 taşıyıcıya yüklenmemelidir.
Ayrıntı: [CONTRIBUTING.md](CONTRIBUTING.md) ve
[pcb_design/EVKA_position_v4/FIRMWARE.md](pcb_design/EVKA_position_v4/FIRMWARE.md).

## Standart Operatör Arayüzü

Depo kökünden:

```bash
python -m tools.evka_gui
python -m tools.evka_gui --tcp 192.168.1.50:8080
python -m tools.evka_gui --ws 192.168.1.50
python -m tools.evka_gui --serial /dev/ttyACM0 --baud 115200
```

Arayüz Serial, TCP, WebSocket ve kayıt tekrarını; 3B/2B grafikleri; Quick IPT; teşhis; ham sayım;
kayıt ve kalibrasyon oturumu araçlarını içerir.

Önemli koordinat kuralları:

- Canlı XYZ sensör referansındadır.
- Software Zero yalnızca ekranda/oturumda ofset uygular; firmware sıfırı değildir.
- Hardware Zero mekanik home konumunda `ZERO` gönderir.
- Kayıtlar ve Quick IPT girdileri software-zero uygulanmamış sensör verisini kullanır.
- Kalibrasyon penceresi aday rapor/JSON üretebilir; canlı `evka_gui` verisine dünya dönüşümü uygulamaz.

Depoda ortak/varsayılan bir kalibrasyon JSON'u yoktur ve kabul edilmiş endpoint/dünya dönüşümü
bulunmaz. PASS alan bir oturum JSON'u yalnızca eski görselleştiriciye
`--legacy-visualizer --calibration <oturum-calibration.json>` ile açıkça verilebilir; `evka_gui`
sensör referansında kalır.

## Telemetri Farkları

Tam ve tek protokol kaynağı: [docs/PROTOCOL.md](docs/PROTOCOL.md).

| Taşıma | 20 Hz veri |
|---|---|
| Serial | `DATA,<x>,<y>,<z>,<r>,<theta>,<phi>,<valid>,<frame>,<ts_ms>` ve okunabilir debug satırı |
| WebSocket | `DATA,...` |
| TCP | Ayrı `X<x>,Y<y>,Z<z>` ve `SENSOR,<r>,<theta>,<phi>,<valid>,<frame>` satırları |

TCP istemcisi tam örnek için XYZ satırını hemen arkasındaki `SENSOR` satırıyla eşleştirmelidir.
`RAW_COUNTS` mutlak donanım sayacı değildir; boot veya son `ZERO*` komutundaki ofsetlere göre
sıfır-bağıl theta/phi/wire sayımlarını döndürür.

## Sık Kullanılan Operatör İşlemleri

- Bağlantı testi: `PING` -> `ACK:PONG`
- LED bağlantı testi: `BLINK` -> `ACK:BLINK`
- Anlık durum: `STATUS`
- Çalışan ölçek değerleri: `CONSTANTS`
- Sıfır-bağıl sayımlar: `RAW_COUNTS`
- Mekanik home'da tüm eksen sıfırı: `ZERO`
- Tek eksen sıfırı: `ZERO_T`, `ZERO_P`, `ZERO_W`

Kalibrasyon, WiFi değiştirme, tüm yanıt/hata biçimleri ve mesajların hangi istemcilere yayınlandığı
için [docs/PROTOCOL.md](docs/PROTOCOL.md) kullanılmalıdır.

## İlk Kontrol ve Durma Koşulları

Firmware açılışta iki saniye bekleyip mevcut enkoder sayaçlarını sıfır kabul eder. Bu sırada sistem
mekanik home'da ve hareketsiz olmalıdır.

Aşağıdaki durumda işlemi durdurun:

- J2 dahil konnektör sırası veya +5V/GND polaritesi kesin değilse;
- hareketsiz bir kanal sayım değiştiriyorsa;
- hareket yanlış kanalı değiştiriyorsa;
- theta aynı noktaya veya home'a aynı sayımla dönmüyorsa;
- bir konnektör ya da kart elemanı ısınıyorsa.

Mevcut hata kaydı:
[docs/calibration/sessions/2026-07-17_repeatability.md](docs/calibration/sessions/2026-07-17_repeatability.md).

## LED ve Batarya Notu

Kaynak kod v4 için varsayılan RGB LED GPIO48'i, alternatif ortamda GPIO38'i seçer. Batarya izleme
kaynakta açıktır ve GPIO1'i 1S LiPo bölücü yolu olarak yorumlar. Bu son geçişte gerçek LED GPIO'su,
renkleri veya batarya ADC doğruluğu fiziksel olarak test edilmemiştir.

## Lisans

Depoda lisans dosyası yoktur. Yeniden dağıtım, kamuya açık ürün sürümü veya üretime hazır olma
iddiası için izin verilmiş sayılmaz. Sahiplik ve lisans ayrıca çözülmelidir.
