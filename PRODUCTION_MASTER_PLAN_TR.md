# EMPEROR OF ASH: THE FORGOTTEN RETURN
## Profesyonel Stüdyo Üretim, Sprint ve Kilometre Taşı Planı (Studio Production Master Plan v1.1)

> **Stüdyo Metodolojisi:** Çevik (Agile) Dikey Kesit Odaklı Oyun Üretimi (*Core Loop First -> Greybox -> Vertical Slice -> Content Scaling -> Polish*)  
> **Proje Yöneticisi & Baş Geliştirici:** Tek Ana Üretim İstasyonu (`Ryzen 7 7800X3D` + `RTX 5080 16 GB` + `D:\UE5_Projects`) + Yaratıcı Tasarım Ortağı  
> **Motor & Araç Zinciri:** Unreal Engine `5.8.4` | Blender `5.3.0` | ComfyUI (`MOSS-Image` + `TRELLIS.2`) | Yerel LLM (`9B` / `27B`)

---

## 1. STÜDYO ÜRETİM AŞAMALARI VE KİLOMETRE TAŞLARI (MACRO MILESTONES)

Profesyonel oyun stüdyolarında bir oyun **6 kilit kapıdan (`Gate`)** geçerek yapılır; bir kapının kriteri bitmeden diğerine geçilmez:

| Kapı (Gate) | Faz Adı | Odak Noktası | "Bitti Sayılma" Kriteri (Exit Criteria / Gate Check) |
| :--- | :--- | :--- | :--- |
| **GATE 0** | **Ön-Üretim (Pre-Production)** ✅ *TAMAMLANDI* | GDD, teknik boru hattı, 3D PBR testi, disk & motor hazırlığı | `MOSS -> TRELLIS.2 -> Blender PBR -> UE 5.8` hattı kanıtlandı; GDD v1.0 yazıldı. |
| **GATE 1** | **Savaş Prototipi (`Combat Gym`)** | Gri odada kamera, hareket, kılıç/yay/büyü vuruş hissi, dodge, hitbox | Kaplamasız gri kutu odada bile 10 dakika sıkılmadan savaşmak keyifli ve akıcı (`60+ FPS`). |
| **GATE 2** | **Sistem Prototipi (`Core Loop`)** | Yapay zekâ, Boss 4'lü seçim, bayılma->kâbus, kayıt (`GameplayTags`), NPC diyalog | Baştan sona 1 tam döngü (*Savaş -> Seçim Yap -> Bayıl -> Kâbustan Çık -> Kaydet/Yükle*) hatasız çalışır. |
| **GATE 3** | **Dikey Kesit (`Vertical Slice`)** ⭐ *EN KRİTİK KAPI* | 15–20 dk'lık final kalitede oynanabilir başlangıç bölümü + Ana Menü + Sinematikler | Oyunun bitmiş halinin %100 görsel, ses ve mekanik kalitesini temsil eden tek kusursuz bölüm. |
| **GATE 4** | **Üretim & İçerik Genişleme (`Alpha`)** | Tüm bölgeler, tüm eğitmenler, tüm Bosslar ve 3 Büyük Sonun uçtan uca bağlanması | Oyun baştan sona bitirilebilir (*Feature Complete* — görsel eksikler/placeholder olabilir). |
| **GATE 5** | **Cila, Optimizasyon & Paketleme (`Beta -> Gold`)** | Bug temizliği, `Low/Med/High/Ultra` FPS testi, ses miksajı, `IoStore` paketleme | Sıfır çökme (*Crash-Free*), hedef donanımda stabil FPS, `15–28 GB` temiz kurulum paketi. |

---

## 2. TEKNİK METRİKLER VE OYUN STANDARTLARI TABLOSU ("THE METRICS BIBLE")

> Profesyonel stüdyolarda harita ve animasyon yapılmadan önce **santimetre ve milisaniye kuralları** dondurulur ki karakter kapıya sıkışmasın, kılıç ağır/kütük kalmasın:

### 2.1. Karakter & Hareket Metrikleri (UE 5.8 Birimi: `1 UU = 1 cm`)
| Parametre | Standart Değer | Açıklama |
| :--- | :--- | :--- |
| **Karakter Boyu / Kapsül** | `180 cm` boy / `34 cm` yarıçap | Hurtbox (hasar kapsülü) adil his için görselden %15 ince (`~29 cm`) tutulur. |
| **Normal Yürüyüş / Koşu / Sprint** | `220 cm/s` / `480 cm/s` / `650 cm/s` | Ağırbaşlı karanlık ortaçağ ağırlığı verir ama hantal hissettirmez. |
| **Koridor / Kapı Minimum Genişliği** | Kapı: `250 cm` / Savaş Koridoru: `600+ cm` | Üçüncü şahıs kameranın duvara çarpıp oyuncuyu kör etmemesi için zorunlu ölçü. |
| **Merdiven / Basamak Yüksekliği** | Maksimum `20–25 cm` | Karakterin takılmadan çıkabileceği basamak sınırı. |

