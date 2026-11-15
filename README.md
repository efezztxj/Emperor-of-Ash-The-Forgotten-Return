# Emperor of Ash: The Forgotten Return (KARARSIZLIK)

Karanlık fantastik üçüncü şahıs Aksiyon-RPG projesi. Aydınlık, karanlık ve kararsızlık arasında sıkışmış bir dünyada; 600 yıllık zalim imparatorluğunu sona erdirmek için kendi hafızasını feda eden ölümsüz bir hükümdarın uyanış hikâyesi.

## 📂 Repo İçeriği

* **`Kararsizlik_Oyun_Evreni_ve_Hikaye_Taslagi (1).pdf`** — Oyunun temel hikâyesi, evreni, karakter geçmişi, sınıf sistemi ve Kararsızlık Evreni başlangıç taslağı.
* **`AI_HAFIZA_VE_KISILIK_REHBERI.md`** — Yerel yapay zekâ modelleri (`9B` / `27B`), tasarım kuralları (ateşli silah yok; kılıç, kalkan, yay, büyü ve keşiş disiplinleri), psikolojik kararsızlık sistemleri, ComfyUI (`MOSS-Image` + `TRELLIS.2`) -> Blender -> Unreal Engine 5 teknik üretim hattı ve **Yapılacaklar Yol Haritası (TODO)**.
* **`concept_art/`** — İlk prototip/deneme konsept referansları (Checkpoint heykeli ve Can Eşyası İdolü denemeleri).

## 🛠️ Kurulacak & Kullanılacak Ana Araçlar

1. **ComfyUI Desktop (`MOSS-Image` + `TRELLIS.2`):** ✅ Kurulu — 2D konsept ve `.glb` 3D model üretimi.
2. **Yerel LLM (`9B` & `27B`):** ✅ Kurulu — Diyalog/prompt üretimi ve Blender Python (`bpy`) / sistem kod otomasyonu.
3. **Blender (4.2 LTS+):** 🔜 Kurulacak — `.glb` temizliği, gerçekçi PBR materyal/kristal shader ataması ve modüler sahne birleştirme.
4. **Unreal Engine 5:** 🔜 Kurulacak — Harita, akıcı ortaçağ yakın dövüş/okçuluk/büyü savaş sistemi, hacimsel sis ve Niagara büyü efektleri.
5. **AccuRIG & Git LFS:** 🔜 Kurulacak — Otomatik karakter iskeletlendirme ve 2 kişilik çakışmasız ortak çalışma altyapısı.
