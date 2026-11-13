# Unreal Engine Entegrasyonu

Hedef: Unreal **hiçbir zaman** API anahtarı görmez, hiçbir zaman modele doğrudan
bağlanmaz. Sadece kendi backend'ine HTTP atar. Model değiştirmek oyunu
yeniden paketlemeyi gerektirmez.

```
┌──────────────┐   HTTP/JSON    ┌────────────────┐   HTTPS    ┌──────────────┐
│ Unreal Engine│ ─────────────► │ Ash AI Backend │ ─────────► │ OpenAI/Claude│
│  (Blueprint/ │ ◄───────────── │   (FastAPI)    │            │ Gemini/Ollama│
│      C++)    │   SSE akış     └────────────────┘            └──────────────┘
└──────────────┘
```

Kontrat üç uç nokta: `GET /health`, `GET /v1/npcs`, `POST /v1/dialogue`
(+ opsiyonel `POST /v1/dialogue/stream`).

---

## 0. Ön koşullar

- Unreal Engine 5.3+ (5.7 güncel sürüm; HTTP ve Json modülleri built-in)
- `AshAI` HTTP çağrıları için: **Project Settings → Plugins → HTTP** açık
- Backend erişilebilir olmalı: editörde `http://127.0.0.1:8000`,
  paketlenmiş oyunda kendi sunucu adresin

> **Uzun süreli prototip için:** UE editöründe Play tuşuna basmadan önce
> `cd backend && uvicorn app.main:app --port 8000` çalışıyor olmalı.
> `backend/.env` içinde `AI_PROVIDER=mock` ise ağ olmadan da tüm akış çalışır —
> entegrasyonu API anahtarı olmadan bitirebilirsin.

---

## 1. Seçenek A — Sadece Blueprint (VaRest ile ~15 dakika)

Blueprint'te JSON kurmak elle çok hantal. **VaRest** (Fab, ücretsiz) kullan:

1. **VaRest** pluginini kur, `VaRest` modülünü aç.
2. `Construct JSON Object` → `Set String Field`:
   - `npc_id` = `kapi_muhafizi_sabri`
   - `player_message` = oyuncunun yazdığı metin
   - `locale` = `tr`
   - `history` = `Construct JSON Array` (boş da olur)
   - `player_state` = `Construct JSON Object` → `level`, `hp`, `max_hp`, `gold`,
     `inventory` (array), `flags` (object)
   - `world_events` = `Construct JSON Array`
3. `Call URL` → `POST`, `http://127.0.0.1:8000/v1/dialogue`,
   `Content-Type: application/json`
4. `Bind Event to On Request Complete` →
   - `Get Response Object` → `Get String Field "text"` → diyalog widget'ına yaz
   - `Get String Field "emotion"` → animasyon/portre seçiminde kullan
   - `Get Array Field "tool_calls"` → aşağıdaki döngü

**Araç çağrılarını uygulama (Blueprint):**

```
ForEach tool_calls
 └─ Switch on String (Get String Field "name")
     ├─ "give_item"      → Get Object Field "arguments" → item_id → AddItem
     ├─ "transfer_gold"  → amount → UpdateGold
     ├─ "set_quest_state"→ quest_id, state → QuestComponent
     ├─ "reveal_lore"    → lore_id → Codex'e ekle
     └─ "open_passage"   → requires_confirmation? → onay UI, sonra aç
```

**Kritik:** `requires_confirmation == true` olan çağrıları oyuncuya onaylat.
Model "kapıyı açtım" dese bile sen açmıyorsan açılmaz — doğru davranış budur.

---

## 2. Seçenek B — C++ (önerilen, temiz ve yeniden kullanılabilir)

