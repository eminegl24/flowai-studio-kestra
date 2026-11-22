# Yerel banka ETL laboratuvarı

Bu ortam, PostgreSQL kaynak sisteminden Oracle veri ambarına veri taşımayı denemek için üç bağlantılı tablo içerir. Kayıtlar örnektir. Servisler Mac’in yerel adresinden erişilir.

| Ayar | PostgreSQL kaynak | Oracle hedef |
|---|---|---|
| Sunucu | 127.0.0.1 | 127.0.0.1 |
| Port | 15432 | 11521 |
| Veritabanı veya servis | `bank_source` | `FREEPDB1` (Service name) |
| Kullanıcı | `bank_source` | `bank_dwh` |
| Parola | `.env` içindeki `BANK_PG_PASSWORD` | `.env` içindeki `BANK_ORACLE_PASSWORD` |

JDBC adresleri

- PostgreSQL: `jdbc:postgresql://127.0.0.1:15432/bank_source`
- Oracle: `jdbc:oracle:thin:@//127.0.0.1:11521/FREEPDB1`

Bu adresler DBeaver ve Mac üzerinde çalışan FlowAI worker için geçerli. Oracle bağlantısında **SID** yerine **Service name** seç. Dosyadaki parolaları bağlantı ayarlarına gir.

## Tablolar ve beklenen kayıt sayıları

| Tablo | İçerik | PostgreSQL ilk veri seti | Oracle başlangıç |
|---|---|---:|---:|
| `customers` | Müşteriler | 3 | 0 |
| `accounts` | Müşteri hesapları ve bakiyeler | 4 | 0 |
| `transactions` | Hesap hareketleri | 6 | 0 |

Hesaplar müşteri kimliğine, hareketler hesap kimliğine bağlı. Yükleme sırası `customers` → `accounts` → `transactions`.

## Başlatma ve test

Docker Desktop açıkken bu klasörde çalıştır:

```sh
python3 setup.py
docker compose up -d --wait
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python lab.py status
.venv/bin/python lab.py load --dry-run
```

`load --dry-run` Oracle’a yazmayı ve kaynakla birebir karşılaştırmayı dener. Başarılı testin sonunda işlemi geri alır ve hedef tablolar boş kalır. Deneme verisini kalıcı yüklemek için `lab.py load`, sonradan karşılaştırmak için `lab.py verify` kullan. Yükleme kimlik alanlarına göre ekleme veya güncelleme yapar. Kaynaktan silinen kayıtlar için Oracle’da silme işlemi uygulamaz.

## İlk SQL alıştırması

Aynı sorguyu PostgreSQL ve Oracle bağlantılarında çalıştır:

```sql
SELECT c.customer_name, a.currency, COUNT(*) AS hareket_sayisi,
       SUM(t.amount) AS net_hareket
FROM customers c
JOIN accounts a ON a.customer_id = c.customer_id
JOIN transactions t ON t.account_id = a.account_id
GROUP BY c.customer_name, a.currency
ORDER BY c.customer_name, a.currency;
```

Yüklemeden sonra iki tarafta dört satır ve aynı tutarlar çıkmalı. Farklı para birimleri ayrı gruplarda kalır.

FlowAI’deki ilk alıştırmada önce PostgreSQL bağlantısıyla `customers` tablosunu okuyup kayıt sayısının 3 olduğunu doğrula. Ardından anahtar alanlarına göre Oracle’a ekleme veya güncelleme yapan akışı dene. Bağlantı şifrelerini Copilot mesajına ya da akışın açık metnine koyma. Ana repo dizininde `./flowai/local.sh bank` komutu FlowAI için PostgreSQL ve Oracle JDBC eklentilerini kurar. İlk bağlantı testi için PostgreSQL’de `io.kestra.plugin.jdbc.postgresql.Query`, Oracle’da `io.kestra.plugin.jdbc.oracle.Query` görevi ve `SELECT COUNT(*) FROM customers` sorgusunu kullanabilirsin. Başka bir FlowAI kurulumu için önce ilgili JDBC eklentilerini yükle.
