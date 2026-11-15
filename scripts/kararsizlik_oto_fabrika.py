#!/usr/bin/env python3
"""
KARARSIZLIK — Tek Cumleden 2D -> Bekle -> 3D (.glb) -> Bekle -> Blender PBR & Onayli Unreal 5.8 Oto-Fabrika!
RTX 5080 (16 GB VRAM) korumali Orkestra Sefi (Sifir ek kutuphane ister — standart Python 3 ile calisir!)

Nasil Calisir?
1. Sen Turkce/Ingilizce ne istedigini yazarsin (orn: "Kirik imparator kilici, kararmis demir ve mor rünlü").
2. (Opsiyonel) LM Studio Server aciksa yerel AI bunu profesyonel Ingilizce MOSS-Image 3D-girdi promptuna cevirir;
   LM Studio kapaliysa bile kendi dahili 'Grounded Dark Medieval PBR' sablonuyla otomatik cevirir!
3. Acik olan ComfyUI'ye (http://127.0.0.1:8000 veya 8188) MOSS-Image API istegi yollar ve GÖRSEL BİTENE KADAR BEKLER!
4. Cikan görseli otomatik olarak TRELLIS.2 API is akisina baglar ve .GLB 3D MODEL BİTENE KADAR BEKLER!
5. .glb dosyasi ComfyUI output\3d klasorune dustugu saniye:
   - Acik olan Blender'daki 'Canli Oto-Yakalayici' (kararsizlik_pipeline_bridge.py v1.3+) onu HAVADA YAKALAR,
   - Otomatik yumusatir, kararmis celik + parlayan mor kristal PBR materyali ve isigini kurar!
6. Sen Blender'da bakip begendigin an tek tusla (veya bu ekranda 'E' yazarak) Unreal Engine 5.8.4'e onaylayip gonderirsin!

Ilk Kurulum (Sadece 1 Kere — 30 Saniye!):
1. ComfyUI'de Settings (Çark ikonu) -> 'Enable Dev mode Options' kutucugunu ac.
2. MOSS-Image is akisini ac -> Ust menuden Workflow -> 'Export (API)' tikla ->
   Bu scriptin yanina `workflows/moss_2d_api.json` adiyla kaydet.
3. TRELLIS.2 Image-to-3D is akisini ac -> Ust menuden Workflow -> 'Export (API)' tikla ->
   Bu scriptin yanina `workflows/trellis_3d_api.json` adiyla kaydet.
"""

import glob
import json
import os
import random
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


# ================= KULLANICI KLASÖR VE PORT AYARLARI =================
COMFY_CANDIDATE_URLS = [
    "http://127.0.0.1:8000",  # ComfyUI Desktop varsayilan portu
    "http://127.0.0.1:8188",  # Standart ComfyUI portu
]
LM_STUDIO_API_URL = "http://127.0.0.1:1234/v1/chat/completions"

COMFY_BASE_OUTPUT = r"C:\Users\efezz\AppData\Local\Comfy-Desktop\ComfyUI-Shared\output"
COMFY_3D_OUTPUT = os.path.join(COMFY_BASE_OUTPUT, "3d")
UNREAL_AUTOIMPORT_DIR = r"C:\KARARSIZLIK_UnrealBridge\AutoImport"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MOSS_API_JSON = os.path.join(SCRIPT_DIR, "workflows", "moss_2d_api.json")
TRELLIS_API_JSON = os.path.join(SCRIPT_DIR, "workflows", "trellis_3d_api.json")
# =====================================================================


DARK_PBR_STYLE_SUFFIX = (
    ", single standalone dark medieval artifact centered on a clean neutral grey background, "
    "full object visible from top to bottom, museum-grade photorealistic 3D scan reference, "
    "weathered hand-forged blackened iron, tarnished aged bronze, subtle deep smoky amethyst crystal, "
    "physically based material definition, zero motion blur, no hands, no text, NOT stylized MMO"
)