### 2.2. Akıcı Savaş Zamanlama Çerçevesi (`60 FPS` Bazında Milisaniye Cetveli)
| Eylem | Hazırlık (`Startup`) | Aktif Vuruş (`Active`) | Toparlanma & İptal (`Recovery / Cancel`) |
| :--- | :--- | :--- | :--- |
| **Hançer Hızlı Kesiş** | `0.15 sn` | `0.10 sn` (Sweep Trace açık) | `0.12 sn`'den itibaren Dodge/Kombo ile **iptal edilebilir!** |
| **Uzun Kılıç Standart Darbe** | `0.28 sn` | `0.14 sn` (Sweep Trace açık) | `0.20 sn`'den itibaren Dodge/Blok ile **iptal edilebilir!** |
| **Kaçınma (`Dodge Step / Roll`)** | `0.05 sn` | **`0.35 sn` Tam Dokunulmazlık (`i-Frame`)** | Toplam süre `0.60 sn` |
| **Kalkan Savuşturma (`Parry`)** | `0.08 sn` | **`0.18 sn` Aktif Parry Penceresi** | Başarılıysa düşmanda `1.8 sn` Denge Kırılması (*Stagger*) |
| **İsabet Duraksaması (`Hitstop`)** | Hafif vuruş: `0.04 sn` | Ağır/Kritik vuruş: `0.08 sn` | Kamera mikro sarsıntısı + kan/kıvılcım Niagara efektiyle senkronize |

---

## 3. SPRINT BAZLI İŞ PAKETLERİ (WORK BREAKDOWN STRUCTURE — WBS)

Her Sprint **2 Haftalık** odaklanmış üretim dilimlerinden oluşur (**Önce Mekanik -> Sonra Sanat -> En Son Sinematik**):

### 🟦 SPRINT 1: Motor Çekirdeği & Savaş Odası (`Combat Gym — Bölüm 1`)
* [ ] **`ENG-01`** `D:\UE5_Projects\EmperorOfAsh` (UE `5.8.4`) kurulumu, klasör hiyerarşisi (`/Core`, `/Combat`, `/AI`, `/UI`, `/Art`, `/Cinematics`, `/Audio`).
* [ ] **`ART-01`** `M_Master_DarkPBR` ana materyalinin kurulumu (Metalik, Roughness, Normal, Emission parametreleriyle).
* [ ] **`CMB-01`** `GASP` tabanlı hareket + `Target Lock-On` (Düşmana kilitlenme ve etrafında strafe/adımlama kamerası).
* [ ] **`CMB-02`** Silah kuşanma soketleri (`hand_r` Kılıç/Hançer, `hand_l` Kalkan/Yay) ve `Weapon Sweep Trace` çarpışma sistemi.
* [ ] **`CMB-03`** 3'lü hafif kombo + 1 ağır saldırı + Animasyon İptali (`AnimNotifyState_CancelWindow`) + `Dodge i-Frame` + `Hitstop`.

### 🟦 SPRINT 2: Yay, Büyü, Can Eşyası ve Oyun Durum Hafızası (`Combat Gym — Bölüm 2`)
* [ ] **`CMB-04`** Kalkan Blok (`Stamina` tüketimi) ve `Parry` (denge kırma + infaz vuruşu).
* [ ] **`CMB-05`** Okçuluk sistemi (omuz üstü nişan kamerası, yay germe süresi, ok mermi fiziği) + İlk Kararsızlık Büyüsü.
* [ ] **`SYS-01`** Can Basma Eşyası altyapısı *(Eşyanın kesin görsel/hikâye tasarımına daha sonra karar verilecek; önce kod altyapısı kurulacak)*.
* [ ] **`SYS-02`** Merkezi `UGameInstanceSubsystem` + `GameplayTags` Kayıt/Yükleme (`Save/Load`) mimarisi.

