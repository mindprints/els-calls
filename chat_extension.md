# PRD — Stepwise AI Voice Replies on 46elks (Option A)

## 1) Objective

Add a “listen → think → speak” loop on top of the current system that plays a pre-recorded MP3 to **MIL_NUMBER** callers and forwards others. The loop records a short utterance, runs STT→LLM→TTS on our VPS, then returns a **play** action to 46elks. Uses only 46elks call actions (`play`, `record`, `next`) and our existing Bottle app. No SIP or live streaming.

## 2) Success criteria

* Calls from **MIL_NUMBER**: greeting MP3 → ≤12s recording with silence-stop → ≤3s model reply playback.
* 1–2 reply turns per call (configurable), then a calm closing.
* Non-MIL calls continue to **connect** to **FALLBACK_NUMBER**.
* Error paths always play a default reassurance MP3 (never dead-end/busy).

## 3) Scope

### In

* 46elks call-action chain: `play → record → play (reply) → [repeat ≤ MAX_TURNS]`.
* New endpoint `POST /recordings` (46elks callback with `wav` URL).
* Server pipeline: fetch WAV → STT → LLM → TTS (ElevenLabs) → write `reply-<callid>-<n>.mp3`.
* Dashboard fields: `MAX_TURNS`, language, enable/disable “AI replies”.

### Out (non-goals)

* Full-duplex “barge-in” conversation.
* SIP bridging to realtime agents.
* Long-term memory or personalization beyond the prompt/KB.

## 4) Users & scenarios

* **Primary**: Mother-in-law calls the 46elks number when anxious; hears greeting, says a few words, hears a brief, warm reply; 1–2 exchanges; gentle goodbye.
* **Secondary**: Other callers reach the normal mobile via **connect**.

## 5) Call flow (per MIL call)

1. **/calls** (mode unset): return

```json
{ "play": "https://calls.mtup.xyz/audio/hello.mp3",
  "skippable": false,
  "next": "https://calls.mtup.xyz/calls?mode=record1" }
```

46elks plays the file; after playback it POSTs `next`.

2. **/calls?mode=record1**: return

```json
{ "record": "https://calls.mtup.xyz/recordings",
  "silencedetection": "yes",
  "timelimit": 12,
  "next": "https://calls.mtup.xyz/calls?mode=reply1" }
```

Silence auto-stops (~3s); then 46elks POSTs `next`.

3. **/recordings**: 46elks sends `wav=<url>`. Server fetches WAV, runs STT→LLM→TTS (ElevenLabs TTS: `POST /v1/text-to-speech/:voice_id`), writes `/app/audio/reply-<callid>-1.mp3`, returns 200.

4. **/calls?mode=reply1**: return

```json
{ "play": "https://calls.mtup.xyz/audio/reply-<callid>-1.mp3",
  "next": "https://calls.mtup.xyz/calls?mode=record2" }
```

If `turn == MAX_TURNS`, omit `next` to end after playback.

5. Repeat `record2 → reply2` up to `MAX_TURNS`. Then optional closing MP3.

Non-MIL path remains:

```json
{ "connect": "+46..." }
```

(with 46elks restrictions noted).

## 6) Functional requirements

* **Endpoints**

  * `POST /calls`

    * Input: `from`, `to`, `callid` (46elks), `mode` (query).
    * Branch: MIL vs non-MIL; mode router (`recordN`, `replyN`).
    * Output: JSON call actions; HTTP 200–204 only.
  * `POST /recordings`

    * Input: `wav` (URL), `callid`, `from`,`to`, etc.
    * Action: fetch WAV; produce `reply-<callid>-N.mp3`; return 200.
  * Existing: `/audio/<filename>` serves MP3; `/settings` CRUD.

* **Config (settings.json additions)**

  * `MAX_TURNS` (int, default 2)
  * `LANG` (default `sv`)
  * `AI_REPLIES_ENABLED` (bool)