def detect_comfy_url():
    for url in COMFY_CANDIDATE_URLS:
        try:
            req = urllib.request.Request(f"{url}/system_stats", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    return url
        except Exception:
            continue
    return None


def build_english_prompt(user_idea: str) -> str:
    """LM Studio aciksa hafif modelle cevirir; kapaliysa VRAM harcamadan yerlesik sablonla olusturur."""
    system_msg = (
        "Convert the user's Turkish dark medieval RPG item/prop idea into ONE concise English image generation prompt "
        "(45-70 words) suitable for 3D reconstruction: single isolated object centered on a clean solid grey studio "
        "background, photorealistic weathered forged iron/stone/aged wood/dark amethyst PBR textures, medieval fantasy "
        "(swords, shields, bows, statues, masks, relics ONLY — NO firearms). Output ONLY the English prompt."
    )
    payload = json.dumps({
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_idea},
        ],
        "temperature": 0.4,
        "max_tokens": 180,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            LM_STUDIO_API_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data["choices"][0]["message"]["content"].strip()
            if text:
                print("[AI Prompt] LM Studio ile profesyonel Ingilizce prompt uretildi!")
                return text + DARK_PBR_STYLE_SUFFIX
    except Exception:
        pass

    # LM Studio kapaliysa (16 GB VRAM'in %100'unu ComfyUI'ye birakmak icin ideal mod!)
    tr_to_en_hints = {
        "kılıç": "medieval dark forged greatsword",
        "kilic": "medieval dark forged greatsword",
        "hançer": "ornate dark medieval ritual dagger",
        "hancer": "ornate dark medieval ritual dagger",
        "kalkan": "battle-worn blackened iron medieval shield",
        "yay": "carved ash-wood and blackened iron medieval longbow",
        "maske": "regal serene King Baldwin IV style full-face silver and iron mask with zero exposed skin",
        "heykel": "eroded faceless ancient dark emperor stone statue checkpoint",
        "idol": "handheld vertical dark empire forged iron and amethyst crystal relic",
        "asa": "ancient dark sorcerer staff with smoky purple crystal",
    }
    matched = [en for tr, en in tr_to_en_hints.items() if tr in user_idea.lower()]
    prefix = ", ".join(matched) + f" ({user_idea})" if matched else user_idea
    return f"Photorealistic dark medieval {prefix}{DARK_PBR_STYLE_SUFFIX}"


def inject_prompt_into_moss_workflow(workflow: dict, prompt_text: str) -> dict:
    wf = json.loads(json.dumps(workflow))
    seed = random.randint(1, 2**31 - 1)
    injected = False

    for _node_id, node in wf.items():
        if not isinstance(node, dict):
            continue
        inputs = node.get("inputs", {})
        class_type = str(node.get("class_type", ""))

        # Seed guncelle
        for s_key in ("seed", "noise_seed"):
            if s_key in inputs and isinstance(inputs[s_key], int):
                inputs[s_key] = seed

        # Pozitif metin kutusunu bul ve promptu yaz (Bos olan negatif kutuya dokunma!)
        if "CLIPTextEncode" in class_type or "TextEncode" in class_type or "Prompt" in class_type:
            for t_key in ("text", "prompt", "string"):
                if t_key in inputs and isinstance(inputs[t_key], str) and len(inputs[t_key].strip()) > 3:
                    inputs[t_key] = prompt_text
                    injected = True
                    break

    if not injected:
        print("[UYARI] MOSS workflow icinde metin dugumu otomatik bulunamadi; varsayilan metinle calisacak.")
    return wf


def inject_image_into_trellis_workflow(workflow: dict, image_path: str) -> dict:
    wf = json.loads(json.dumps(workflow))
    seed = random.randint(1, 2**31 - 1)

    for _node_id, node in wf.items():
        if not isinstance(node, dict):
            continue
        inputs = node.get("inputs", {})
        class_type = str(node.get("class_type", ""))

        for s_key in ("seed", "noise_seed"):
            if s_key in inputs and isinstance(inputs[s_key], int):
                inputs[s_key] = seed

        if "LoadImage" in class_type and "image" in inputs:
            inputs["image"] = image_path

    return wf


def upload_image_to_comfy(comfy_url: str, filepath: str) -> str:
    """Uretilen 2D gorseli TRELLIS.2 LoadImage dugumunun okuyabilmesi icin ComfyUI input klasorune yukler."""
    boundary = f"----KararsizlikBoundary{random.randint(100000, 999999)}"
    filename = os.path.basename(filepath)
    with open(filepath, "rb") as f:
        file_bytes = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        f"{comfy_url}/upload/image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res.get("name", filename)


def queue_and_wait_comfy(comfy_url: str, workflow: dict, step_title: str) -> dict:
    payload = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(
        f"{comfy_url}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        prompt_id = json.loads(resp.read().decode("utf-8"))["prompt_id"]

    print(f"⏳ [{step_title}] ComfyUI kuyruga alindi (ID: {prompt_id[:8]}...), bitmesi bekleniyor...")
    start = time.time()
    while True:
        time.sleep(2.5)
        try:
            with urllib.request.urlopen(f"{comfy_url}/history/{prompt_id}", timeout=10) as h_resp:
                hist = json.loads(h_resp.read().decode("utf-8"))
                if prompt_id in hist:
                    elapsed = int(time.time() - start)
                    print(f"✅ [{step_title}] Tamamlandi! ({elapsed} saniye)")
                    return hist[prompt_id]
        except Exception:
            pass


def free_comfy_vram(comfy_url: str):
    """MOSS-Image bittikten sonra TRELLIS.2 gecisinde 16 GB VRAM tertemiz olsun diye bellegi bosaltir!"""
    try:
        data = json.dumps({"unload_models": True, "free_memory": True}).encode("utf-8")
        req = urllib.request.Request(
            f"{comfy_url}/free",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=10).read()
        print("🧹 [VRAM Korumasi] MOSS-Image bellekten bosaltildi, 16 GB VRAM TRELLIS.2 icin hazir!")
    except Exception:
        pass


def find_newest_file(directory: str, extensions: tuple, since_time: float):
    candidates = []
    for ext in extensions:
        candidates.extend(glob.glob(os.path.join(directory, f"*{ext}")))
        candidates.extend(glob.glob(os.path.join(directory, "**", f"*{ext}"), recursive=True))
    recent = [p for p in candidates if os.path.getmtime(p) >= since_time - 2.0]
    if recent:
        return max(recent, key=os.path.getmtime)
    return max(candidates, key=os.path.getmtime) if candidates else None


def main():
    print("=" * 72)
    print("🔥 KARARSIZLIK OTO-FABRİKA (2D -> Bekle -> 3D -> Blender PBR -> Onaylı UE5) 🔥")
    print("=" * 72)

    comfy_url = detect_comfy_url()
    if not comfy_url:
        print("❌ ComfyUI acik degil! Lutfen once ComfyUI Desktop'u acip tekrar calistir.")
        sys.exit(1)
    print(f"🟢 ComfyUI baglantisi bulundu: {comfy_url}")

    if not os.path.isfile(MOSS_API_JSON) or not os.path.isfile(TRELLIS_API_JSON):
        os.makedirs(os.path.dirname(MOSS_API_JSON), exist_ok=True)
        print("\n📌 İLK KURULUM ADIMI (Sadece 1 Kere Yapilacak):")
        print("   ComfyUI'de Settings -> 'Enable Dev mode Options' ac ve iki is akisini kaydet:")
        print(f"   1) MOSS-Image Workflow -> Export (API) -> {MOSS_API_JSON}")
        print(f"   2) TRELLIS.2 Workflow  -> Export (API) -> {TRELLIS_API_JSON}")
        sys.exit(0)

    user_idea = " ".join(sys.argv[1:]).strip()
    if not user_idea:
        user_idea = input("\n⚔️ Ne uretelim kanka? (Orn: 'Kirik imparator kilici, kararmis celik ve mor kristal'): ").strip()
    if not user_idea:
        print("Fikir girilmedi, cikiliyor.")
        sys.exit(0)

    # 1. Prompt hazirla
    en_prompt = build_english_prompt(user_idea)
    print(f"\n📝 Kullanilan 2D->3D Promptu:\n   {en_prompt}\n")

    # 2. MOSS-Image 2D Görsel Üret ve Bekle
    with open(MOSS_API_JSON, "r", encoding="utf-8") as f:
        moss_wf = json.load(f)
    moss_wf = inject_prompt_into_moss_workflow(moss_wf, en_prompt)

    t0 = time.time()
    queue_and_wait_comfy(comfy_url, moss_wf, "ADIM 1/3: MOSS-Image 2D Konsept Uretimi")
    newest_img = find_newest_file(COMFY_BASE_OUTPUT, (".png", ".jpg", ".webp"), t0)
    if not newest_img:
        print("❌ Uretilen 2D gorsel output klasorunde bulunamadi!")
        sys.exit(1)
    print(f"🖼️ 2D Gorsel hazir: {newest_img}")

    # VRAM Temizle (RTX 5080 16 GB korumasi!)
    free_comfy_vram(comfy_url)
    time.sleep(2.0)

    # 3. TRELLIS.2 3D Model Üret ve Bekle
    uploaded_name = upload_image_to_comfy(comfy_url, newest_img)
    with open(TRELLIS_API_JSON, "r", encoding="utf-8") as f:
        trellis_wf = json.load(f)
    trellis_wf = inject_image_into_trellis_workflow(trellis_wf, uploaded_name)

    t1 = time.time()
    queue_and_wait_comfy(comfy_url, trellis_wf, "ADIM 2/3: TRELLIS.2 3D .GLB Model Uretimi")
    newest_glb = find_newest_file(COMFY_3D_OUTPUT, (".glb",), t1)
    if not newest_glb:
        print("❌ Uretilen .glb dosyasi output\\3d klasorunde bulunamadi!")
        sys.exit(1)

    print(f"\n🎉 ADIM 3/3: 3D Model Hazir! -> {newest_glb}")
    print("👉 Blender'da '🟢 Canli Oto-Yakalayici' aciksa model SU AN OTOMATIK SAHNEDE PBR + ISIKLA ACILDI!")
    print("   (Degilse Blender KARARSIZLIK panelinde '1. Son ComfyUI Modelini Getir' tusuna bas!)")

    # Kullanici Onayi
    ans = input("\n✅ Blender'da inceledin mi? Unreal Engine 5.8'e GONDERMEK icin [E] yazip Enter'a bas (Iptal icin Enter): ").strip().lower()
    if ans in ("e", "evet", "y", "yes"):
        print("💡 Not: Yumusatilmis/temizlenmis versiyon icin Blender'daki '2. ONAYLA -> Unreal Engine 5.8'e Gonder!' butonuna basman en yuksek kaliteyi verir.")
        os.makedirs(UNREAL_AUTOIMPORT_DIR, exist_ok=True)
        dest = os.path.join(UNREAL_AUTOIMPORT_DIR, f"SM_{os.path.basename(newest_glb)}")
        shutil.copy2(newest_glb, dest)
        print(f"🚀 Unreal Engine AutoImport klasorune kopyalandi: {dest}")
    else:
        print("⏸️ Unreal aktarimi beklendi — istedigin an Blender icindeki 2. Butonla onaylayip gonderebilirsin!")


if __name__ == "__main__":
    main()
