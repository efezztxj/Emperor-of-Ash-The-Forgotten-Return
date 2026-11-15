# EMPEROR OF ASH: THE FORGOTTEN RETURN *(Çalışma Kodu: KARARSIZLIK)*
## Resmi Oyun Tasarım ve Teknik Mimari Dokümanı (Game Design Document — GDD v1.0)

> **Belge Durumu:** Canlı Tasarım & Üretim Dokümanı (Prototip / Ön-Üretim Aşaması — Hikâye ve görsel detaylar ekip içi beyin fırtınasıyla genişlemeye açıktır).  
> **Hedef Platform:** PC (Windows — DirectX 12)  
> **Oyun Motoru & Üretim Hattı:** Unreal Engine `5.8.4` + Blender `5.3.0` (`OptiX`) + ComfyUI (`MOSS-Image` & `TRELLIS.2`) + Yerel LLM (`9B` & `27B`)

---

## 1. YÖNETİCİ ÖZETİ (GAME OVERVIEW)

| Başlık | Detay |
| :--- | :--- |
| **Çalışma Başlığı** | **Emperor of Ash: The Forgotten Return** *(Evren Teması: Kararsızlık)* |
| **Tür (Genre)** | Karanlık Fantastik Üçüncü Şahıs Aksiyon-RPG (*Grounded Dark Medieval Souls-lite / Seçim Odaklı RPG*) |
| **Kamera Açısı** | Dinamik Omuz Üstü Üçüncü Şahıs + Kesintisiz Gerçek Zamanlı Oyun İçi Sinematikler (`Level Sequencer`) |
| **Görsel Yönetmenlik** | Sinematik Karanlık Ortaçağ Gerçekçiliği (*Demon's Souls Remake, Elden Ring, Lords of the Fallen 2023* kalitesi — çizgifilmsi/eski MMORPG estetiğinden tamamen uzak, kirli dövme çelik, ıslak taş, sarmaşık, kül ve dumanlı ametist paleti) |
| **Silah Kuralı** | **Ateşli / modern silah KESİNLİKLE YOKTUR.** Sadece ortaçağ ve karanlık fantezi disiplinleri: Kılıç, Hançer, Kalkan, Yay/Okçuluk, Asa/Büyü ve Silahsız Keşiş (Monk) dövüş sanatları. |
| **Temel Felsefe** | *"En küçük detayda bile oyuncuyu ve kahramanı içten içe kararsız bırakmak."* Aydınlık ve karanlık mutlak iyi/kötü değildir; her gücün, her dinlenmenin ve her merhametin ağır bir bedeli vardır. |

---

## 2. HİKÂYE, EVREN VE KRONOLOJİ (LORE & NARRATIVE)

### 2.1. İlk Varlık ve 600 Yıllık Karanlık İmparatorluk
* Evren yaratılmadan önce Tanrı, kendisinden sonra **ilk varlığı** yaratır; ona **ölümsüzlük** bahşeder ve bedenini sonsuza dek **25 yaşında** sabitler.
* Kibri ve kusurlu doğası yüzünden cennetten kovulup insanların ve tuhaf varlıkların yaşadığı yeryüzüne sürgün edilir.
* İlahi gücüyle insanların başına geçer ve **600 yıl boyunca** demir yumrukla yönettiği karanlık bir imparatorluk kurar. Halk onu Tanrı katında görür; o ise cennete duyduğu öfkeyle **Gerçek Tanrı'nın öğretilerinin tam tersini emreden kendi ters-dinini** inşa eder.
* **Zoraki Mutluluk Yasası:** Bu dinde imparatorluk sınırları içindeki herkesin her koşulda **mutlu görünmesi ve yüzünde gülümseme taşıması zorunludur**. Gerçek Tanrı'ya gizlice inananlar veya kederini belli edenler ağır işkenceler ve idamlarla cezalandırılır.
* **Yüzsüz / Maskeli Hükümdar Kimliği:** İmparator hükümdarlığı boyunca yüzünü halktan gizleyen **vakur, tam kapalı gümüş/demir bir kraliyet maskesi** (*IV. Baldwin otoritesinde, sıfır açık ten bırakan tasarım*) takmıştır; bu yüzden heykellerinde de gerçek yüzü görünmez veya zamanla aşınmıştır.

### 2.2. Kararsızlık Büyüsü ve Büyük Unutuş
* 600 yılın sonunda İmparator kendi kurduğu sahte tebessüm ve zulüm düzeninden derin bir bıkkınlık duyar. Ancak kimliği bilindiği sürece halkın korkudan değişmeyeceğini anlar; düzeni bizzat içeriden yıkmak ister.
* **Kararsızlık Evreni'nin Hükümdarı** ile gizli bir anlaşma yapar. Karanlık büyü mahzeninde Baş Büyücü ve ekibiyle yasaklı **Kararsızlık Büyüsü** başlatılır:
  * Mühürlerden yoğun dumanlı mor enerji yükselir, büyücülerin elleri kavrularak yanar ve **2–3 kilometrelik alanı sarsan devasa bir mor patlama** gerçekleşir.
* İmparator tüm hafızasını, geçmişini ve kimliğini kaybeder; geriye yalnızca temel hayatta kalma içgüdüsü ve dövüş refleksleri kalır.

### 2.3. Uyanış ve Gri Yaratıklar
* Kararsızlık boyutuna düşen baygın bedenini iki sıska, soluk gri, biçimsiz varlık olan **Gri Yaratıklar** sürükleyerek çıkarır ve küçük bir ortaçağ şehrinin hemen dışındaki **sarmaşıklı, sisli karanlık orman girişine** bırakır.
* Kahraman çamurun içinde gözlerini açtığında üzerinde sıradan yöre kıyafeti, bel çantası, birkaç parça para ve **küçük bir hançer** vardır; ağaçların arasından şehrin uğultusu gelir.

### 2.4. Kararsızlık Evreni ve Yaratık Doğası
* Yaşarken inancı, seçimi ve vicdanı arasında sıkışıp **kararsızlık içinde ölen insanlar** bu boyuta düşer ve en büyük korkularının grotesk birleşimine dönüşür:
  * *Örnek Boss/Yaratık 1:* İnsan gövdeli, çoklu örümcek bacaklı, başı ters dönmüş ve saçları aşağı sarkan gece avcısı.
  * *Örnek Boss/Yaratık 2:* Dönüşümünü tamamlayamadan ölenlerin et ve uzuvlarının birbirine kaynadığı çok kollu birleşmiş ceset ucubeleri.

### 2.5. Üç Büyük Son (Endings)
Bossları aştıkça hafıza parçaları geri döner. Kahraman gerçekte o nefret ettiği 600 yıllık zalim İmparatorun **kendisi olduğunu** hatırladığında anlaşma bozulur ve Kararsızlık Evreni'nin Hükümdarı onu son hesaplaşma için kendi boyutuna çeker. Oyuncuyu 3 felsefi son bekler:
1. **Aydınlık Düzen:** Karanlığı temizler ama günahkârları "arındırmak" adına insanların özgür iradesini ve duygularını silen katı/bağnaz bir mutlak düzen kurar.
2. **Karanlık İmparatorluğun Dönüşü:** Eski korku, demir disiplin ve zoraki tebessüm saltanatını yeniden kurar; zalimdir ama şehri dış canavarlardan koruyan sert bir güvenlik sağlar.
3. **Bağımsız Üçüncü Yol (Kül ve Kararsızların İmparatorluğu):** İki mutlak uçtan da koparak kusurlulara, kararsızlara ve dışlanmışlara yaşama hakkı tanıyan özgür ama tehlikeli yeni bir çağ başlatır.

---

## 3. TEMEL OYNANIŞ SİSTEMLERİ (CORE GAMEPLAY MECHANICS)

### 3.1. Sınıfsız, Eğitmen Tabanlı Melez Gelişim Sistemi
* Oyunun başında oyuncu sadece **Irk, Cinsiyet ve Fiziksel Özelliklerini** belirler (su birikintisindeki yansıma sekansı); **hazır sınıf seçimi yoktur.**
* **Yaşayan Eğitmenler:** Oyuncu şehirde, ormanda veya zindanlarda tanıştığı ustalardan eğitim alarak kendi yolunu şekillendirir:
  * *Kılıç & Kalkan Ustası* (Savuşturma/Parry, ağır/hafif çelik komboları)
  * *Gölge & Hançer Disiplini* (Çevik kanama/arkadan infaz teknikleri)
  * *Kül Okçusu* (Uzun yay, zayıf nokta nişancılığı, tuzak okları)
  * *Keşiş / Yakın Dövüş Sanatları* (Silahsız içsel darbe ve denge kırma)
  * *Kararsızlık & Karanlık Büyü Ustaları* (Mor enerji mühürleri, sis ve ruh büyüleri)
* **Eğitimi Yarıda Bırakma Sonuçları & Melez Sentez:**
  * Oyuncu bir eğitimi yarıda bırakıp başka disipline geçebilir ve öğrendiklerini birleştirebilir (*ör. Keşiş yumruk kombosunu Kararsızlık büyüsüyle patlatmak*).
  * Terk edilen eğitmen kişiliğine göre; anlayış gösterebilir, verdiği özel ekipmana el koyabilir veya ihanete uğradığını düşünüp ileride **intikamcı bir Boss** olarak oyuncunun yolunu kesebilir!

### 3.2. Akıcı Savaş Mimarisi (Combat Feel — "Kütük Gibi Olmama" Anayasası)
1. **Animasyon İptali (`Animation Canceling`):** Saldırı animasyonunun vuruş sonrası toparlanma (*recovery*) karelerinde oyuncu kilitli kalmaz; anında `Kaçınma (Dodge)`, `Kalkan Blok/Parry` veya `Sonraki Kombo` ile akışı kesebilir.
2. **Milimetrik Silah Taraması (`Weapon Socket Sweep Trace`):** Kaba görünmez kutular yerine kılıcın kabzasından ucuna her karede kapsül izi taranır; silah düşmanın hangi uzvuna değerse darbe tam o noktada patlar.
3. **Adil Hurtbox & i-Frames:** Oyuncunun hasar alma kapsülü görsel modelden **%15 daha incedir** (ucuz sıyırma hasarlarını önler); kaçınma anında `~0.35 sn` dokunulmazlık penceresi vardır.
4. **Darbe Ağırlığı (`Hitstop` & Fiziksel Sarsıntı):** İsabet anında `0.04–0.05 sn` mikro duraksama, `MetaSounds` değişken perde kılıç sesi ve `Physical Animation` ile düşman uzvunun darbe yönünde sarsılması uygulanır.

### 3.3. Ölümsüzlük, Bayılma, Kâbuslar ve Gri Yaratıklar Döngüsü
* Ana karakter ölümsüz olduğu için canı sıfırlandığında klasik *"Öldün"* ekranı çıkmaz; karakter **bayılır**.
* **Kâbus Boyutu:** Bayıldığında (veya yüksek Kararsızlık yükünde) geçmişteki günahlarını simgeleyen sürreal zihin sekanslarına düşer (*insan kafalarından örülü patika, paçalarından çeken eller, ufukta koşuldukça çatlayıp beyaz ışıkla patlayan dev dolunay*).
* **Soyulma Riski ve Gri Yaratıkların Yardımı:** Şehir sokaklarında veya haydut bölgesinde bayılırsa kesesindeki parası veya silahı çalınabilir; ancak **Gri Yaratıklar** karakteri (ve çoğu zaman kurtarabildikleri eşyalarını) en yakın güvenli noktaya / İmparator Heykeli Checkpoint'ine taşır.

### 3.4. Boss Sonu 4'lü Kararsızlık Seçimi
Her Boss yenildiğinde hemen ölmez; diz çöker ve oyuncuya 4 kader yolu açılır:
1. **İnfaz Et (Öldür):** Anında yüksek güç, ganimet ve Can İdolü dolumu sağlar; karanlık eğilimi ve kâbus ağırlığını artırır.
2. **Affet ve Safına Kat:** Müttefik olarak güvenli bölgeye veya ileriki büyük savaşlara katılır.
3. **Gitmesine İzin Ver (Serbest Bırak):** İleriki bölgelerde çok daha güçlenmiş olarak (hatta terk ettiğin bir eğitmenle birleşip **İkili Boss** halinde!) veya en zor anında sürpriz kurtarıcı olarak dönebilir.
4. **Bilgi / Teknik Öğren:** Canını bağışlama karşılığında sadece o Boss'a ait gizli bir kılıç tekniğini, büyüyü veya geçmişine dair kilit bir sırrı alırsın.

---

## 4. PSİKOLOJİK "HER AN KARARSIZ BIRAKMA" SİSTEMLERİ

Oyuncuyu sadece büyük diyaloglarda değil, **en ufak oyun içi eylemde bile** ikilemde bırakan 6 çekirdek mekanik:

1. **Güvenilmez Dış Ses (%50 Doğru / %50 Paranoya):** Kararsızlık Hükümdarı kafanın içinde NPC'ler hakkında fısıldar (*"Koynunda hançer var, sakın arkanı dönme"*). Oyun boyunca bu uyarıların yarısı hayat kurtaran gerçek, yarısı ise oyuncuyu masum birini öldürmeye iten yalandır.
2. **Can Basma & Hafıza Kırıntısı İkilemi:**
   * Can Eşyası (İdol), düşmandan yaşam enerjisi çekerek dolar; sık kullanmak zihinsel bulanıklığı artırır.
   * Bulunan **Hafıza Kırıntılarını** kırıp tüketmek kalıcı Can/Hasar gücü verir **ama o geçmiş anısını sonsuza dek yok eder**; saklamak ise karakteri zayıf bırakır ama gerçeği açar.
3. **Checkpoint'te Dinlenme Bedeli (Zaman İlerlemesi):** Acil olayların yaşandığı bölgelerde İmparator Heykeli'nde dinlenip can doldurmak zamanı ileri sarar; mahzende kurtarılmayı bekleyen isyancıların idam edilmesine yol açabilir.
4. **Zoraki Gülümseme Okuma (Sosyal Gizlilik):** Şehirde herkes gülümser ama dikkatli bakıldığında dudağı titreyen veya gözü dolan NPC'ler gizli direnişçilerdir. İhbar etmek anında muhafız ödülü verir; yardım etmek gizli yeteneklerin kapısını açar.
5. **Canlı Tereddüt Sayacı:** Yol ayrımlarında veya kritik seçim ekranlarında uzun süre hareketsiz kalıp karar verememek Kararsızlık bağını titreştirir ve gölgelerdeki pusu yaratıklarını üzerine çeker.
6. **Kusurlu Güçlü Ekipmanlar (`Trade-off Gear`):** Hiçbir güçlü zırh veya kılıç saf "+Güç" vermez; örneğin *İmparatorluk Muhafız Zırhı* yüksek savunma verir ve askerleri dost yapar ama mazlum halk korkudan kapısını kapatır.

---

## 5. KULLANICI ARAYÜZÜ (UI / HUD) VE SİNEMATİK AKIŞ MİMARİSİ

### 5.1. Sinematik Oyun Açılış Akışı (`Seamless Flow`)
1. **Açılış -> Canlı 3D Ana Menü:** Kısa stüdyo logosundan sonra doğrudan oyun motoru içinde gerçek zamanlı çalışan 3D sahne açılır (*sarmaşıklı sisli ormanda yüzsüz İmparator anıtı, uçuşan küller, saplı kılıç, dumanlı mor kristal ve solda gümüş taş oyma `EMPEROR OF ASH` menüsü*).
2. **`NEW JOURNEY` (İlk Başlangıç Sinematiği):** Karanlık büyü mahzenindeki mor Kararsızlık patlaması -> İki Gri Yaratığın baygın karakteri sarmaşıklı ormana bırakıp çalılara çekilmesi -> Karakterin uyanışı -> Siyah ekran girmeden kameranın omuz arkasına kayıp kontrolü oyuncuya vermesi.
3. **`CONTINUE` (Devam Et Mikro-Sinematiği):** Sıkıcı yükleme ekranı yerine kamera son kalınan İmparator Heykeli Checkpoint'inin dibinde pelerinine sarılıp dinlenen karaktere yaklaşır; karakter derin bir nefes alıp kılıcını yoklayarak ayağa kalkar, pelerininin külünü silker ve kesintisiz olarak oynanış başlar.

### 5.2. Oyun İçi Ekran Arayüzü (`HUD` — Özgün Tasarım İlkeleri)
* **Sol Üst Köşe:** İnce eskitilmiş gümüş çerçeve içinde Can (`HP` - koyu kan kırmızısı), Dayanıklılık (`Stamina` - küllü kehribar) ve Odak/Kararsızlık (` ince dumanlı mor çizgi`).
* **Sol Alt Köşe (4'lü Elmas Hızlı Eşya Çaprazı):**
  * *Üst Yuva:* Can Eşyası (İdol — doluluk ve kalan kullanım adediyle)
  * *Sol Yuva:* Aktif Kılıç / Kalkan / Yay dizilimi
  * *Sağ Yuva:* Aktif Büyü / Keşiş mührü
  * *Alt Yuva:* Kullanılabilir hızlı eşyalar (fırlatma hançeri, sargı vb.)
* **Sağ Alt Köşe:** Savaş dışında sönümlenen minimal Kül Parası / Hafıza sayacı.

---

## 6. NPC VE BOSS KİŞİLİK MİMARİSİ

* Oyundaki hiçbir sokak NPC'si veya Boss tek cümlelik cansız kukla olmayacaktır.
* Her NPC için kendi karakter özelliğine (*korkak, kibirli, fanatik, gizli isyancı, alaycı*) göre yazılmış **10 farklı klasik/durumsal tepki cümlesi** içeren JSON/DataTable havuzu bulunur:
  * Oyuncunun üstündeki kan/kül durumuna, giydiği zırha, saat dilimine ve önceki seçim etiketlerine (`GameplayTags`) göre farklı tepki verir.

---

## 7. TEKNİK MİMARİ VE ÜRETİM BORU HATTI (PRODUCTION PIPELINE)

### 7.1. Geliştirme Donanımı & Disk Yapısı
* **İşlemci & GPU:** AMD Ryzen 7 7800X3D + NVIDIA GeForce RTX 5080 (16 GB VRAM)
* **Disk Düzeni:** Tüm Unreal Engine `5.8.4` projesi (`D:\UE5_Projects`) ve motor önbelleği (`D:\UE5_DDC`) `D:` SSD sürücüsünde tutulur. Paketlenmiş bitmiş oyun hedef boyutu (`IoStore + Oodle` sıkıştırması ile): **15 GB – 28 GB** (İlk Dikey Kesit Demo: **4 GB – 8 GB**).
* **Grafik Ölçeklendirme (`Low / Medium / High / Ultra`):** Modeller bir kez yüksek kalitede üretilir; UE 5.8 **Nanite / Otomatik LOD**, doku **Mipmap (`4K -> 512p`)** ve **Scalability Settings** ile her bilgisayara otomatik uyum sağlar.

### 7.2. Adım Adım 3D, Animasyon, VFX ve Ses Üretim Hattı
1. **2D Konsept & Referans:** ComfyUI `MOSS-Image` (`steps: 45-50, cfg: 3.2`, nötr gri arka planlı fotogerçekçi PBR referansı).
2. **3D Model Üretimi:** ComfyUI `TRELLIS.2` (`.glb` çıktısı).
3. **PBR Yükseltme & Yumuşatma Köprüsü:** Blender `5.3.0` (`scripts/kararsizlik_pipeline_bridge.py` özel eklentisi ile `Weld + Pin-Boundary Smooth`, kararmış çelik + parlayan kristal PBR kurulumu ve kullanıcı onayıyla Unreal `AutoImport` klasörüne aktarım).
4. **Animasyon & Sinematik:**
   * *İnsan Hareketleri:* UE 5.8 `Game Animation Sample (GASP)` + `Mixamo / Fab` mocap + `Cascadeur` AI fizik düzeltme.
   * *Grotesk Yaratıklar:* UE 5.8 `Control Rig` (Prosedürel çok bacaklı IK) + `AnimDynamics / Chaos Cloth` fiziksel kol/saç salınımı.
   * *Sinematikler:* UE 5.8 `Level Sequencer` + `Cine Camera Actor` + Telefon videosundan AI Mocap + `MetaHuman Audio-to-Face`.
5. **Efektler (VFX) & Ses:**
   * *Sis, Buhar & Büyü:* `Exponential Height Fog (Volumetric)` + `Niagara` parçacık sistemleri + el/silah yanma *Dissolve Shader*'ları.
   * *Ses & Müzik:* UE 5.8 `MetaSounds` dinamik katmanlı müzik/vuruş sesleri + yerel AI TTS ile yankılı Dış Ses / Boss seslendirmeleri.
6. **Kayıt & Seçim Hafızası:** Merkezi `UGameInstanceSubsystem` + `GameplayTags` (`World.Boss.X.Spared`, `Player.Trainer.Y.Abandoned`, `Player.HesitationScore`).

---

## 8. ÜRETİM YOL HARİTASI (5 AŞAMALI UYGULAMA PLANI)

### Aşama 1 — Motor Kurulumu & Master Material *(Gün 1)*
- [ ] `D:\UE5_Projects\EmperorOfAsh` projesini UE `5.8.4` ile oluşturmak.
- [ ] Karanlık Dövme Çelik, Eskitilmiş Taş ve Parlayan Mor Kristal için tek bir **Ana Master Material** kurmak.

### Aşama 2 — Gri Kutu Savaş Test Odası (`Combat Gym`) *(Hafta 1)*
- [ ] Üçüncü şahıs kamera, hedefe kilitlenme (`Lock-On`), `HP / Stamina / Odak` barları.
- [ ] Hançer, Kılıç, Kalkan ve Yay kuşanma; animasyon iptalli akıcı saldırı, `Dodge` (`i-frame`), `Parry/Blok`, `Weapon Sweep Trace` hitbox ve `Hitstop`.
- [ ] Can Eşyası (İdol) kullanma animasyonu ve iyileşme döngüsü.

### Aşama 3 — Yapay Zekâ Düşman, Boss Seçimi & Kayıt Defteri *(Hafta 2)*
- [ ] UE 5.8 `StateTree` ile temel muhafız/yaratık yapay zekâsı.
- [ ] Boss `%5` canda diz çökme sekansı, Güvenilmez Dış Ses fısıltısı ve 4'lü Kararsızlık Seçim ekranı + `GameplayTags` kayıt sistemi.

### Aşama 4 — Bayılma, Kâbus ve Gri Yaratıklar Döngüsü *(Hafta 3)*
- [ ] Can sıfırlanınca bayılma geçişi, kısa Kâbus koridoru prototipi ve Gri Yaratıkların son İmparator Heykeli Checkpoint'ine bırakma mekaniği.

### Aşama 5 — İlk 15 Dakikalık Oynanabilir Dikey Kesit (`Vertical Slice`) & Sinematikler *(Hafta 4)*
- [ ] **Giriş Bölgesi İnşası:** Sarmaşıklı sisli karanlık orman açıklığı -> İlk İmparator Heykeli Checkpoint -> Taş Köprü Mini-Boss -> Sisli Küçük Şehir Kapısı ve zoraki gülümseyen ilk NPC'ler.
- [ ] **Özgün UI & Sinematik Giydirme:** Kendi tasarladığımız `EMPEROR OF ASH` Canlı 3D Ana Menüsü, HUD çerçeveleri, `New Journey` açılış sinematiği ve `Continue` heykel dibinden kalkış mikro-sinematiği.
