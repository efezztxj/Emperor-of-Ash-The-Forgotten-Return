# Kararsızlık — Oyun Deposu

Karanlık fantastik RPG: hafızasını kaybetmiş ölümsüz bir hükümdar. Bu depo oyunun **AI katmanını** barındırır:
Unreal Engine'in HTTP ile konuştuğu, modele bağımlı olmayan bir NPC diyalog
backend'i. Oyun kodu Unreal'da, model erişimi burada.

```
Unreal Engine  ──HTTP/JSON──►  Kararsızlık AI  ──►  OpenAI / Claude / Gemini
 (Blueprint/C++) ◄──SSE──────   (FastAPI)        └─►  Ollama / LM Studio (yerel)
```

## Depoda ne var

| Yol | İçerik |
|---|---|
| `docs/lore/WORLD_BIBLE.md` | **Oyunun hikâye taslağı** — dünya, ana karakter, din, Kararsızlık Evreni, boss seçimleri, üç son |
| `docs/lore/Kararsizlik_Oyun_Evreni_ve_Hikaye_Taslagi.pdf` | Taslağın orijinal PDF'i (arşiv) |
| `docs/AI_MIMARISI.md` | Teknik kararlar: neden backend, maliyet, güvenlik, RAG eşiği |
| `docs/UNREAL_ENTEGRASYON.md` | Blueprint (VaRest) + kopyala-yapıştır C++ `AshAISubsystem` |
| `backend/` | Çalışan AI servisi (FastAPI) |
| `tools/unreal/echo_ai_client.py` | UE sınıfının Python ikizi, canlı test için |

## Neden backend var
## Hızlı başlangıç (API anahtarı gerekmez)

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r backend/requirements.txt

cd backend
cp .env.example .env          # AI_PROVIDER=mock ile başlar
uvicorn app.main:app --reload --port 8000
```

Başka bir terminalde:

```bash
python tools/unreal/echo_ai_client.py     # interaktif NPC sohbeti
```

`mock` sağlayıcı gerçek modelin sözleşmesini taklit eder: JSON çıktı, tool_call,
streaming, fallback — hepsi ağ olmadan test edilebilir.

## Gerçek modele geçmek

`backend/.env` içinde üç satır:

```bash
# Bulut
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1-mini

# veya tamamen yerel (Ollama açıkken)
AI_PROVIDER=local
LOCAL_MODEL=qwen3:8b

# veya Gemini
AI_PROVIDER=gemini
GEMINI_API_KEY=...
```

`GET /health` → `{"status":"ok"}` gördüğünde bağlısın.

## API

| Uç nokta | Açıklama |
|---|---|
| `GET /health` | Sağlayıcı/model durumu, offline mı |
| `GET /v1/npcs` | Karakter kartı listesi (UE tek kaynaktan okur) |
| `GET /v1/npcs/{id}` | Tek karakter |
| `GET /v1/tools` | Modele izin verilen eylemler (whitelist, 12 araç) |
| `POST /v1/dialogue` | Tek tur diyalog → `text`, `emotion`, `tool_calls` |
| `POST /v1/dialogue/stream` | Aynı istek, `text/event-stream` |

```bash
curl -X POST localhost:8000/v1/dialogue -H 'Content-Type: application/json' -d '{
  "npc_id": "kapi_muhafizi_sabri",
  "player_message": "Geçit nereye çıkıyor?",
  "player_state": {"level":3,"hp":62,"max_hp":100,"gold":25,
                   "inventory":["rusty_key"],"flags":{}},
  "world_events": [{"kind":"player_entered_hall","detail":"kuzey girişi"}]
}'
```

Yanıt:

```json
{
  "npc_id": "kapi_muhafizi_sabri",
  "text": "Aşağıya. Ama aşağıda seni bekleyen şey... senin hatırladığın şey değil.",
  "emotion": "afraid",
  "tool_calls": [
    {"name": "reveal_lore", "arguments": {"lore_id": "under_hall"}, "requires_confirmation": false}
  ],
  "usage": {"model": "gpt-4.1-mini", "provider": "openai", "latency_ms": 940, "fallback_used": false}
}
```

## Depo yapısı

```
backend/
  app/main.py                 # uç noktalar, SSE, orkestrasyon
  app/config.py               # tek yerden ayar (.env)
  app/schemas.py              # UE ile sözleşme
  app/providers/              # openai-uyumlu, gemini, mock, fallback
  app/lore/npcs.json          # karakter kartları  ← burayı düzenle
  app/lore/tools.json         # izinli eylemler   ← whitelist
  app/lore/world.md           # dünya kuralları ve ton (WORLD_BIBLE.md'nin prompt hâli)
  app/game/validation.py      # modelin önerisini doğrular
  tests/                      # 19 test, ağsız
tools/unreal/echo_ai_client.py  # UE sınıfının Python ikizi
docs/UNREAL_ENTEGRASYON.md      # Blueprint + C++ kodu, adım adım
```

## Test

```bash
cd backend && pytest -q
```

## Tasarım kararları

- **Yapılandırılmış çıktı:** model `{"say","emotion","tool_calls"}` döner.
  Function calling desteklemeyen modeller için de aynı sözleşme geçerli;
  `parse_model_output` hem JSON'u hem gömülü JSON'u hem düz metni kabul eder.
- **Doğrulama oyunda, modele güven yok:** `game/validation.py` whitelist,
  tip, envanter ve altın bakiyesi kontrolü yapar. Reddedilen çağrılar
  düşer, oyuna hiç ulaşmaz.
- **Fallback her zaman açık:** sağlayıcı hatasında oyun durmaz.
- **Türkçe önce:** karakter kartları, prompt'lar ve ton Türkçe yazıldı.

## Hikâyeden sisteme: eşleme

Taslaktaki mekanikler AI katmanına nasıl bağlanıyor:

| Taslak | Teknik karşılık |
|---|---|
| Dinin "herkes mutlu görünecek" baskısı | NPC karakter kartlarında `voice` + `taboos`; diyalog tonu zorlanır |
| Sınıf seçimi yok, yollar sonradan açılır | `grant_discipline` / `abandon_discipline` araçları |
| Bosslarda öldür / affet / serbest bırak / eğitim al | `set_quest_state` + `shift_allegiance`, dört ayrı sonuç |
| Hafıza parça parça açılır | `recover_memory` aracı + `reveal_lore`; kimlik asla doğrudan söylenmez |
| Gri yaratıkların itaati | `gri_yaratik_emdri` aracı (eşya taşı / güvenli noktaya götür) |
| Aydınlık–karanlık–kararsız dengesi | `shift_allegiance` (-10..+10) → üç son |
| Kararsızlık Evreni bossları | Karakter kartı + `spawn_encounter`, onay gerektiren araç |

## Sırada ne var

- [ ] RAG: `WORLD_BIBLE.md` + görev metinleri Supabase/pgvector'a, ilgili parçaları context'e
- [ ] Konuşma hafızası: NPC başına son N turu kalıcı sakla (şu an UE gönderiyor)
- [ ] TTS: ElevenLabs (bulut) veya Piper (yerel), `emotion` alanıyla ses tonu
- [ ] STT: mikrofon → metin, aynı `/v1/dialogue`
- [ ] Maliyet paneli: sağlayıcı/token bazlı günlük özet
