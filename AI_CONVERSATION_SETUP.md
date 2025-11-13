# AI Conversation System Setup Guide

## Overview

This system adds AI-powered conversation capabilities to your existing 46elks call system. When enabled, calls from the MIL number will engage in a "listen → think → speak" loop using:

- **STT (Speech-to-Text)**: Soniox API
- **LLM (Language Model)**: DeepSeek API  
- **TTS (Text-to-Speech)**: ElevenLabs API with your custom voice

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Add these environment variables to your `.env` file:

```env
SONIOX_API_KEY=your_soniox_api_key_here
DEEPSEEK_API_KEY=your_deepseek_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

### 3. Verify Custom Audio Files

Ensure these custom-recorded MP3 files are in your `audio/` directory:
- `hello.mp3` - Initial greeting
- `waiting.mp3` - "Please wait" message  
- `goodbye.mp3` - Closing message
- `fallback.mp3` - Generic reassurance message

These should be your own recorded voice messages for a more personal touch.

### 4. Test the System

```bash
python test_ai_conversation.py
```

This will verify your custom audio files and API configurations.

### 5. Deploy and Test

Deploy your updated application and test with actual calls to your 46elks number.

Your custom voice recordings will be used throughout the conversation flow.

## API Configuration

### Soniox (STT)
- Sign up at [Soniox](https://soniox.com/)
- Get API key from dashboard
- Supports Swedish language

### DeepSeek (LLM)  
- Sign up at [DeepSeek](https://platform.deepseek.com/)
- Create API key in console
- Uses `deepseek-chat` model

### ElevenLabs (TTS)
- Uses your existing API key
- Voice ID: `5JD3K0SA9QTSxc9tVNpP` (your custom voice)
- Model: `eleven_multilingual_v2`

## Configuration Settings

The system uses these settings in `settings.json`:

```json
{
  "MAX_TURNS": 3,
  "LANG": "sv",
  "AI_REPLIES_ENABLED": true
}
```

- **MAX_TURNS**: Maximum conversation exchanges (1-5 recommended)
- **LANG**: Language code (`sv` for Swedish)
- **AI_REPLIES_ENABLED**: Toggle AI conversation on/off

## Call Flow

When AI replies are enabled and MIL calls:

1. **Initial Greeting**: Plays `hello.mp3`
2. **Recording**: Records up to 12 seconds with silence detection
3. **Processing**: STT → LLM → TTS pipeline
4. **Response**: Plays generated `reply-{callid}-{turn}.mp3`
5. **Repeat**: Continues until MAX_TURNS reached
6. **Closing**: Plays `goodbye.mp3`

## Dashboard Integration

The system integrates with your existing dashboard. Add these controls to enable AI settings management:

```html
<div class="section">
    <h3>AI Conversation Settings</h3>
    <form id="ai-settings-form" onsubmit="return false;">
        <label>
            <input type="checkbox" id="ai_enabled" name="ai_enabled">
            Enable AI Replies
        </label>
        
        <label for="max_turns">Maximum Conversation Turns:</label>
        <input type="number" id="max_turns" name="max_turns" min="1" max="5" value="3">
        
        <label for="language">Language:</label>
        <select id="language" name="language">
            <option value="sv">Swedish</option>
            <option value="en">English</option>
        </select>
        
        <button type="submit">Save AI Settings</button>
    </form>
</div>
```

## File Management

### Generated Files
- `reply-{callid}-{turn}.mp3` - AI response audio files
- Automatically cleaned up after 24 hours

### Cleanup Commands
```bash
# List conversation files
python cleanup_conversation_files.py --list

# Dry run (see what would be deleted)
python cleanup_conversation_files.py --dry-run

# Clean files older than 24 hours (default)
python cleanup_conversation_files.py

# Clean files older than 12 hours
python cleanup_conversation_files.py --hours 12
```

## Error Handling

- **STT Failure**: Uses fallback response
- **LLM Failure**: Generic comforting response
- **TTS Failure**: Plays `fallback.mp3`
- **Timeout**: Plays `waiting.mp3` and retries
- **API Errors**: Graceful degradation to fallback behavior

## Monitoring & Logging

The system provides detailed logging:

```
🎙️  STT Result: [transcribed text]
🧠 LLM Response: [AI response text]  
🔊 TTS saved: [filename] ([size] bytes)
⏱️  Timing - STT: [time]s, LLM: [time]s, TTS: [time]s, Total: [time]s
```

## Performance Targets

- **Turn Time**: Target ≤3.0 seconds (end of talk → reply playback)
- **Recording**: 12 second limit with silence detection
- **Response Length**: 1-2 sentences for natural conversation flow

## Security & Privacy

- **Data Minimization**: Only process necessary audio data
- **Temporary Storage**: Audio files deleted after 24 hours
- **API Security**: All external API calls use HTTPS
- **GDPR Compliance**: Swedish context with privacy considerations

## Troubleshooting

### Common Issues

1. **Missing Audio Files**
   - Verify all required MP3 files are in the `audio/` directory
   - Ensure files are properly recorded and accessible

2. **API Key Errors**
   - Verify keys in `.env` file
   - Check API quotas and billing

3. **High Latency**
   - Monitor timing logs
   - Consider shorter responses
   - Check network connectivity

4. **No AI Responses**
   - Verify `AI_REPLIES_ENABLED: true` in settings
   - Check MIL number configuration

### Testing Commands

```bash
# Test complete pipeline
python test_ai_conversation.py

# Test TTS only
python tts.py

# Test ElevenLabs API
python eleven_test.py

# Generate specific audio file
python audio_manager.py generate "Your test message"
```

## Deployment Notes

- Ensure all dependencies are installed on your VPS
- Verify API keys are set in production environment
- Monitor disk space for audio file accumulation
- Set up regular cleanup with cron job if needed
- Your custom voice recordings will provide a consistent, personal experience

## Support

For issues with:
- **STT**: Contact Soniox support
- **LLM**: Contact DeepSeek support  
- **TTS**: Contact ElevenLabs support
- **Integration**: Check application logs and test scripts

The system is designed to be robust and handle failures gracefully, ensuring callers always receive a response even when individual components fail.