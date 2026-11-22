# FlowAI Studio kullanım kılavuzu

[Türkçe](flowai-studio.tr.md) · [English](flowai-studio.en.md) · [Kurulum özeti](../README.md)

FlowAI Studio, akışları tarayıcıdan yazmak, zamanlamak ve izlemek için kullanılan yerel bir çalışma ortamıdır. Workflow motoru Apache-2.0 lisanslı Kestra OSS 1.3.48 tabanlıdır. PostgreSQL → Oracle laboratuvarı, ürünle gelen sentetik verili örneklerden biridir.

## 1. Mac’te kurulum

Özel GitHub deposuna erişim, JDK 25, Node.js 22 ve Python 3.13 veya 3.14 gerekir. Veritabanı laboratuvarı için Docker Desktop da gerekir.

```bash
git clone --branch main https://github.com/eminegl24/flowai-studio-kestra.git
cd flowai-studio-kestra
./flowai/local.sh setup
./flowai/local.sh run
```

[FlowAI Studio’yu aç](http://127.0.0.1:18081/ui/main/welcome). `admin` hesabının üretilen parolası, kendi Mac’indeki `.flowai-local/config.local.json` dosyasında `users.admin.password` alanındadır. Terminal işlemi açıkken uygulama çalışır. Durdurmak için **Ctrl+C** kullan. İlk derleme bağımlılıkları indirdiği için daha uzun sürebilir. Java bulunamazsa `JAVA_HOME` değerini JDK 25 dizinine ayarla.

Arayüz varsayılan olarak **18081**, dahili motor **18082** portundadır. Özel port kullanmak için `FLOWAI_PORT=18181 FLOWAI_ENGINE_PORT=18182 ./flowai/local.sh run` çalıştır. Örnekleri içe aktarırken aynı `FLOWAI_PORT` değerini kullan.

## 2. İlk akışını çalıştır

1. **AI Copilot** ekranında **Write a log message** önerisini seç veya **Start a Tutorial** ile rehbere başla.
2. Akış editöründe **Flow Code** alanını incele. Akışın `id`, `namespace` ve `tasks` alanlarını göreceksin.
3. **Save → Execute** ile akışı kaydet ve başlat. Girdi isteyen örneklerde formu doldur.
4. **Executions → son çalıştırma → Logs** yoluyla mesajı bul. Çalıştırmanın durumu **SUCCESS** ise görev başarıyla tamamlanmıştır.

Bir öneri metnini değiştirmeden gönderdiğinde hazır örnek açılır. Kendi tarifini yazarsan **editör Copilot’u** Gemini ile YAML taslağı üretebilir. Gemini’yi etkinleştirmek için uygulamayı durdur, `./flowai/local.sh gemini` komutuyla kendi anahtarını görünmeyen isteme gir ve uygulamayı yeniden başlat.

```yaml
id: ilk_merhaba
namespace: egitim.baslangic
tasks:
  - id: mesaj_yaz
    type: io.kestra.plugin.core.log.Log
    message: Merhaba, FlowAI!
```

`namespace` akışları gruplar. Yerel URL’deki `main` üst çalışma alanıdır. Bir **Execution ID**, akışın tek bir çalıştırmasını tanımlar ve otomatik üretilir. **Execution labels** ile çalıştırmaya `amac=ilk_test` gibi aranabilir bir etiket ekleyebilirsin.

## 3. Ekranları kullan

| Ekran | Kullanımı |
|---|---|
| **Flows → Edit** | YAML’ı düzenle. Önceki kayıtları **Revisions** üzerinden incele. |
| **Topology** | Görevlerin sırasını ve bağımlılıklarını gör. |
| **Executions → Overview / Gantt** | Sonucu, başlangıç zamanını ve her görevin süresini incele. |
| **Logs / Outputs / Metrics** | Mesajları ve hata ayrıntılarını, görev verilerini ve ölçümleri ayrı ayrı gör. |
| **Debug Expression** | Mevcut çalıştırmanın bağlamında bir Pebble ifadesini dene. |
| **Triggers** | Akışı neyin başlattığını kontrol et. **Tenant → Triggers** ekranında zamanlanmış işleri birlikte gör. |
| **Blueprints → Community** | Örnek akış ve pano şablonlarını incele. Şablonun eklentilerini ve bağlantı ayarlarını doğrula. |
| **Tenant → KV Store** | Gizli olmayan çalışma değerlerini sakla. Örneğin son başarılı aktarım tarihini kaydet. |
| **Studio Tools** | Yerel denetim kayıtlarını, SAP envanterini ve AgentHub bağlantısını aç. |

**Copilot Sohbet**, işi tarif etmek, bir ekranı anlamak veya hatayı açıklatmak için kullanılabilir. Kayıtlı bir akışı tam adıyla yazarsan, uygulama son çalıştırmanın kod sürümünü yerelde inceleyip görev özeti ve tanınan hata kodlarını Gemini’ye verebilir. Ham loglar ve kayıtlı YAML otomatik gönderilmez. Sohbet üretilen aday kodu kontrol eder ve çalıştırma testi yapılamayan kodu saklayabilir. Uygulamada taslak oluşturup gözden geçirmek için **Flow Code → AI Copilot** yolunu kullan. Test amaçlı olmayan müşteri kayıtlarını, parolaları ve API anahtarlarını sohbet mesajlarına koyma.

## 4. PostgreSQL → Oracle laboratuvarı

1. Docker Desktop’ı aç. FlowAI’yi durdur ve `./flowai/local.sh bank` çalıştır. Bu komut eğitim veritabanlarını, yerel gizli ayarları ve örneklerin eklentilerini kurar.
2. FlowAI’yi yeniden başlat. Başka bir Terminal’de `./flowai/local.sh examples --bank` çalıştır. Aynı kimliğe sahip mevcut akışlar korunur.
3. `egitim.banka.banka_baglanti_kontrolu` akışını çalıştır. Yeni laboratuvarda kaynakta **3**, hedefte **0** müşteri beklenir.
4. `egitim.banka.postgres_to_oracle_transactions` akışını aç. Tarihsel kimliği bu şekilde kalsa da depodaki kayıtlı örnek **müşteri tablosunu** aktarır. Çalıştırıp hedefteki sonucu **Outputs**, **Logs** veya DBeaver üzerinden kontrol et.

| Bağlantı | Yerel adres | Kullanıcı |
|---|---|---|
| PostgreSQL | `127.0.0.1:15432/bank_source` | `bank_source` |
| Oracle | `127.0.0.1:11521/FREEPDB1` | `bank_dwh` |

DBeaver ayarları ve veri yükleme seçenekleri [laboratuvar kılavuzunda](../examples/bank-etl/README.md). Hesap ve işlem tablolarını da taşıyan bir akış tasarlarsan sıra **müşteri → hesap → işlem** olmalı. `ORA-02291`, Oracle’ın ilgili üst kaydı bulamadığını söyler.

## 5. Zamanla, izle ve bildir

**Günlük çalışma** için akıştaki **Schedule** tetikleyicisini kullan. Eğitim akışı İstanbul saatiyle **08.00** için `cron: "0 8 * * *"` ve `timezone: Europe/Istanbul` içerir. İçe aktarılan tetikleyici kapalı başlar. Akışı manuel test ettikten sonra **Triggers** ekranından etkinleştir ve bir sonraki çalışma saatini kontrol et. **Execute → Schedule date** tek bir çalıştırma planlar. **Backfill**, geçmişteki plan saatleri için çalıştırma oluşturur. Geçmiş veri işlemek için sorgunun plan tarihini kullanması gerekir.

| Akış | Davranış | Kurulum |
|---|---|---|
| `postgres_to_oracle_bildirim` | Aktarım sonucu önce loga yazılır, sonra Resend ile e-posta gönderilir. | `./flowai/local.sh resend SENDER_EMAIL RECIPIENT_EMAIL` komutuyla kendi hesabını yapılandır, FlowAI’yi yeniden başlat ve tetikleyiciyi etkinleştir. |
| `postgres_to_oracle_teams_bildirim` | Sonucu Teams kanalına gönderir. | Teams Workflows adresini yerel `TEAMS_WEBHOOK_URL` gizli ayarına ekle, FlowAI’yi yeniden başlat ve tetikleyiciyi etkinleştir. |
| `postgres_to_oracle_teshis` | Aktarım başarısız olduğunda ödeme hesaplarının Oracle’da bulunup bulunmadığını salt okunur sorgularla kontrol eder. | Tetikleyiciyi etkinleştir veya manuel testte eski bir aktarımın `source_execution_id` değerini gir. |

Bildirim zincirini denemek için **ana aktarımı** manuel çalıştır. Bildirim akışını doğrudan çalıştırmak yalnızca test logu üretir. Teams’e gerçek gönderim için kanal erişimi ve geçerli Workflows adresi gerekir. Teşhis örneği eksik hesapları raporlar. Otomatik onarım ve yeniden çalıştırma bu örnekte bağlı değildir.

## 6. Yönetim, veri ve diğer entegrasyonlar

- **Roller** — `admin` yönetir, `operator` mevcut işleri başlatabilir, `viewer` görüntüler. Roller yerel gateway’de uygulanır. Kullanıcı ve gizli ayarlar yerel yapılandırmada tutulur.
- **Audit** — Yönetici **Studio Tools → Load recent activity** ile son işlemleri görebilir. İş çalıştırma logları ise ilgili **Execution → Logs** ekranındadır.
- **AgentHub** — **Studio Tools** üzerinden bir HTTP agent’ına istek gönderilebilir. Bağlantı sözleşmesi kontrollü bir servisle test edilmiştir. Kurumunuzun adresi, yetkisi ve gerekiyorsa istek biçimi uyarlaması gerekir.
- **MCP ve SAP** — MCP aracı ATL/XML dışa aktarımların envanterini çıkarır. Çıkan taslak, SAP dönüşüm ve eşlemelerinin tamamını taşımak için yeterli değildir.
- **Yerel dosyalar** — `.flowai-local/` kimlik bilgilerini, çalıştırma geçmişini ve eklentileri tutar. Veritabanı laboratuvarı Docker birimleri kullanır. Git’e yalnızca kod, şema ve örnek veriler gider.

Bu kurulum yerel geliştirme içindir. Ortak veya üretim kurulumundan önce erişim, kimlik yönetimi, veri saklama ve operasyon süreçleri ekipçe değerlendirilmelidir. [Teknik geliştirme kılavuzu](../flowai/README.md) · [Açık kaynak atıfları](../FLOWAI-NOTICE.txt) · [Apache 2.0 lisansı](../LICENSE)

## 7. Sorun giderme

| Belirti | İlk kontrol |
|---|---|
| **Sayfa açılmıyor** | Terminal’de `local.sh run` çalışıyor mu? `.flowai-local/studio.log` ve `.flowai-local/engine.log` dosyalarına bak. |
| **Invalid type / No plugin registered** | Akışın istediği eklenti bu kurulumda yüklenmemiş olabilir. Laboratuvar için `local.sh bank` komutunu tamamla ve yeniden başlat. |
| **Flow Code kırmızı uyarı veriyor** | Editöre YAML koy. Python görevinde kodu `script: |` altında girintili yaz. |
| **Execute başarılı, bildirim gelmedi** | Ana aktarımın ve bildirim akışının çalıştırmalarını ayrı kontrol et. Resend gönderen/alıcı ayarını veya Teams adresini doğrula. Bildirim akışının doğrudan manuel testi gönderim yapmaz. |
| **Günlük iş çalışmadı** | **Tenant → Triggers** altında tetikleyicinin etkinliğini, saat dilimini ve bir sonraki planı kontrol et. Yerel uygulama plan zamanında çalışıyor olmalı. |