* **AI pipeline**

  * **STT**: vendor-pluggable; placeholder allowed initially.
  * **LLM**: 1–2 sentences, Swedish, dementia-safe phrasing.
  * **TTS**: ElevenLabs TTS REST (`/v1/text-to-speech/:voice_id`, `accept: audio/mpeg`).

* **File naming**

  * Replies: `reply-<callid>-<turn>.mp3` under `/app/audio`.

## 7) Non-functional requirements

* **Latency targets**

  * Greeting to start-recording: immediate (file already hosted).
  * Turn time (end of talk → reply playback begins): target ≤3.0 s (@ 12 s timelimit; ≤1.5 s if utterance short).
* **Reliability**

  * If synthesis not ready within 8 s, play default reassurance MP3.
  * All endpoints must return 200–204; on exceptions, return fallback `play`.
* **Capacity**

  * Single-caller concurrency adequate; future: limit active transcodes.
* **Security**

  * Validate `wav` URL host as 46elks (or fetch with timeouts).
  * Do not store raw WAV beyond processing.
* **Privacy**

  * Data minimization (no unnecessary PII).
  * Document purpose; Swedish context/GDPR—retain only derived MP3 for short time if needed.

## 8) Dashboard changes

* Toggle “AI replies (Option A)”: on/off.
* Inputs: `MAX_TURNS`, language, ElevenLabs `VOICE_ID` (env), test button to synthesize a sample line.
* Status panel per callid (last generated `reply-*.mp3` links).

## 9) Error handling

* **46elks cannot fetch MP3** → return `play` with baked-in fallback (hello/closing); check TLS/URL; 46elks logs show `hangup: badsource` if URL fails.
* **STT/LLM/TTS error** → write a stock reply MP3 (pre-rendered) and continue.
* **Timeouts** (WAV fetch or TTS) → serve fallback; log error.

## 10) Observability

* Structured logs per turn: `{callid, mode, from, wav_fetched_ms, stt_ms, llm_ms, tts_ms, mp3_size, outcome}`.
* Access log for `/audio/*`.
* Simple `/debug-audio` index (non-indexed URL) in staging only.

## 11) Rollout plan

1. **Dev**: dry-run with curl and test callid; verify `next` chaining and MP3 serving.
2. **Staging**: enable `AI_REPLIES_ENABLED`, MAX_TURNS=1, short messages.
3. **Prod**: MIL only; keep closing MP3; observe 1–2 days; then consider MAX_TURNS=2.

## 12) Test cases

* MIL, mode unset → returns `play+next=record1`.
* `record1` → returns `record` with `silencedetection=yes`, `timelimit=12`, `next=reply1`.
* POST `/recordings` with valid `wav` → creates `reply-<callid>-1.mp3`, 200.
* `reply1` before file exists → fallback `play`; after file exists → reply `play+next=record2`.
* Non-MIL → `connect` to fallback; 46elks call history shows `result: success/busy`.
* Bad TTS key/voice → fallback MP3 plays (no hangup).
* MP3 URL 404 → 46elks logs show fetch failure; next call fixed URL works.

## 13) Risks & mitigations

* **Latency spikes** (TTS/STT): keep outputs short; use 12s or less timelimit and silence detection; cache common replies.
* **TLS/CA trust**: host audio on `calls.mtup.xyz` (valid Let’s Encrypt); avoid self-signed.
* **Cost overrun**: Starter ElevenLabs plan (~30k credits) is pilot-sized; monitor turn count and reply length.

## 14) Implementation notes (diffs)

* Extend `/calls` to route by `mode` and `callid`; add an 8s wait loop before fallback when in `replyN`.
* Add `POST /recordings` to download `wav`, run STT→LLM→TTS, and write `reply-*.mp3`.
* ElevenLabs TTS: `POST https://api.elevenlabs.io/v1/text-to-speech/:voice_id` with `accept: audio/mpeg`, `xi-api-key`.
* Keep current behavior for non-MIL unchanged.


