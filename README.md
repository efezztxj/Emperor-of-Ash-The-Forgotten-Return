# Emperor of Ash: The Forgotten Return (KARARSIZLIK)

Karanlık fantastik üçüncü şahıs Aksiyon-RPG projesi. Aydınlık, karanlık ve kararsızlık arasında sıkışmış bir dünyada; 600 yıllık zalim imparatorluğunu sona erdirmek için kendi hafızasını feda eden ölümsüz bir hükümdarın uyanış hikâyesi.

## 📂 Repo İçeriği

* **`PRODUCTION_MASTER_PLAN_TR.md`** — **Profesyonel Stüdyo Üretim, Sprint & Kilometre Taşı Planı (`Gate 0 -> Gold Master`):** Sprint iş paketleri (`ENG/CMB/AI/SYS/LVL/CIN`), santimetre ve milisaniye savaş cetveli (*The Metrics Bible*), varlık takip matrisi *(yüzü kapatan unsur bu hafta, can eşyası daha sonra belirlenecek notuyla)* ve resmi UE `5.8.4` klasör mimarisi.
* **`GAME_DESIGN_DOCUMENT_TR.md`** — **Resmi Oyun Tasarım ve Teknik Mimari Dokümanı (GDD v1.0):** Hikâye, sınıfsız melez sistem, akıcı savaş mimarisi, "her an kararsız bırakma" psikolojisi, sinematik açılış/`Continue` akışı, HUD prensipleri, üretim hattı ve 5 aşamalı geliştirme planı.
* **`Kararsizlik_Oyun_Evreni_ve_Hikaye_Taslagi (1).pdf`** — Oyunun temel hikâyesi, evreni, karakter geçmişi, sınıf sistemi ve Kararsızlık Evreni başlangıç taslağı.
* **`AI_HAFIZA_VE_KISILIK_REHBERI.md`** — Yerel yapay zekâ modelleri (`9B` / `27B`), tasarım kuralları (ateşli silah yok; kılıç, kalkan, yay, büyü ve keşiş disiplinleri), psikolojik kararsızlık sistemleri, ComfyUI (`MOSS-Image` + `TRELLIS.2`) -> Blender 5.3.0 -> Unreal Engine 5.8.4 teknik üretim hattı ve **Yapılacaklar Yol Haritası (TODO)**.
* **`scripts/kararsizlik_config.json`** — Tüm klasör ve port yollarının tutulduğu merkezi konfigürasyon dosyası (`D:\UE5_Projects\EmperorOfAsh_Bridge` uyumlu).
* **`scripts/blender_trellis_pbr_upgrader.py`** — TRELLIS.2 `.glb` modelleri için **3 Materyal Profilli** (`METAL_CRYSTAL`, `STONE_RUIN`, `WOOD_LEATHER`) Blender 5.x PBR scripti.
* **`scripts/kararsizlik_pipeline_bridge.py`** — **Özel Blender 5.x Köprü Eklentisi (`v2.0.0`):** Materyal profili seçici, otomatik Pivot/Ölçek standardı (`Zemin Z=0` / `Silah Kabzası`), Poligon bütçesi (`Decimate`), otomatik **`UCX_` çarpışma kabuğu** (`FBX + GLB`) ve onaylı `ApprovedStaging` + Unreal 5.8.4 `AutoImport` aktarımı!
* **`scripts/kararsizlik_oto_fabrika.py`** — **RTX 5080 (16 GB VRAM) Korumalı Orkestra Şefi:** Negatif prompt korumalı pozitif düğüm hedefleme, ComfyUI hata/timeout yakalama ve VRAM boşaltma (`/free`) ile 2D -> 3D üretim akışı.
* **`scripts/kararsizlik_lmstudio_mcp.py`** — **LM Studio MCP Skill Sunucusu:** Ham `.glb` yerine Blender'da temizlenmiş (`ApprovedStaging`) modelleri Unreal 5.8.4'e aktaran güvenli MCP sunucusu.
* **`concept_art/`** — İlk prototip/deneme konsept referansları (Checkpoint heykeli ve Can Eşyası İdolü denemeleri).

## 🛠️ Kurulu & Hazır Ana Araçlar (Ryzen 7 7800X3D + RTX 5080)

1. **ComfyUI Desktop (`MOSS-Image` + `TRELLIS.2`):** ✅ Kurulu — 2D konsept ve `.glb` 3D model üretimi.
2. **Yerel LLM (`9B` & `27B`):** ✅ Kurulu — Diyalog/prompt üretimi ve Blender Python (`bpy`) / sistem kod otomasyonu.
3. **Blender 5.3.0 (`OptiX RTX 5080`):** ✅ Kurulu — `.glb` temizliği, gerçekçi PBR materyal/kristal shader ataması (`scripts/blender_trellis_pbr_upgrader.py`) ve modüler sahne birleştirme.
4. **Unreal Engine 5.8.4 & Git LFS:** ✅ Kurulu — Harita, akıcı ortaçağ yakın dövüş/okçuluk/büyü savaş sistemi, hacimsel sis, Niagara büyü efektleri ve 2 kişilik çakışmasız ortak çalışma altyapısı.
