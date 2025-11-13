"""
Cleanup Script for Old Conversation Files

This script automatically removes conversation files older than 24 hours
to prevent the audio directory from filling up with temporary files.
"""

import os
import time
from datetime import datetime, timedelta
from pathlib import Path


def cleanup_old_conversation_files(audio_dir="audio", hours_old=24):
    """
    Remove conversation files older than specified hours

    Args:
        audio_dir: Directory containing audio files
        hours_old: Delete files older than this many hours (default: 24)
    """
    audio_path = Path(audio_dir)

    if not audio_path.exists():
        print(f"❌ Audio directory not found: {audio_dir}")
        return

    # Calculate cutoff time
    cutoff_time = time.time() - (hours_old * 3600)
    deleted_count = 0
    total_size = 0

    print(f"🧹 Cleaning up conversation files older than {hours_old} hours...")
    print(f"📁 Scanning directory: {audio_path.absolute()}")

    # Find and delete old conversation files
    for file_path in audio_path.glob("reply-*.mp3"):
        try:
            # Get file modification time
            file_mtime = file_path.stat().st_mtime

            if file_mtime < cutoff_time:
                file_size = file_path.stat().st_size
                file_age = time.time() - file_mtime
                file_age_hours = file_age / 3600

                # Delete the file
                file_path.unlink()
                deleted_count += 1
                total_size += file_size

                print(
                    f"🗑️  Deleted: {file_path.name} "
                    f"({file_size:,} bytes, {file_age_hours:.1f} hours old)"
                )

        except Exception as e:
            print(f"❌ Failed to delete {file_path.name}: {e}")

    # Summary
    print(f"\n📊 Cleanup Summary:")
    print(f"   Files deleted: {deleted_count}")
    print(
        f"   Total space freed: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)"
    )

    if deleted_count == 0:
        print("   No old files found to clean up")
    else:
        print(f"   ✅ Cleanup completed successfully")


def list_conversation_files(audio_dir="audio"):
    """
    List all conversation files with their ages
    """
    audio_path = Path(audio_dir)

    if not audio_path.exists():
        print(f"❌ Audio directory not found: {audio_dir}")
        return

    conversation_files = list(audio_path.glob("reply-*.mp3"))

    if not conversation_files:
        print("📁 No conversation files found")
        return

    print(f"📁 Conversation files in {audio_path.absolute()}:")
    print("-" * 80)

    for file_path in sorted(conversation_files, key=lambda x: x.stat().st_mtime):
        file_mtime = file_path.stat().st_mtime
        file_age = time.time() - file_mtime
        file_size = file_path.stat().st_size

        age_hours = file_age / 3600
        age_days = file_age / 86400

        if age_days >= 1:
            age_str = f"{age_days:.1f} days"
        else:
            age_str = f"{age_hours:.1f} hours"

        print(f"  {file_path.name}")
        print(f"    Size: {file_size:,} bytes | Age: {age_str}")
        print()


def main():
    """Main function with command line interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Clean up old conversation files")
    parser.add_argument(
        "--audio-dir", default="audio", help="Audio directory path (default: audio)"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Delete files older than this many hours (default: 24)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List conversation files instead of cleaning up",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )

    args = parser.parse_args()

    if args.list:
        list_conversation_files(args.audio_dir)
    elif args.dry_run:
        print("🔍 DRY RUN - Showing files that would be deleted:")
        # For dry run, we'll just list files that would be deleted
        audio_path = Path(args.audio_dir)
        cutoff_time = time.time() - (args.hours * 3600)

        old_files = []
        for file_path in audio_path.glob("reply-*.mp3"):
            if file_path.stat().st_mtime < cutoff_time:
                old_files.append(file_path)

        if old_files:
            print(f"Would delete {len(old_files)} files older than {args.hours} hours:")
            for file_path in old_files:
                file_age = (time.time() - file_path.stat().st_mtime) / 3600
                print(f"  - {file_path.name} ({file_age:.1f} hours old)")
        else:
            print("No files would be deleted")
    else:
        cleanup_old_conversation_files(args.audio_dir, args.hours)


if __name__ == "__main__":
    main()
