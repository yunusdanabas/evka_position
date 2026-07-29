# Repeatability Test

> **Active blocker evidence, not acceptance:** theta count/return loss remains unresolved. This
> session must not be used to approve PPR, a world transform, or production readiness.

Working distance: 1.7 – 2.4 m.

## Sonuç

| Ölçüt | Değer |
|---|---|
| Repeatability (RMS) | **± 10 mm** |
| Aynı point'in iki ölçümü arası — ortalama | 18.5 mm |
| Aynı point'in iki ölçümü arası — en iyi / en kötü | 4.5 / 34.4 mm |

## Axis bazında

| Axis | Repeat error | Durum |
|---|---|---|
| Radius (draw-wire) | < 2 mm | ✅ |
| Elevation (phi) | ~0.1° | ✅ |
| Azimuth (theta) | 1.1°'ye kadar | ❌ 2 m'de 35 mm |

## Sebep

Hatanın tamamı azimuth ekseninde. Radius ve elevation encoder'ları aynı point'e her
dönüşte aynı değeri okuyor, azimuth encoder'ı okumuyor. Bu bir yazılım veya calibration
factor hatası değil — factor yanlış olsa aynı point'te yine aynı değer okunurdu.
Azimuth encoder'ı ölçümler arasında count kaybediyor; muhtemel sebep coupling'inde
mechanical slip veya backlash.
