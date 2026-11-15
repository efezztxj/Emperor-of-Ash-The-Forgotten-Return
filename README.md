# Emperor of Ash: The Forgotten Return (KARARSIZLIK)

Karanlık fantastik üçüncü şahıs Aksiyon-RPG projesi. Aydınlık, karanlık ve kararsızlık arasında sıkışmış bir dünyada; 600 yıllık zalim imparatorluğunu sona erdirmek için kendi hafızasını feda eden ölümsüz bir hükümdarın uyanış hikâyesi.

## 📂 Repo İçeriği

* **`Kararsizlik_Oyun_Evreni_ve_Hikaye_Taslagi (1).pdf`** — Oyunun temel hikâyesi, evreni, karakter geçmişi, sınıf sistemi ve Kararsızlık Evreni başlangıç taslağı.
* **`AI_HAFIZA_VE_KISILIK_REHBERI.md`** — Yerel yapay zekâ modelleri (`9B` / `27B`), tasarım kuralları (ateşli silah yok; kılıç, kalkan, yay, büyü ve keşiş disiplinleri), psikolojik kararsızlık sistemleri, ComfyUI (`MOSS-Image` + `TRELLIS.2`) -> Blender 5.3.0 -> Unreal Engine 5.8.4 teknik üretim hattı ve **Yapılacaklar Yol Haritası (TODO)**.
* **`scripts/blender_trellis_pbr_upgrader.py`** — TRELLIS.2'den çıkan düz `.glb` modelleri Blender'da tek tıkla gerçekçi dövme çelik + içten parlayan kristal PBR materyaline ve sinematik ışıklandırmaya çeviren hazır Python (`bpy`) scripti.
* **`concept_art/`** — İlk prototip/deneme konsept referansları (Checkpoint heykeli ve Can Eşyası İdolü denemeleri).

## 🛠️ Kurulu & Hazır Ana Araçlar (Ryzen 7 7800X3D + RTX 5080)

1. **ComfyUI Desktop (`MOSS-Image` + `TRELLIS.2`):** ✅ Kurulu — 2D konsept ve `.glb` 3D model üretimi.
2. **Yerel LLM (`9B` & `27B`):** ✅ Kurulu — Diyalog/prompt üretimi ve Blender Python (`bpy`) / sistem kod otomasyonu.
3. **Blender 5.3.0 (`OptiX RTX 5080`):** ✅ Kurulu — `.glb` temizliği, gerçekçi PBR materyal/kristal shader ataması (`scripts/blender_trellis_pbr_upgrader.py`) ve modüler sahne birleştirme.
4. **Unreal Engine 5.8.4 & Git LFS:** ✅ Kurulu — Harita, akıcı ortaçağ yakın dövüş/okçuluk/büyü savaş sistemi, hacimsel sis, Niagara büyü efektleri ve 2 kişilik çakışmasız ortak çalışma altyapısı.
