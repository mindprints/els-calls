# els-calls

Inbound-only call router for a single Swedish 46elks virtual number.

## Purpose

Provide a calm, consistent message to one specific caller while forwarding all other calls to a regular mobile number.

- If call is from a specific number (`MIL_NUMBER`) → play a pre-recorded MP3 over the phone, then hang up.
- If call is from anyone else → connect to a fallback number (`FALLBACK_NUMBER`).

The `MIL_NUMBER`, `FALLBACK_NUMBER`, and active audio file are all configurable via a simple web dashboard.

## Architecture

- Provider: [46elks](https://46elks.com/)
- Number: 1x Swedish virtual number with voice enabled.
- Hosting: Dokploy/Hostinger VPS
- App:
  - Python + Bottle backend API
  - Gunicorn
  - Simple vanilla JS/HTML frontend for dashboard
  - Dockerized, exposed on port `8000`
- Configuration:
  - Persisted in `settings.json`
  - Managed via the web dashboard.
- Entry:
  - `voice_start` on the 46elks number points to this app:
    - `https://calls.mtup.xyz/calls`

46elks calls our webhook on every inbound call and executes returned [call actions]. :contentReference[oaicite:0]{index=0}

## Configuration

Configuration is managed via a simple web dashboard served at the application's root (`/`).

The dashboard allows you to:
- Set the `MIL_NUMBER` (the special caller).
- Set the `FALLBACK_NUMBER` (where other calls are forwarded).
- Upload new audio message files (MP3 format).
- Select which of the uploaded audio files is the active one.

All settings are stored in `settings.json` within the Docker container.

## Endpoints

### `GET /`

Serves the main HTML dashboard for configuration.

### `POST /calls`

Main 46elks `voice_start` webhook. This is the endpoint that 46elks should be configured to call for incoming voice calls.

- **Logic**: It checks the incoming `from` number against the `MIL_NUMBER` from `settings.json`.
  - If it matches, it plays the `ACTIVE_AUDIO_FILE` from `settings.json`.
  - Otherwise, it connects the call to the `FALLBACK_NUMBER`.

### `GET /settings`

API endpoint to fetch the current configuration from `settings.json`. Used by the dashboard.

### `POST /settings`

API endpoint to update and save the configuration to `settings.json`. Used by the dashboard.

### `GET /audio/<filename>`

Serves a specific audio file. Used by 46elks to play the message.

### `GET /audio_files`

API endpoint to get a list of all available MP3 files in the `/app/audio` directory. Used by the dashboard.

### `POST /upload_audio`

API endpoint for uploading new MP3 files. Used by the dashboard.