### 🟦 SPRINT 3: Düşman AI, Boss 4'lü Kararsızlık Seçimi & NPC Sistemi
* [ ] **`AI-01`** UE 5.8 `StateTree` ile Yakın Dövüşçü Muhafız ve Okçu/Yaratık yapay zekâsı (devriye, fark etme, saldırı, blok).
* [ ] **`AI-02`** Mini-Boss tasarımı + `%5 HP` Diz Çökme durumu -> Zaman yavaşlaması -> Güvenilmez Dış Ses -> **4'lü Kararsızlık Seçimi** (`Öldür / Affet / Bırak / Öğren`).
* [ ] **`SYS-03`** JSON / DataTable tabanlı **10 Kişilik Tepkili** NPC Diyalog & Tereddüt Sayacı sistemi.
* [ ] **`SYS-04`** Eğitmen (Trainer) başlangıç/bırakma altyapısı (terk edilen eğitmenin durum etiketinin değişmesi).

### 🟦 SPRINT 4: Ölümsüzlük, Bayılma, Kâbus Boyutu & Checkpoint Döngüsü
* [ ] **`SYS-05`** `HP == 0` olduğunda bayılma sekansı -> Şehirdeyse eşya/para kaybı kontrolü -> Kâbus Haritasına geçiş.
* [ ] **`LVL-01`** Kâbus koridoru prototipi (sis, aşağı çeken eller efekti, ufukta çatlayan dolunay tetikleyicisi).
* [ ] **`SYS-06`** Gri Yaratıkların kurtarma mantığı ve Checkpoint dinlenme sistemi.

### 🟦 SPRINT 5: Giriş Bölgesi İnşası (`Sarmaşıklı Karanlık Orman -> Küçük Şehir Girişi`)
* [ ] **`LVL-02`** 350 metrelik başlangıç haritasının **Greybox (Gri Kutu)** inşası ve yürüyüş/savaş mesafesi testi.
* [ ] **`ART-02`** UE5 Landscape + Megascans sarmaşık, ıslak kaya, çamur, ağaçlandırma (`PCG`) + `Exponential Height Fog` (Hacimsel Sis) ve `Lumen` karanlık alacakaranlık ışıklandırması.
* [ ] **`ART-03`** ComfyUI -> Blender köprüsüyle üretilen imza yapıların yerleştirilmesi.

### 🟦 SPRINT 6: Özgün UI/HUD, Ses Miksajı & Gerçek Zamanlı Sinematikler (`Vertical Slice Tamamlama!`)
* [ ] **`UI-01`** Kendi tasarlayacağımız `EMPEROR OF ASH` **Canlı 3D Ana Menüsü**, Sol Üst `HP/Stamina/Odak` barları ve Sol Alt **4'lü Elmas Eşya Çaprazı**.
* [ ] **`CIN-01`** `Level Sequencer` ile **1) `New Journey` Mahzen Patlaması & Ormanda Uyanış Sinematiği** (Gri Yaratıkların çalılara kaçışı + kesintisiz oynanışa geçiş).
* [ ] **`CIN-02`** `Level Sequencer` ile **2) `Continue` Dinlenme Noktasından Kalkış Mikro-Sinematiği** ve **3) Köprü Mini-Boss Giriş Sinematiği**.
* [ ] **`AUD-01`** `MetaSounds` kılıç, yay, adım, orman rüzgârı, şehir uğultusu ve Kararsızlık Hükümdarı yankılı Dış Ses seslendirmeleri.
* [ ] **`QA-01`** `Low / Medium / High / Ultra` grafik ayarları testi ve ilk paketlenmiş `.exe` **Vertical Slice Demo** çıktısı!

---

## 4. DİKEY KESİT (VERTICAL SLICE) VARLIK LİSTESİ (ASSET TRACKER MATRIX)

> İlk 20 dakikalık oynanabilir vitrin bölümü için üretilecek odaklı varlık listesi:

