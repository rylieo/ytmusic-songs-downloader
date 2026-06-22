#!/usr/bin/env python3
"""
YouTube Music Downloader - Strict Playlist Isolation & Index-Based Skip Edition
Clean Architecture, File-based Cookie Auth with Pre-flight Validation.
Strictly downloads tracks parsed directly from the playlist without fallback search.
"""

import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Dict, Optional, Tuple

from mutagen.easyid3 import EasyID3
from mutagen.id3 import APIC, ID3
from mutagen.id3 import error as ID3Error
from yt_dlp import YoutubeDL

# Validasi Library Utama
try:
    from ytmusicapi import YTMusic
except ImportError:
    print("Error: Library 'ytmusicapi' tidak ditemukan.")
    print("Silakan install: pip install ytmusicapi")
    sys.exit(1)

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False
    print("[Warning] Modul 'Pillow' tidak ditemukan. Cover art tidak akan di-crop 1:1.")


# Variabel Global untuk status penggunaan cookies
USE_COOKIES = True


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def clean_track_title(title: str) -> str:
    """Membersihkan judul dari noise teks promosi video."""
    cleaned = re.sub(
        r'(?i)[\(\[].*?(official|music video|lyric|1080p|full hd|hq|audio|video|live).*?[\)\]]', 
        '', 
        title
    )
    return " ".join(cleaned.split())


def sanitize_filename(name: str) -> str:
    """Memastikan nama file aman untuk semua OS (Windows, Linux, macOS)."""
    return ''.join(c for c in name if c not in r'<>:\"/\\|?*').strip()


def select_quality() -> Tuple[str, Optional[int]]:
    menu = """
Select output quality/format:
1) Original quality (no re‑encoding)
2) MP3 – High quality (320 kbps)
3) MP3 – Medium quality (192 kbps)
4) MP3 – Low quality (128 kbps)
Enter choice [1-4]: """
    while True:
        choice = input(menu).strip()
        if choice in {'1', '2', '3', '4'}:
            mapping = {'1': ('original', None), '2': ('mp3', 320), '3': ('mp3', 192), '4': ('mp3', 128)}
            return mapping[choice]
        print("Invalid choice, please enter 1-4.")


