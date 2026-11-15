#!/usr/bin/env python3
"""
KARARSIZLIK — LM Studio (Bionic 27B / Qwen 9B) Doğrudan MCP Skill Sunucusu!
Standart Kutuphane (Sifir pip kurulumu — JSON-RPC 2.0 stdio MCP protokolu!)

Bu dosya LM Studio -> Program (Integrations / MCP) -> `mcp.json` icine eklendiginde,
Bionic / 9B modeline su 2 GERÇEK YETENEĞİ (Tool/Skill) kazandirir:

1. `uret_2d_3d_ve_blendera_at(prompt_en, esya_adi)`:
   - Bionic senin Turkce istegini alir, kendi zekasiyla Ingilizce MOSS-Image promptunu yazar ve bu araci cagirir!
   - Arac gerekirse LM Studio VRAM'ini rahatlatir, ComfyUI'de MOSS-Image 2D gorseli uretip BITMESINI BEKLER,
   - VRAM'i temizler, TRELLIS.2 ile .glb 3D modeli uretip BITMESINI BEKLER,
   - Blender Canli Yakalayiciya sinyal birakir (model aninda Blender'da PBR + isikla acilir) ve Bionic'e rapor verir!

2. `onayla_ve_unreala_gonder(esya_adi)`:
   - Sen LM Studio sohbetinde "begendim kanka, onayla Unreal'a at" dediginde Bionic bu araci cagirir
     ve modeli C:\\KARARSIZLIK_UnrealBridge\\AutoImport klasorune gonderir!
"""

import json
import os
import shutil
import sys
import time
import urllib.request

# Ayni klasordeki kararsizlik_oto_fabrika fonksiyonlarini kullan
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import kararsizlik_oto_fabrika as fabrika


TOOLS_MANIFEST = [
    {
        "name": "uret_2d_3d_ve_blendera_at",
        "description": (
            "Kullanici bir oyun esyasi, kilic, kalkan, yay, maske veya heykel uretmek istediginde bu araci cagir! "
            "Once ComfyUI MOSS-Image ile 2D gorsel uretir ve bitmesini bekler, sonra VRAM temizleyip TRELLIS.2 ile "
            "3D .glb modele cevirir ve bitmesini bekler, ardindan Blender PBR sahnesine gonderir. "
            "KESIN KURAL: Ateşli silah yasaktir; karanlik ortacag fantastik PBR tarzinda Ingilizce prompt ver."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt_en": {
                    "type": "string",
                    "description": (
                        "Detailed English photorealistic dark medieval prompt for MOSS-Image: single isolated object "
                        "centered on clean neutral grey background, weathered forged iron, tarnished bronze, smoky amethyst."
                    ),
                },
                "esya_adi": {
                    "type": "string",
                    "description": "Temiz dosya ismi (orn: Kirik_Imparator_Kilici)",
                },
            },
            "required": ["prompt_en", "esya_adi"],
        },
    },
    {
        "name": "onayla_ve_unreala_gonder",
        "description": (
            "SADECE kullanici Blender'daki 3D modeli gordukten sonra acikca 'onayliyorum / begendim / Unreal Engine'e at' "
            "dediginde cagir! En son uretilen 3D .glb modelini Unreal Engine 5.8 AutoImport klasorune aktarir."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "esya_adi": {
                    "type": "string",
                    "description": "Unreal Engine'de gorunecek temiz model adi (orn: SM_Kirik_Imparator_Kilici)",
                }
            },
            "required": ["esya_adi"],
        },
    },
]


def run_pipeline_tool(prompt_en: str, esya_adi: str) -> str:
    comfy_url = fabrika.detect_comfy_url()
    if not comfy_url:
        return "HATA: ComfyUI su an acik degil! Kullaniciya ComfyUI Desktop'u acmasini soyle."

    if not os.path.isfile(fabrika.MOSS_API_JSON) or not os.path.isfile(fabrika.TRELLIS_API_JSON):
        return (
            f"HATA: API sablon dosyalari eksik! ({fabrika.MOSS_API_JSON} ve {fabrika.TRELLIS_API_JSON} bulunamadi)."
        )

    full_prompt = prompt_en.strip()
    if "neutral grey background" not in full_prompt.lower():
        full_prompt += fabrika.DARK_PBR_STYLE_SUFFIX

    with open(fabrika.MOSS_API_JSON, "r", encoding="utf-8") as f:
        moss_wf = json.load(f)
    moss_wf = fabrika.inject_prompt_into_moss_workflow(moss_wf, full_prompt)

    t0 = time.time()
    fabrika.queue_and_wait_comfy(comfy_url, moss_wf, "MOSS-Image 2D")
    newest_img = fabrika.find_newest_file(fabrika.COMFY_BASE_OUTPUT, (".png", ".jpg", ".webp"), t0)
    if not newest_img:
        return "HATA: 2D gorsel uretildi ancak output klasorunde bulunamadi."

    fabrika.free_comfy_vram(comfy_url)
    time.sleep(1.5)

    uploaded_name = fabrika.upload_image_to_comfy(comfy_url, newest_img)
    with open(fabrika.TRELLIS_API_JSON, "r", encoding="utf-8") as f:
        trellis_wf = json.load(f)
    trellis_wf = fabrika.inject_image_into_trellis_workflow(trellis_wf, uploaded_name)

    t1 = time.time()
    fabrika.queue_and_wait_comfy(comfy_url, trellis_wf, "TRELLIS.2 3D")
    newest_glb = fabrika.find_newest_file(fabrika.COMFY_3D_OUTPUT, (".glb",), t1)
    if not newest_glb:
        return f"2D gorsel hazir ({newest_img}), ancak TRELLIS.2 .glb ciktisi bulunamadi."

    fabrika.free_comfy_vram(comfy_url)

    return (
        f"BASARILI! '{esya_adi}' icin:\n"
        f"1) 2D Konsept Gorsel uretildi: {newest_img}\n"
        f"2) 3D Model (.glb) uretildi: {newest_glb}\n"
        f"3) Blender Canli Oto-Yakalayici aciksa su an Blender ekraninda Karanlik Celik + Mor Kristal PBR olarak acildi "
        f"(acik degilse Blender KARARSIZLIK panelinde 1. Butona basmasi yeterli).\n"
        f"Simdi kullaniciya Blender'da modeli incelemesini ve begendiyse Unreal Engine 5.8'e gondermek icin onay vermesini sor!"
    )


