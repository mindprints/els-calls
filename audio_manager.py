"""
Audio Manager for ElevenLabs TTS Integration

This script provides comprehensive audio management capabilities including:
- Text-to-speech generation using ElevenLabs
- Audio file playback and management
- Batch processing and organization
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    import pygame
except ImportError:
    print("Installing pygame...")
    os.system(f"{sys.executable} -m pip install pygame")
    import pygame

try:
    from dotenv import load_dotenv
    from elevenlabs import ElevenLabs
except ImportError:
    print("Installing required packages...")
    os.system(f"{sys.executable} -m pip install python-dotenv elevenlabs")
    from dotenv import load_dotenv
    from elevenlabs import ElevenLabs


class AudioManager:
    """Comprehensive audio management for ElevenLabs TTS integration"""

    def __init__(self):
        """Initialize audio manager with configuration"""
        self.audio_dir = Path("audio")
        self.config_file = Path("audio_config.json")
        self.elevenlabs_client = None
        self.pygame_initialized = False

        # Create audio directory if it doesn't exist
        self.audio_dir.mkdir(exist_ok=True)

        # Load configuration
        self.config = self._load_config()

        # Initialize pygame for audio playback
        self._init_pygame()

        # Initialize ElevenLabs client
        self._init_elevenlabs()

    def _load_config(self) -> Dict:
        """Load or create configuration file"""
        default_config = {
            "default_voice_id": "5JD3K0SA9QTSxc9tVNpP",
            "default_model": "eleven_multilingual_v2",
            "audio_history": [],
            "favorite_voices": [],
            "output_format": "mp3_44100_128",
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    return {**default_config, **json.load(f)}
            except Exception as e:
                print(f"Warning: Could not load config: {e}")
                return default_config
        else:
            return default_config

    def _save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")

    def _init_pygame(self):
        """Initialize pygame for audio playback"""
        try:
            pygame.mixer.init()
            self.pygame_initialized = True
            print("✅ Audio playback initialized")
        except Exception as e:
            print(f"❌ Failed to initialize audio playback: {e}")

    def _init_elevenlabs(self):
        """Initialize ElevenLabs client"""
        try:
            load_dotenv()
            api_key = os.getenv("ELEVENLABS_API_KEY")

            if not api_key:
                print("❌ ELEVENLABS_API_KEY not found in environment")
                return

            self.elevenlabs_client = ElevenLabs(api_key=api_key)
            print("✅ ElevenLabs client initialized")

        except Exception as e:
            print(f"❌ Failed to initialize ElevenLabs: {e}")

    def generate_tts(
        self,
        text: str,
        voice_id: str = None,
        model_id: str = None,
        output_filename: str = None,
    ) -> Optional[str]:
        """
        Generate text-to-speech audio using ElevenLabs

        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID (uses default if None)
            model_id: Model to use (uses default if None)
            output_filename: Output filename (auto-generated if None)

        Returns:
            Path to generated audio file or None if failed
        """
        if not self.elevenlabs_client:
            print("❌ ElevenLabs client not available")
            return None

        voice_id = voice_id or self.config["default_voice_id"]
        model_id = model_id or self.config["default_model"]

        # Generate output filename if not provided
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_text = "".join(
                c for c in text[:20] if c.isalnum() or c in (" ", "_", "-")
            ).strip()
            safe_text = safe_text.replace(" ", "_")
            output_filename = f"tts_{safe_text}_{timestamp}.mp3"

        output_path = self.audio_dir / output_filename

        try:
            print(f"🎙️  Generating TTS: '{text[:50]}...'")
            print(f"   Voice: {voice_id[:8]}...")
            print(f"   Model: {model_id}")

            # Generate audio
            audio_generator = self.elevenlabs_client.text_to_speech.convert(
                voice_id=voice_id,
                output_format=self.config["output_format"],
                enable_logging=True,
                optimize_streaming_latency=0,
                text=text,
                model_id=model_id,
            )

            # Collect audio data
            audio_data = b""
            for chunk in audio_generator:
                if isinstance(chunk, bytes):
                    audio_data += chunk

            # Save to file
            with open(output_path, "wb") as f:
                f.write(audio_data)

            # Update configuration
            audio_info = {
                "filename": output_filename,
                "text": text,
                "voice_id": voice_id,
                "model_id": model_id,
                "timestamp": datetime.now().isoformat(),
                "file_size": len(audio_data),
            }

            self.config["audio_history"].append(audio_info)
            self._save_config()

            print(f"✅ Audio saved: {output_filename} ({len(audio_data)} bytes)")
            return str(output_path)

        except Exception as e:
            print(f"❌ TTS generation failed: {e}")
            return None

    def play_audio(self, file_path: str) -> bool:
        """
        Play an audio file

        Args:
            file_path: Path to audio file

        Returns:
            True if playback successful, False otherwise
        """
        if not self.pygame_initialized:
            print("❌ Audio playback not available")
            return False

        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False

        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            print(f"🔊 Playing: {os.path.basename(file_path)}")

            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

            print(f"✅ Finished: {os.path.basename(file_path)}")
            return True

        except Exception as e:
            print(f"❌ Playback failed: {e}")
            return False

    def list_audio_files(self, pattern: str = "*.mp3") -> List[Path]:
        """
        List audio files in the audio directory

        Args:
            pattern: File pattern to match

        Returns:
            List of audio file paths
        """
        return sorted(self.audio_dir.glob(pattern))

    def get_elevenlabs_files(self) -> List[Path]:
        """Get only ElevenLabs generated audio files"""
        patterns = [
            "elevenlabs_*.mp3",
            "test_voice.mp3",
            "voice_test_*.mp3",
            "tts_*.mp3",
        ]
        files = []

        for pattern in patterns:
            files.extend(self.audio_dir.glob(pattern))

        return sorted(set(files))

    def play_all_elevenlabs(self):
        """Play all ElevenLabs generated audio files"""
        files = self.get_elevenlabs_files()

        if not files:
            print("❌ No ElevenLabs generated files found")
            return

        print(f"🎙️  Playing {len(files)} ElevenLabs files:")
        for file_path in files:
            self.play_audio(str(file_path))
            print()

    def show_audio_history(self):
        """Show TTS generation history"""
        history = self.config.get("audio_history", [])

        if not history:
            print("📝 No TTS generation history")
            return

        print(f"📝 TTS History ({len(history)} items):")
        for i, item in enumerate(reversed(history[-10:]), 1):  # Show last 10
            print(f"  {i}. {item['filename']}")
            print(f"     Text: {item['text'][:50]}...")
            print(f"     Voice: {item['voice_id'][:8]}...")
            print(f"     Time: {item['timestamp'][:16]}")
            print()

    def cleanup_old_files(self, days_old: int = 30):
        """
        Clean up audio files older than specified days

        Args:
            days_old: Delete files older than this many days
        """
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        deleted_count = 0

        for file_path in self.audio_dir.glob("*.mp3"):
            if file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    print(f"🗑️  Deleted: {file_path.name}")
                except Exception as e:
                    print(f"❌ Failed to delete {file_path.name}: {e}")

        print(f"✅ Cleanup complete: {deleted_count} files deleted")

    def interactive_mode(self):
        """Run interactive audio management mode"""
        while True:
            print("\n" + "=" * 50)
            print("🎵 AUDIO MANAGER")
            print("=" * 50)
            print("1. Generate TTS")
            print("2. Play audio file")
            print("3. Play all ElevenLabs files")
            print("4. List audio files")
            print("5. Show TTS history")
            print("6. Cleanup old files")
            print("7. Exit")
            print("-" * 50)

            try:
                choice = input("Select option (1-7): ").strip()

                if choice == "1":
                    text = input("Enter text to convert: ").strip()
                    if text:
                        voice_id = input(
                            f"Voice ID [default: {self.config['default_voice_id']}]: "
                        ).strip()
                        voice_id = voice_id or self.config["default_voice_id"]
                        self.generate_tts(text, voice_id)

                elif choice == "2":
                    files = self.list_audio_files()
                    if files:
                        print("Available files:")
                        for i, f in enumerate(files, 1):
                            print(f"  {i}. {f.name}")

                        try:
                            file_num = int(input("Enter file number: "))
                            if 1 <= file_num <= len(files):
                                self.play_audio(str(files[file_num - 1]))
                            else:
                                print("❌ Invalid file number")
                        except ValueError:
                            print("❌ Please enter a valid number")
                    else:
                        print("❌ No audio files found")

                elif choice == "3":
                    self.play_all_elevenlabs()

                elif choice == "4":
                    files = self.list_audio_files()
                    if files:
                        print(f"📁 Found {len(files)} audio files:")
                        for f in files:
                            print(f"  - {f.name}")
                    else:
                        print("❌ No audio files found")

                elif choice == "5":
                    self.show_audio_history()

                elif choice == "6":
                    try:
                        days = input(
                            "Delete files older than [default: 30] days: "
                        ).strip()
                        days = int(days) if days else 30
                        self.cleanup_old_files(days)
                    except ValueError:
                        print("❌ Please enter a valid number")

                elif choice == "7":
                    print("👋 Goodbye!")
                    break

                else:
                    print("❌ Invalid option")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break


def main():
    """Main function"""
    manager = AudioManager()

    if len(sys.argv) > 1:
        # Command line mode
        if sys.argv[1] == "generate":
            text = (
                " ".join(sys.argv[2:])
                if len(sys.argv) > 2
                else "Hello, this is a test."
            )
            manager.generate_tts(text)
        elif sys.argv[1] == "play":
            manager.play_all_elevenlabs()
        elif sys.argv[1] == "list":
            files = manager.list_audio_files()
            for f in files:
                print(f.name)
        elif sys.argv[1] == "cleanup":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            manager.cleanup_old_files(days)
        else:
            print(
                "Usage: python audio_manager.py [generate|play|list|cleanup|interactive]"
            )
    else:
        # Interactive mode
        manager.interactive_mode()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