def download_thumbnail(url: str, dest: Path) -> Optional[Path]:
    """Mengunduh thumbnail dan melakukan crop 1:1 secara aman."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(dest, 'wb') as out_file:
            out_file.write(response.read())
        
        if HAS_PILLOW:
            with Image.open(dest) as img:
                width, height = img.size
                if width != height:
                    new_size = min(width, height)
                    left = (width - new_size) / 2
                    top = (height - new_size) / 2
                    img.crop((left, top, left + new_size, top + new_size)).save(dest)
        return dest
    except Exception as e:
        print(f"  [Warning] Gagal memproses thumbnail: {e}")
        if dest.exists():
            dest.unlink()
        return None


def embed_metadata(audio_path: Path, metadata: Dict[str, str], cover_path: Optional[Path] = None) -> None:
    """Menyuntikkan ID3 tags dan cover art ke file audio."""
    try:
        audio = EasyID3(str(audio_path))
    except ID3Error:
        audio = EasyID3()
        
    for tag, value in metadata.items():
        if value:
            audio[tag] = value
    audio.save()

    if cover_path and audio_path.suffix.lower() == '.mp3':
        try:
            id3 = ID3(str(audio_path))
            with open(cover_path, 'rb') as img:
                id3.add(APIC(mime='image/jpeg', type=3, desc='Cover', data=img.read()))
            id3.save()
        except Exception as e:
            print(f"  [Warning] Gagal menyuntikkan cover art: {e}")


def convert_to_mp3(input_file: Path, output_file: Path, bitrate: int) -> bool:
    """Fungsi mandiri untuk menangani konversi FFmpeg."""
    cmd = [
        'ffmpeg', '-y', '-i', str(input_file), '-vn',
        '-ab', f'{bitrate}k', '-ar', '44100', '-loglevel', 'error', str(output_file)
    ]
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  [FFmpeg Error] Gagal konversi: {e}")
        return False
    except KeyboardInterrupt:
        raise KeyboardInterrupt


def get_base_ydl_opts() -> dict:
    """Menyediakan opsi dasar yt-dlp secara kondisional berdasarkan status validasi cookies."""
    opts = {
        'quiet': True,
        'no_warnings': True,
        'js_runtimes': {'node': {}},
    }
    cookie_file = Path("cookies.txt")
    if USE_COOKIES and cookie_file.exists():
        opts['cookiefile'] = str(cookie_file)
    return opts


def check_cookies_validity() -> None:
    """Memeriksa keberadaan dan validitas berkas cookies.txt secara lokal sebelum skrip dieksekusi."""
    global USE_COOKIES
    cookie_file = Path("cookies.txt")

    if not cookie_file.exists():
        print("[!] File cookies.txt tidak ditemukan.")
        choice = input("Lanjut tanpa cookies? (y/n): ").strip().lower()
        if choice == 'y':
            USE_COOKIES = False
            print("[✓] Melanjutkan tanpa cookies.\n")
            return
        else:
            print("[✕] Batalkan proses.")
            sys.exit(0)

    print("[*] Memverifikasi cookies.txt...")
    try:
        with open(cookie_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        has_netscape_header = "Netscape HTTP Cookie File" in content
        has_auth_tokens = any(token in content for token in ["LOGIN_INFO", "__Secure-3PSID", "SID"])

        if has_netscape_header and has_auth_tokens:
            print("[✓] Cookies terverifikasi.\n")
            return
        else:
            raise ValueError("Struktur file salah atau token tidak dikenali.")

    except Exception as e:
        print(f"[!] Cookies tidak valid atau rusak: {e}")
        choice = input("Lanjut tanpa cookies? (y/n): ").strip().lower()
        if choice == 'y':
            USE_COOKIES = False
            print("[✓] Melanjutkan tanpa menggunakan cookies.\n")
        else:
            print("[✕] Batalkan proses.")
            sys.exit(0)


def process_entry(url: str, base_dir: Path, output_format: str, bitrate: Optional[int], 
                  track_index: Optional[int] = None) -> bool:
    """
    Memproses unduhan track secara strict berdasarkan direct URL dari playlist.
    Tanpa search fallback ke luar system.
    """
    ydl_opts = get_base_ydl_opts()
    ydl_opts.update({'ignoreerrors': True})
    info = None
    
    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except (Exception, KeyboardInterrupt):
            raise KeyboardInterrupt

    if not info:
        print(f"  [Gagal] Track tidak dapat diakses.")
        return False

    raw_title = info.get('track') or info.get('title', 'Unknown Track')
    title = clean_track_title(raw_title)
    artist = info.get('artist') or info.get('uploader') or 'Unknown Artist'
    album = info.get('album') or ''
    thumbnail_url = info.get('thumbnail')
    video_id = info.get('id', 'temp_id')

    display_name = f"{artist} - {title}"
    if track_index is not None:
        display_name = f"{track_index:02d} - {display_name}"
    safe_final_name = sanitize_filename(display_name)

    print(f"  [Downloading] {display_name}")
    
    final_path = base_dir / f"{safe_final_name}.mp3" if output_format != 'original' else base_dir / f"{safe_final_name}"
    
    temp_template = str(base_dir / f"{video_id}.%(ext)s")
    dl_opts = get_base_ydl_opts()
    dl_opts.update({
        'quiet': False,
        'format': 'bestaudio/best',
        'outtmpl': temp_template,
        'ignoreerrors': True
    })

    try:
        with YoutubeDL(dl_opts) as ydl_dl:
            ydl_dl.download([url])
            
        downloaded_files = list(base_dir.glob(f"{video_id}.*"))
        if not downloaded_files:
            return False
        
        raw_path = downloaded_files[0]
        ext = raw_path.suffix
        
        if output_format == 'original':
            final_path = base_dir / f"{safe_final_name}{ext}"
            if final_path.exists():
                final_path.unlink()
            raw_path.rename(final_path)
        else:
            final_path = base_dir / f"{safe_final_name}.mp3"
            conversion_success = convert_to_mp3(raw_path, final_path, bitrate)
            if raw_path.exists():
                raw_path.unlink()
            if not conversion_success:
                return False

        # METADATA & COVER ART
        cover_path = None
        if thumbnail_url:
            cover_path = base_dir / f"cover_{video_id}.jpg"
            cover_path = download_thumbnail(thumbnail_url, cover_path)

        meta = {'title': title, 'artist': artist, 'album': album}
        embed_metadata(final_path, meta, cover_path)

        if cover_path and cover_path.exists():
            cover_path.unlink()

        return True

    except KeyboardInterrupt:
        print(f"\n  [*] Membersihkan sisa unduhan terinterupsi (ID: {video_id})...")
        
        for junk_file in base_dir.glob(f"*{video_id}*"):
            try:
                if junk_file.exists():
                    junk_file.unlink()
            except Exception:
                pass
                
        try:
            if track_index is not None:
                prefix = f"{track_index:02d} - "
                for broken_file in base_dir.iterdir():
                    if broken_file.name.startswith(prefix) and not broken_file.name.endswith('.jpg'):
                        print(f"  [*] Menghapus file terinterupsi: '{broken_file.name}'")
                        broken_file.unlink()
            elif final_path.exists():
                final_path.unlink()
        except Exception:
            pass

        raise KeyboardInterrupt

    except Exception as e:
        print(f"  [Runtime Error] Gagal memproses lagu: {e}")
        return False


def process_playlist(url: str, base_dir: Path, output_format: str, bitrate: Optional[int]) -> None:
    match = re.search(r"list=([A-Za-z0-9_-]+)", url)
    if not match:
        print("[Gagal] URL Playlist tidak valid.")
        return
    playlist_id = match.group(1)

    print("\n[*] Mengumpulkan link playlist...")
    try:
        ytm = YTMusic()
        playlist_data = ytm.get_playlist(playlistId=playlist_id, limit=None)
    except Exception as e:
        print(f"Gagal integrasi API: {e}")
        return

    playlist_name = sanitize_filename(playlist_data.get('title', 'playlist'))
    tracks = playlist_data.get('tracks', [])
    playlist_dir = base_dir / playlist_name
    ensure_dir(playlist_dir)

    print(f"\nTarget : {playlist_name}")
    print(f"Total  : {len(tracks)} lagu")
    print("-" * 50)

    existing_files = os.listdir(playlist_dir)
    success_count = 0
    failed_songs = []

    for index, track in enumerate(tracks, start=1):
        if not track or not track.get('videoId'):
            failed_songs.append(f"Track {index}: Data Kosong/Terhapus")
            continue

        video_id = track['videoId']
        raw_title = track.get('title', 'Unknown Track')
        artists = track.get('artists', [])
        uploader = ", ".join([a.get('name', '') for a in artists if a.get('name')])
        clean_title = clean_track_title(raw_title)

        prefix = f"{index:02d} - "
        already_exists = False
        existing_filename = ""

        for file_name in existing_files:
            if file_name.startswith(prefix) and not file_name.endswith('.jpg'):
                if output_format == 'mp3' and file_name.endswith('.mp3'):
                    already_exists = True
                    existing_filename = file_name
                    break
                elif output_format == 'original' and not file_name.endswith('.mp3'):
                    already_exists = True
                    existing_filename = file_name
                    break

        if already_exists:
            print(f"[{index}/{len(tracks)}] [Skip] '{existing_filename}' terdeteksi aman.")
            success_count += 1
            continue

        video_url = f"https://music.youtube.com/watch?v={video_id}"
        print(f"\n[{index}/{len(tracks)}] Memproses direct link...")
        
        if process_entry(video_url, playlist_dir, output_format, bitrate, track_index=index):
            success_count += 1
        else:
            failed_songs.append(f"Track {index}: {uploader} - {clean_title} (ID: {video_id})")

    print(f"\nSelesai: Berhasil memproses {success_count} dari {len(tracks)} lagu.")
    if failed_songs:
        log_path = base_dir / "gagal_download.txt"
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("Daftar Gagal:\n" + "\n".join(failed_songs))
        print(f"Log kegagalan ditulis ke: {log_path.resolve()}")


def main() -> None:
    if not shutil.which('ffmpeg'):
        print("Error: FFmpeg tidak terdeteksi pada sistem.")
        sys.exit(1)

    check_cookies_validity()

    url = input("Enter YouTube Music URL: ").strip()
    if not url:
        return

    output_format, bitrate = select_quality()
    downloads_root = ensure_dir(Path('downloads'))

    print("\nMemulai analisa URL...")
    
    init_opts = get_base_ydl_opts()
    init_opts.update({
        'ignoreerrors': True,
        'extract_flat': True
    })
    
    try:
        with YoutubeDL(init_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except (Exception, KeyboardInterrupt):
        raise KeyboardInterrupt

    if not info:
        print("[Gagal] Tidak dapat mengekstrak data dari URL.")
        sys.exit(1)

    if is_playlist(info):
        process_playlist(url, downloads_root, output_format, bitrate)
    else:
        process_entry(url, downloads_root, output_format, bitrate)


def is_playlist(info: dict) -> bool:
    return info.get('_type') == 'playlist' or 'entries' in info


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Proses dibatalkan oleh pengguna (Ctrl+C).")
        print("[*] Menghentikan sisa proses skrip.")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)