def approve_unreal_tool(esya_adi: str) -> str:
    """Oncelikle Blender v2.0 Koprusunun olusturdugu temizlenmis (Weld+Smooth+Pivot+UCX) dosyayi arar!"""
    clean = "".join(c if c.isalnum() or c == "_" else "_" for c in esya_adi.strip()) or "Kararsizlik_Asset"
    if not clean.startswith("SM_"):
        clean = f"SM_{clean}"

    os.makedirs(fabrika.UNREAL_AUTOIMPORT_DIR, exist_ok=True)

    # 1. Oncelik: Blender v2.0 Koprusunun hazirladigi temizlenmis ApprovedStaging dosyalari (.fbx + .glb)
    staged_fbx = fabrika.find_newest_file(fabrika.APPROVED_STAGING_DIR, (".fbx",), 0.0)
    staged_glb = fabrika.find_newest_file(fabrika.APPROVED_STAGING_DIR, (".glb",), 0.0)
    if staged_fbx or staged_glb:
        copied = []
        if staged_fbx:
            dest_fbx = os.path.join(fabrika.UNREAL_AUTOIMPORT_DIR, f"{clean}.fbx")
            shutil.copy2(staged_fbx, dest_fbx)
            copied.append(dest_fbx)
        if staged_glb:
            dest_glb = os.path.join(fabrika.UNREAL_AUTOIMPORT_DIR, f"{clean}.glb")
            shutil.copy2(staged_glb, dest_glb)
            copied.append(dest_glb)
        return (
            f"ONAYLANDI VE AKTARILDI! Blender'da temizlenmis (Weld + Smooth + Pivot + UCX Collision) model "
            f"Unreal Engine 5.8 AutoImport klasorune gonderildi:\n" + "\n".join(copied)
        )

    # Eger kullanici henuz Blender'da 2. Butona basmadiysa ham kopyalama YAPMA, once Blender temizligini iste!
    return (
        "UYARI: Henuz Blender temizligi (Weld + Pivot + UCX Collision) uygulanmamis! "
        "Ham TRELLIS modeli dogrudan Unreal'a atilmadi. Lutfen Blender sag paneldeki (N -> KARARSIZLIK) "
        "'2. ONAYLA -> Unreal Engine 5.8'e Gonder!' butonuna basarak temizlenmis modeli gonder."
    )


def send_rpc(msg: dict):
    sys.__stdout__.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.__stdout__.flush()


def main():
    # print() cagrilarini stderr'e yonlendir ki MCP stdout JSON kanalini bozmasin!
    sys.stdout = sys.stderr

    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = req.get("method", "")
        req_id = req.get("id")

        if method == "initialize":
            send_rpc({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "kararsizlik-3d-factory", "version": "1.0.0"},
                },
            })
        elif method.startswith("notifications/"):
            continue
        elif method == "tools/list":
            send_rpc({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": TOOLS_MANIFEST},
            })
        elif method == "tools/call":
            params = req.get("params", {})
            t_name = params.get("name", "")
            args = params.get("arguments", {}) or {}
            try:
                if t_name == "uret_2d_3d_ve_blendera_at":
                    out_text = run_pipeline_tool(
                        args.get("prompt_en", "dark medieval sword"),
                        args.get("esya_adi", "Kararsizlik_Asset"),
                    )
                elif t_name == "onayla_ve_unreala_gonder":
                    out_text = approve_unreal_tool(args.get("esya_adi", "SM_Kararsizlik_Asset"))
                else:
                    out_text = f"Bilinmeyen arac: {t_name}"
                send_rpc({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": out_text}], "isError": False},
                })
            except Exception as exc:
                send_rpc({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": f"Arac calisma hatasi: {exc}"}], "isError": True},
                })
        elif req_id is not None:
            send_rpc({"jsonrpc": "2.0", "id": req_id, "result": {}})


if __name__ == "__main__":
    main()
