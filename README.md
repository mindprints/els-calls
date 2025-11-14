# els-calls

Inbound-only call router for a single Swedish 46elks virtual number with AI conversation capabilities.

## Purpose

Provide intelligent, dementia-safe conversation responses to one specific caller while forwarding all other calls to a regular mobile number.

- **AI Conversation Mode**: If call is from a specific number (`MIL_NUMBER`) and AI is enabled → engage in multi-turn conversation using STT→LLM→TTS pipeline
- **Fallback Mode**: If call is from anyone else → connect to a fallback number (`FALLBACK_NUMBER`)
- **Legacy Mode**: If AI is disabled for MIL calls → play pre-recorded MP3 and hang up

The `MIL_NUMBER`, `FALLBACK_NUMBER`, audio files, and AI conversation settings are all configurable via a simple web dashboard.

## Architecture

- **Provider**: [46elks](https://46elks.com/)
- **Number**: 1x Swedish virtual number with voice enabled
- **Hosting**: Dokploy/Hostinger VPS
- **App**: 
  - Python + Bottle backend API
  - Gunicorn
  - Simple vanilla JS/HTML frontend for dashboard
  - Dockerized, exposed on port `8000`

### AI Conversation Pipeline

- **STT Provider**: [Soniox API](https://soniox.com/) for Swedish speech recognition
- **LLM Provider**: [DeepSeek API](https://www.deepseek.com/) for dementia-safe Swedish responses
- **TTS Provider**: [ElevenLabs API](https://elevenlabs.io/) with custom voice ID `5JD3K0SA9QTSxc9tVNpP`
- **Call Flow**: 46elks integration with `play → record → play (AI reply)` chain
- **Error Handling**: Graceful fallbacks using custom MP3 recordings

### Configuration

- **Persisted in**: `settings.json`
- **Managed via**: Web dashboard at application root (`/`)
- **File Storage**: Uploaded audio files stored in `/app/audio` directory
- **Conversation Files**: Temporary conversation recordings automatically cleaned up after 24 hours

### Entry Point

- `voice_start` on the 46elks number points to this app:
  - `https://calls.mtup.xyz/calls`

46elks calls our webhook on every inbound call and executes returned [call actions].

## Features

### AI Conversation System

- **Multi-turn Conversations**: Configurable conversation depth (default: 3 turns)
- **Dementia-Safe Responses**: LLM optimized for clear, simple Swedish communication
- **Fast Response Time**: Target ≤3 seconds from end of speech to reply playback
- **Silence Detection**: 12-second recording limit with intelligent silence handling
- **Language Support**: Primary Swedish with configurable language settings

### Dashboard Controls

The dashboard allows you to:
- Set the `MIL_NUMBER` (the special caller)
- Set the `FALLBACK_NUMBER` (where other calls are forwarded)
- Upload new audio message files (MP3 format)
- Select which uploaded audio file is active
- Enable/disable AI conversation replies
- Configure maximum conversation turns
- Set conversation language

## Configuration

### Environment Variables

Required API keys for AI features:
```bash
SONIOX_API_KEY=your_soniox_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key  
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

### Settings (settings.json)

```json
{
  "MIL_NUMBER": "+46705152223",
  "FALLBACK_NUMBER": "+46733466657",
  "ACTIVE_AUDIO_FILE": "Aha-remix.mp3",
  "SCHEDULE": [],
  "MAX_TURNS": 3,
  "LANG": "sv",
  "AI_REPLIES_ENABLED": true
}
```

## Endpoints

### Web Dashboard

- `GET /` - Serves the main HTML dashboard for configuration

### Call Handling

- `POST /calls` - Main 46elks `voice_start` webhook
  - **AI Mode**: If `AI_REPLIES_ENABLED=true` and caller is `MIL_NUMBER` → engage in conversation
  - **Legacy Mode**: If `AI_REPLIES_ENABLED=false` and caller is `MIL_NUMBER` → play active audio file
  - **Fallback**: All other calls → connect to `FALLBACK_NUMBER`

### Settings Management

- `GET /settings` - Fetch current configuration from `settings.json`
- `POST /settings` - Update and save configuration to `settings.json`

### Audio Management

- `GET /audio/<filename>` - Serve specific audio file (used by 46elks)
- `GET /audio_files` - Get list of all available MP3 files
- `POST /upload_audio` - Upload new MP3 files

### AI Conversation

- `POST /conversation` - Handle AI conversation turn (internal use)
- Embedded AI conversation module handles STT→LLM→TTS pipeline

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
```

### Production Environment

- **Platform**: Docker deployment via Dokploy
- **VPS**: Hostinger/Dokploy environment  
- **Domain**: calls.mtup.xyz
- **Port**: 8000

## File Structure

```
els-calls/
├── app.py                 # Main application with embedded AI conversation
├── audio_manager.py       # Audio file management utilities
├── tts.py                 # ElevenLabs TTS integration
├── cleanup_conversation_files.py  # Automatic file cleanup
├── eleven_test.py         # ElevenLabs API testing
├── test_ai_conversation.py # AI conversation testing
├── requirements.txt       # Python dependencies
├── settings.json          # Application configuration
├── Dockerfile            # Container configuration
├── index.html            # Dashboard interface
├── index_wip.html        # Work-in-progress dashboard
├── audio/                # Uploaded audio files directory
├── images/               # Dashboard images and assets
├── AI_CONVERSATION_SETUP.md  # AI integration documentation
├── chat_extension.md     # Conversation system specifications
└── README.md             # This file
```

## Dependencies

```txt
bottle
gunicorn
python-dotenv
requests
elevenlabs
```

## Monitoring & Maintenance

- **File Cleanup**: Conversation recordings automatically deleted after 24 hours
- **Error Handling**: Graceful fallback to MP3 files if AI services fail
- **Performance**: Monitor STT→LLM→TTS pipeline latency
- **API Quotas**: Track usage for Soniox, DeepSeek, and ElevenLabs APIs

## Troubleshooting

### Common Issues

1. **AI Features Not Working**: Check environment variables and API keys
2. **Dashboard Controls Unresponsive**: Verify JavaScript is enabled and check browser console
3. **Audio Upload Fails**: Ensure files are MP3 format and under size limits
4. **Conversation Files Not Cleaning Up**: Check cleanup script execution

### Rollback Plan

If AI features cause issues:
1. Set `AI_REPLIES_ENABLED: false` in settings to disable AI conversation
2. System will automatically fall back to legacy MP3 playback behavior
3. Non-MIL calls continue unchanged to fallback number

## Development

The system maintains backward compatibility while adding AI conversation capabilities. All existing voicemail functionality remains intact when AI features are disabled.