İki parça: bir **GameInstanceSubsystem** (HTTP + parse) ve bir
**data struct** (Blueprint'e açık). Yeni bir `AshAI` modülü aç:

**`AshAI.Build.cs`**

```csharp
using UnrealBuildTool;

public class AshAI : ModuleRules
{
    public AshAI(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new[]
        {
            "Core", "CoreUObject", "Engine", "HTTP", "Json", "JsonUtilities"
        });
    }
}
```

**`AshAITypes.h`** — backend sözleşmesinin UE karşılığı

```cpp
#pragma once
#include "CoreMinimal.h"
#include "AshAITypes.generated.h"

USTRUCT(BlueprintType)
struct FAshAIToolCall
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly) FString Name;
    UPROPERTY(BlueprintReadOnly) TMap<FString, FString> Arguments; // düzleştirilmiş
    UPROPERTY(BlueprintReadOnly) bool bRequiresConfirmation = false;
};

USTRUCT(BlueprintType)
struct FAshAIDialogueResult
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly) bool bSuccess = false;
    UPROPERTY(BlueprintReadOnly) FString Text;
    UPROPERTY(BlueprintReadOnly) FString Emotion = TEXT("neutral");
    UPROPERTY(BlueprintReadOnly) TArray<FAshAIToolCall> ToolCalls;
    UPROPERTY(BlueprintReadOnly) bool bFallbackUsed = false; // ağ/model sorunu
    UPROPERTY(BlueprintReadOnly) int32 LatencyMs = 0;
    UPROPERTY(BlueprintReadOnly) FString ErrorMessage;
};

USTRUCT(BlueprintType)
struct FAshAIPlayerState
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadWrite) int32 Level = 1;
    UPROPERTY(BlueprintReadWrite) int32 HP = 100;
    UPROPERTY(BlueprintReadWrite) int32 MaxHP = 100;
    UPROPERTY(BlueprintReadWrite) int32 Gold = 0;
    UPROPERTY(BlueprintReadWrite) TArray<FString> Inventory;
    UPROPERTY(BlueprintReadWrite) TMap<FString, bool> Flags;
};
```

**`AshAISubsystem.h`**

```cpp
#pragma once
#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Interfaces/IHttpRequest.h"
#include "AshAITypes.h"
#include "AshAISubsystem.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(
    FOnAshDialogueComplete, FAshAIDialogueResult, Result);

UCLASS()
class UAshAISubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()

public:
    UPROPERTY(BlueprintAssignable, Category = "Ash AI")
    FOnAshDialogueComplete OnDialogueComplete;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ash AI")
    FString BaseUrl = TEXT("http://127.0.0.1:8000");

    /** Blueprint'ten çağır: tek tur diyalog. */
    UFUNCTION(BlueprintCallable, Category = "Ash AI")
    void RequestDialogue(const FString& NpcId,
                         const FString& PlayerMessage,
                         const FAshAIPlayerState& PlayerState,
                         const TArray<FString>& HistoryLines);

private:
    void HandleResponse(FHttpRequestPtr Request, FHttpResponsePtr Response, bool bConnected);
};
```

**`AshAISubsystem.cpp`**

```cpp
#include "AshAISubsystem.h"
#include "HttpModule.h"
#include "Interfaces/IHttpResponse.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"

void UAshAISubsystem::RequestDialogue(const FString& NpcId,
                                      const FString& PlayerMessage,
                                      const FAshAIPlayerState& PlayerState,
                                      const TArray<FString>& HistoryLines)
{
    // --- payload ---
    TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
    Root->SetStringField(TEXT("npc_id"), NpcId);
    Root->SetStringField(TEXT("player_message"), PlayerMessage);
    Root->SetStringField(TEXT("locale"), TEXT("tr"));

    TArray<TSharedPtr<FJsonValue>> History;
    for (const FString& Line : HistoryLines)
    {
        TSharedPtr<FJsonObject> Turn = MakeShared<FJsonObject>();
        Turn->SetStringField(TEXT("role"), TEXT("player"));
        Turn->SetStringField(TEXT("content"), Line);
        History.Add(MakeShared<FJsonValueObject>(Turn));
    }
    Root->SetArrayField(TEXT("history"), History);

    TSharedPtr<FJsonObject> State = MakeShared<FJsonObject>();
    State->SetNumberField(TEXT("level"), PlayerState.Level);
    State->SetNumberField(TEXT("hp"), PlayerState.HP);
    State->SetNumberField(TEXT("max_hp"), PlayerState.MaxHP);
    State->SetNumberField(TEXT("gold"), PlayerState.Gold);

    TArray<TSharedPtr<FJsonValue>> Inv;
    for (const FString& Item : PlayerState.Inventory)
    {
        Inv.Add(MakeShared<FJsonValueString>(Item));
    }
    State->SetArrayField(TEXT("inventory"), Inv);

    TSharedPtr<FJsonObject> Flags = MakeShared<FJsonObject>();
    for (const TPair<FString, bool>& Pair : PlayerState.Flags)
    {
        Flags->SetBoolField(Pair.Key, Pair.Value);
    }
    State->SetObjectField(TEXT("flags"), Flags);
    Root->SetObjectField(TEXT("player_state"), State);
    Root->SetArrayField(TEXT("world_events"), {});

    FString Payload;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Payload);
    FJsonSerializer::Serialize(Root.ToSharedRef(), Writer);

    // --- istek ---
    TSharedRef<IHttpRequest, ESPMode::ThreadSafe> Request =
        FHttpModule::Get().CreateRequest();
    Request->SetURL(BaseUrl + TEXT("/v1/dialogue"));
    Request->SetVerb(TEXT("POST"));
    Request->SetHeader(TEXT("Content-Type"), TEXT("application/json"));
    Request->SetContentAsString(Payload);
    Request->SetTimeout(30.0f);
    Request->OnProcessRequestComplete().BindUObject(
        this, &UAshAISubsystem::HandleResponse);
    Request->ProcessRequest();
}

void UAshAISubsystem::HandleResponse(FHttpRequestPtr Request,
                                     FHttpResponsePtr Response,
                                     bool bConnected)
{
    FAshAIDialogueResult Result;

    if (!bConnected || !Response.IsValid())
    {
        Result.bSuccess = false;
        Result.bFallbackUsed = true;
        Result.ErrorMessage = TEXT("backend_unreachable");
        OnDialogueComplete.Broadcast(Result);
        return;
    }

    if (Response->GetResponseCode() != 200)
    {
        Result.bSuccess = false;
        Result.ErrorMessage = FString::Printf(TEXT("http_%d"), Response->GetResponseCode());
        OnDialogueComplete.Broadcast(Result);
        return;
    }

    TSharedPtr<FJsonObject> Json;
    TSharedRef<TJsonReader<>> Reader =
        TJsonReaderFactory<>::Create(Response->GetContentAsString());
    if (!FJsonSerializer::Deserialize(Reader, Json) || !Json.IsValid())
    {
        Result.ErrorMessage = TEXT("bad_json");
        OnDialogueComplete.Broadcast(Result);
        return;
    }

    Result.bSuccess = true;
    Json->TryGetStringField(TEXT("text"), Result.Text);
    Json->TryGetStringField(TEXT("emotion"), Result.Emotion);

    const TArray<TSharedPtr<FJsonValue>>* Calls = nullptr;
    if (Json->TryGetArrayField(TEXT("tool_calls"), Calls) && Calls)
    {
        for (const TSharedPtr<FJsonValue>& Value : *Calls)
        {
            const TSharedPtr<FJsonObject> Obj = Value->AsObject();
            if (!Obj.IsValid()) { continue; }

            FAshAIToolCall Call;
            Obj->TryGetStringField(TEXT("name"), Call.Name);
            Obj->TryGetBoolField(TEXT("requires_confirmation"),
                                 Call.bRequiresConfirmation);

            const TSharedPtr<FJsonObject>* Args = nullptr;
            if (Obj->TryGetObjectField(TEXT("arguments"), Args) && Args)
            {
                for (const auto& Pair : (*Args)->Values)
                {
                    Call.Arguments.Add(Pair.Key, Pair.Value->AsString());
                }
            }
            Result.ToolCalls.Add(Call);
        }
    }

    const TSharedPtr<FJsonObject>* Usage = nullptr;
    if (Json->TryGetObjectField(TEXT("usage"), Usage) && Usage)
    {
        (*Usage)->TryGetBoolField(TEXT("fallback_used"), Result.bFallbackUsed);
        (*Usage)->TryGetNumberField(TEXT("latency_ms"), Result.LatencyMs);
    }

    OnDialogueComplete.Broadcast(Result);
}
```

**Blueprint kullanımı:** `Get AshAISubsystem` → `Bind Event to OnDialogueComplete`
→ `RequestDialogue`. Gelen `ToolCalls` dizisini `Switch on Name` ile uygula.

> `HandleResponse` oyun thread'inde çağrılır, ama içinde `//` yorumlarını
> sadeleştirmeyi unutma; UE'de dosya başına `#include` sırası bazen derleyici
> sürümüne göre değişir.

---

## 3. Akış (streaming) — altyazı harf harf aksın

`POST /v1/dialogue/stream` `text/event-stream` döner:

```
data: {"type":"chunk","text":"Geçit kapalı."}
data: {"type":"chunk","text":" Ama sen zaten biliyorsun."}
data: {"type":"done","emotion":"sly","tool_calls":[],"usage":{...}}
```

UE tarafında bunu **tam HTTP streaming** olarak okumak gerekir
(`IHttpRequest` gövde parçaları için `OnRequestProgress` + kümülatif buffer).
Pratik kestirme: `mock`/prototip aşamasında normal `/v1/dialogue` kullan,
cümleyi 40 ms aralıkla kendin harf harf yaz — görsel sonuç aynı, kod çok daha basit.
Gerçek token akışı gerektiğinde `OnRequestProgress` ile buffer'ı `\n\n` üzerinden böl.

**SSE + TTS:** akış geldikçe cümleyi seslendirme kuyruğuna at
(`MetaSound` veya platform TTS). Cümle sonu noktalama geldiğinde kuyruğa ekle —
bu yüzden backend cümle sınırlarında parça gönderiyor.

---

## 4. Karakter verisini nerede tutacaksın

| Veri | Yer | Neden |
|---|---|---|
| Karakter kartı (kişilik, sır, tabu) | `backend/app/lore/npcs.json` | Tek doğruluk kaynağı; kod değişmeden güncellenir |
| Dünya kuralları / ton | `backend/app/lore/world.md` | Prompt'a enjekte edilir |
| İzinli eylemler | `backend/app/lore/tools.json` | Whitelist; model başka şey çağıramaz |
| Oyuncu durumu | UE (save game) | Oyunun gerçeği; backend'e sadece okumak için gider |
| Gradient/portre/animasyon | UE Data Asset | Görsel iş backend'in işi değil |

Blueprint'te `UPrimaryDataAsset` ile NPC tanımını tutup `id` alanıyla backend'e
göndermek en temizi: UI metinleri UE'de lokalize edilir, kişilik backend'de kalır.

---

## 5. Yapılacaklar kontrol listesi

- [ ] `backend` çalışıyor, `/health` 200 dönüyor
- [ ] `AI_PROVIDER=mock` ile uçtan uca diyalog alındı (anahtarsız)
- [ ] Gerçek sağlayıcı bağlandı, `health` → `status: ok`
- [ ] `tool_calls` uygulanıyor ve **whitelist dışı hiçbir şey** çalışmıyor
- [ ] Ağ kapatıldığında oyun kilitlenmiyor (`fallback_used` → sabit replik)
- [ ] Timeout 30 s altında; UI'da "düşünüyor" göstergesi var
- [ ] Save/load sonrası `player_state` doğru gidiyor
- [ ] Rate limit açık (`MAX_REQUESTS_PER_MINUTE`)
- [ ] Anahtar `.env`'de, paketlenmiş oyunda **yok**
