# els-calls

Inbound-only call router for a single Swedish 46elks virtual number.

## Purpose

Provide a calm, consistent message to one specific caller (e.g. elderly relative) while forwarding all other calls to a regular mobile number.

- If call is from `MIL_NUMBER` → play a pre-recorded MP3 over the phone, then hang up.
- If call is from anyone else → connect to `FALLBACK_NUMBER`.

Built for low cost, high reliability, minimal moving parts.

## Architecture

- Provider: [46elks](https://46elks.com/)
- Number: 1x Swedish virtual number with voice enabled.
- Hosting: Dokploy/Hostinger VPS
- App:
  - Python + Bottle
  - Gunicorn
  - Dockerized, exposed on port `8000`
- Entry:
  - `voice_start` on the 46elks number points to this app:
    - `https://calls.mtup.xyz/calls`

46elks calls our webhook on every inbound call and executes returned [call actions]. :contentReference[oaicite:0]{index=0}

## Endpoints

### `GET /`

Health check.

- Returns `200 ok`.

### `GET /audio/<filename>`

Static file server for audio.

- Root: `/app/audio`
- Used for voicemail message MP3.
- Example:
  - `https://calls.mtup.xyz/audio/Aha-remix.mp3`

### `POST /calls`

Main 46elks `voice_start` webhook.

Input (form-encoded by 46elks):

- `from`: caller in E.164 format (e.g. `+4670xxxxxxx`)
- `to`: our 46elks number
- other standard 46elks fields ignored

Logic:

```python
from_number = (request.forms.get("from") or "").replace(" ", "")

if from_number == MIL_NUMBER:
    return {
        "play": "https://calls.mtup.xyz/audio/Aha-remix.mp3"
    }

return {
    "connect": FALLBACK_NUMBER
}