| Kategori | Varlık Adı | Üretim Yöntemi | Poligon / Doku Hedefi | Durum / Açık Karar Notu |
| :--- | :--- | :--- | :--- | :--- |
| **Karakter** | Ana Kahraman (Yöre Kıyafetli + Pelerinli) | MOSS -> TRELLIS.2 -> Mixamo/GASP Rig | `35K–50K Tri` / `4K PBR` | 🔜 Sırada |
| **Karakter** | **Hükümdarın Yüzünü Kapatan Unsur** *(Maske sadece örnekti!)* | MOSS -> TRELLIS.2 -> Blender PBR | `8K Tri` / `2K PBR` | ⏳ **Bu Hafta Belirlenecek** |
| **Yaratık** | Gri Yaratıklar (Sıska İkili) | MOSS -> TRELLIS.2 -> Rig + Jitter | `20K Tri` / `2K PBR` | 🔜 Sırada |
| **Boss** | Köprü Muhafızı / İlk Kararsızlık Yaratığı | MOSS -> TRELLIS.2 -> Control Rig / GASP | `40K Tri` / `4K PBR` | 🔜 Sırada |
| **NPC** | Zoraki Gülümseyen Şehirli (2 Varyasyon + Eğitmen) | MetaHuman / TRELLIS.2 + Gülümseme ShapeKey | `30K Tri` / `2K PBR` | 🔜 Sırada |
| **Silah/Eşya** | **Can Basma Eşyası** *(İdol sadece 3D PBR testiydi!)* | MOSS -> TRELLIS.2 -> Blender PBR | `10K Tri` / `2K PBR` | ⏳ **Daha Sonra Karar Verilecek** |
| **Silah/Eşya** | Başlangıç Hançeri, Demir Kılıç, Kalkan, Uzun Yay | MOSS -> TRELLIS.2 -> Blender PBR | `5K–8K Tri` / `2K PBR` | 🔜 Sırada |
| **Çevre** | İmparator Heykeli / Checkpoint *(Yüzü kapatan unsura göre kesinleşecek)* | MOSS -> TRELLIS.2 -> Blender PBR + Nanite | Nanite / `4K Stone PBR` | 🧪 Konsept Denendi |
| **Çevre** | Taş Kemerli Köprü & Küçük Şehir Surları/Kapısı | Modüler Blender + Megascans Sarmaşık/Doğa | Nanite / `2K–4K Tileable` | 🔜 Sırada |

---

## 5. PROFESYONEL RİSK YÖNETİMİ VE "KAPSAM ŞİŞMESİ" (SCOPE CREEP) KALKANI

| Tehlike (Risk) | Stüdyo Çözüm Kuralı |
| :--- | :--- |
| **"Haritayı çok büyük yapıp boş kalması"** | Açık dünya çölü YASAK! *Dark Souls 1 / Lies of P* gibi **birbirine kestirme kapılarla bağlanan yoğun, atmosferik, dolu koridor-bölgeler** yapılacak. |
| **"Mekanik bitmeden 50 tane silah modellemek"** | `Sprint 1–2` bitip tek kılıçla savaş kusursuz olmadan 2. kılıcı modellemek YASAK! |
| **"Kayıt sistemini sona bırakmak"** | Seçim odaklı RPG olduğu için `GameplayTags + SaveGame` daha `Sprint 2`'de kurulacak. |
| **"Performansın sonradan çökmesi (`FPS Drop`)"** | Her Cuma 10 dakikalık `Stat Unit / Stat GPU` kontrolü yapılacak; küçük objelerde 4K kaplama kullanılmayacak, UE 5.8 `Nanite` aktif tutulacak. |

---

## 6. UNREAL ENGINE `5.8.4` STANDART KLASÖR MİMARİSİ (`D:\UE5_Projects\EmperorOfAsh`)

```text
/Content
 ├── /Core               -> (GM_Emperor, GI_WorldStateSubsystem, BP_SaveGame)
 ├── /Characters
 │    ├── /Hero          -> (BP_Hero, SK_Hero, ABP_Hero)
 │    ├── /Bosses        -> (BP_Boss_Bridge, ST_BossAI)
 │    ├── /NPCs          -> (BP_NPC_Base, DT_NPCDialogues)
 │    └── /GreyOnes      -> (BP_GreyCreature)
 ├── /Combat
 │    ├── /Weapons       -> (BP_Weapon_Base, SM_Dagger, SM_Sword, SM_Shield, SM_Bow)
 │    ├── /HealingItem   -> (BP_HealingItem_Base — kesin tasarım sonra belirlenecek)
 │    └── /Animations    -> (AM_SwordCombo, AM_Dodge, AM_Parry)
 ├── /Materials          -> (M_Master_DarkPBR, MI_BlackenedIron, MI_AmethystGlow)
 ├── /Maps
 │    ├── L_MainMenu_3D  -> (Canlı 3D Ana Menü Sahnesi)
 │    ├── L_CombatGym    -> (Gri Kutu Savaş Test Odası)
 │    ├── L_Act1_Forest  -> (Sarmaşıklı Orman & Şehir Girişi)
 │    └── L_Nightmare_01 -> (Bayılma Kâbus Sekansı)
 ├── /Cinematics         -> (LS_Prologue_Explosion, LS_Continue_WakeUp, LS_BossIntro)
 ├── /UI                 -> (WBP_HUD_Main, WBP_MainMenu, WBP_MoralChoice4)
 ├── /VFX                -> (NS_PurpleExplosion, NS_AshFloating)
 └── /Audio              -> (MS_SwordSwing, MS_ForestAmbience, VO_IndecisionRuler)
```
