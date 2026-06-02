#!/usr/bin/env python3
"""
YouTube Music Downloader - Perfect Match (Clean Audio, 1:1 Cover & Reporting)
"""

import os
import sys
import json
import shutil
import subprocess
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from yt_dlp import YoutubeDL
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC, error as ID3Error

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False
    print("Peringatan: Modul 'Pillow' tidak ditemukan. Cover tidak akan di-crop 1:1. (Install dengan: pip install Pillow)")


def ensure_download_dir(base: Path) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    return base


def is_playlist(info: dict) -> bool:
    return info.get('_type') == 'playlist' or 'entries' in info


def get_playlist_name(info: dict) -> str:
    title = info.get('title', 'playlist')
    return ''.join(c for c in title if c not in r'<>:\"/\\|?*').strip()


def select_quality() -> Tuple[str, Optional[int]]:
    menu = """
Select output quality/format:
1) Original quality (no re‑encoding, keep source format)
2) MP3 – High quality (320 kbps)
3) MP3 – Medium quality (192 kbps)
4) MP3 – Low quality (128 kbps)
Enter choice [1-4]: """
    while True:
        choice = input(menu).strip()
        if choice == '1':
            return 'original', None
        elif choice == '2':
            return 'mp3', 320
        elif choice == '3':
            return 'mp3', 192
        elif choice == '4':
            return 'mp3', 128
        else:
            print("Invalid choice, please enter a number between 1 and 4.")


def download_thumbnail(url: str, dest: Path) -> Path:
    import urllib.request
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(url, str(dest))
        
        # CROP GAMBAR MENJADI 1:1 KOTAK JIKA PILLOW TERSEDIA
        if HAS_PILLOW:
            with Image.open(dest) as img:
                width, height = img.size
                if width != height:
                    # Ambil ukuran terkecil untuk membuat kotak sempurna
                    new_size = min(width, height)
                    left = (width - new_size) / 2
                    top = (height - new_size) / 2
                    right = (width + new_size) / 2
                    bottom = (height + new_size) / 2
                    
                    img = img.crop((left, top, right, bottom))
                    img.save(dest)
                    
        return dest
    except Exception as e:
        print(f"Warning: failed to download/crop thumbnail – {e}")
        return None


def embed_metadata(audio_path: Path, metadata: Dict[str, str], cover_path: Optional[Path] = None) -> None:
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
            pass


def run_ffmpeg(input_file: Path, output_file: Path, bitrate: int) -> bool:
    cmd = [
        'ffmpeg', '-y', '-i', str(input_file), '-vn',
        '-ab', f'{bitrate}k', '-ar', '44100', '-loglevel', 'error', str(output_file)
    ]
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e}")
        return False


def build_ydl_opts(output_template: str, download_best_audio: bool = True) -> dict:
    return {
        'format': 'bestaudio/best' if download_best_audio else 'bestaudio',
        'outtmpl': output_template,
        'quiet': False,
        'no_warnings': True,
        'ignoreerrors': True,
        'noprogress': False,
        'progress_hooks': [download_hook],
        'js_runtimes': {'node': {}},
    }


def download_hook(d):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate')
        if total:
            percent = d['downloaded_bytes'] / total * 100
            print(f"\rDownloading… {percent:5.1f}% ", end='', flush=True)
    elif d['status'] == 'finished':
        print("\rDownload completed.               ")


def clean_track_title(title: str) -> str:
    """Membersihkan judul dari embel-embel seperti 1080p, Official Video, dll."""
    # Hapus teks dalam kurung siku atau kurung biasa yang mengandung kata-kata tidak penting
    cleaned = re.sub(r'(?i)[\(\[].*?(official|music video|lyric|1080p|full hd|hq|audio|video|live).*?[\)\]]', '', title)
    return " ".join(cleaned.split())


def process_entry(url: str, base_dir: Path, output_format: str, bitrate: Optional[int], fallback_title: Optional[str] = None, track_index: Optional[int] = None) -> bool:
    # Ambil info awal
    ydl_opts_info = {'quiet': True, 'skip_download': True, 'js_runtimes': {'node': {}}}
    with YoutubeDL(ydl_opts_info) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except Exception:
            info = None

        if info is None and fallback_title:
            print(f"\n[Fallback] Link rusak. Mencari audio murni untuk: '{fallback_title}'...")
            search_opts = {'quiet': True, 'extract_flat': True, 'js_runtimes': {'node': {}}}
            try:
                with YoutubeDL(search_opts) as ydl_s:
                    search_res = ydl_s.extract_info(f"ytsearch1:{fallback_title} audio", download=False)
                    if search_res and search_res.get('entries'):
                        new_url = f"https://www.youtube.com/watch?v={search_res['entries'][0]['id']}"
                        info = ydl.extract_info(new_url, download=False)
                        url = new_url
            except Exception:
                print("Pencarian fallback gagal.")

        if info is None:
            return False

        # --- PERBAIKAN JUDUL (MENGUTAMAKAN METADATA YT MUSIC) ---
        # yt music biasanya menyimpan nama asli di variabel 'track'
        raw_title = info.get('track') or info.get('title', 'unknown')
        title = clean_track_title(raw_title)
        
        artist = info.get('artist') or info.get('uploader') or 'Unknown Artist'
        album = info.get('album') or ''
        thumbnail_url = info.get('thumbnail')
        video_id = info.get('id', 'unknown_id')

        # --- PENOMORAN NAMA FILE ---
        base_name = f"{artist} - {title}"
        if track_index is not None:
            base_name = f"{track_index:02d} - {base_name}"
            
        safe_final_name = ''.join(c for c in base_name if c not in r'<>:\"/\\|?*').strip()

        # [FITUR SKIP]
        if output_format == 'mp3':
            expected_file = base_dir / f"{safe_final_name}.mp3"
            if expected_file.exists():
                print(f"\n[Skip] '{expected_file.name}' sudah ada. Melewati download.")
                return True
        else:
            existing_files = [p for p in base_dir.glob(f"{safe_final_name}.*") if p.suffix.lower() != '.jpg']
            if existing_files:
                print(f"\n[Skip] '{existing_files[0].name}' sudah ada. Melewati download.")
                return True

        print(f"\n[Processing] {base_name}")
        
        # Download menggunakan ID sebagai nama sementara agar tidak terjadi bug saat ganti nama
        temp_template = str(base_dir / f"{video_id}.%(ext)s")
        ydl_opts = build_ydl_opts(temp_template)
        with YoutubeDL(ydl_opts) as ydl_dl:
            ydl_dl.download([url])

    # Mencari file sementara yang baru saja didownload menggunakan ID
    downloaded_files = list(base_dir.glob(f"{video_id}.*"))
    if not downloaded_files:
        return False
    
    raw_path = downloaded_files[0]
    ext = raw_path.suffix
    
    if output_format == 'original':
        final_path = base_dir / f"{safe_final_name}{ext}"
        if raw_path != final_path:
            if final_path.exists():
                final_path.unlink()
            raw_path.rename(final_path)
    else:
        final_path = base_dir / f"{safe_final_name}.mp3"
        if not run_ffmpeg(raw_path, final_path, bitrate):
            print("Conversion failed.")
            return False
        if raw_path != final_path and raw_path.exists():
            raw_path.unlink()

    cover_path = None
    if thumbnail_url:
        cover_path = base_dir / f"cover_{video_id}.jpg"
        download_thumbnail(thumbnail_url, cover_path)

    meta = {'title': title, 'artist': artist, 'album': album}
    embed_metadata(final_path, meta, cover_path)

    if cover_path and cover_path.exists():
        cover_path.unlink()

    print(f"Saved to: {final_path}")
    return True


def process_playlist(url: str, base_dir: Path, output_format: str, bitrate: Optional[int]) -> None:
    ydl_opts = {
        'quiet': True, 
        'skip_download': True, 
        'ignoreerrors': True, 
        'extract_flat': True,
        'js_runtimes': {'node': {}}
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if info is None:
            print("Failed to retrieve playlist information.")
            return
        playlist_name = get_playlist_name(info)
        entries = info.get('entries', [])

    playlist_dir = base_dir / playlist_name
    ensure_download_dir(playlist_dir)

    print(f"\nPlaylist: {playlist_name}")
    print(f"Total tracks found: {len(entries)}")
    print("--------------------------------------------------")

    success_count = 0
    failed_songs = []

    for index, entry in enumerate(entries, start=1):
        if entry is None:
            print(f"\n[{index}/{len(entries)}] Info track kosong. Melewati...")
            failed_songs.append(f"Track {index}: [Info Kosong/Dihapus Permanen]")
            continue
        
        video_id = entry.get('id')
        
        raw_title = entry.get('title', 'Unknown Track')
        raw_uploader = entry.get('uploader', '')
        fallback_query = f"{raw_title} {raw_uploader}".strip()
        
        if not video_id:
            failed_songs.append(f"Track {index}: {fallback_query} (Tidak ada Video ID)")
            continue
            
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        print(f"\n[{index}/{len(entries)}] Preparing track...")
        
        try:
            # Mengirimkan track_index ke dalam process_entry untuk penomoran
            success = process_entry(video_url, playlist_dir, output_format, bitrate, fallback_query, track_index=index)
            if success:
                success_count += 1
            else:
                failed_songs.append(f"Track {index}: {fallback_query} (Gagal Download)")
        except Exception as e:
            print(f"Error processing track {index}: {e}.")
            failed_songs.append(f"Track {index}: {fallback_query} (Error Skrip)")
            continue

    print("\n================================================--")
    print(f"HASIL AKHIR: Berhasil mengunduh/skip {success_count} dari {len(entries)} lagu.")
    
    if failed_songs:
        log_path = base_dir / "gagal_download.txt"
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("Daftar Lagu Gagal Download:\n")
            f.write("="*30 + "\n")
            f.write("\n".join(failed_songs))
            
        print(f"PERINGATAN: Ada {len(failed_songs)} lagu yang tidak tersedia di YouTube (dihapus/diblokir).")
        print(f"Cek file laporan di: {log_path.resolve()}")
    else:
        print("BERHASIL 100%! Tidak ada lagu yang gagal di-download.")
    print("================================================--")


def main() -> None:
    if not shutil.which('ffmpeg'):
        print("Error: ffmpeg is not installed or not in PATH.")
        sys.exit(1)

    url = input("Enter YouTube Music URL (track or playlist): ").strip()
    if not url:
        print("No URL provided.")
        sys.exit(1)

    output_format, bitrate = select_quality()
    downloads_root = Path('downloads')
    ensure_download_dir(downloads_root)

    print("\nAnalyzing URL, please wait...")
    
    try:
        with YoutubeDL({'quiet': True, 'skip_download': True, 'ignoreerrors': True, 'extract_flat': True, 'js_runtimes': {'node': {}}}) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        print(f"Failed to extract information: {e}")
        sys.exit(1)

    if info is None:
        print("Error: Could not retrieve any information from the provided URL.")
        sys.exit(1)

    if is_playlist(info):
        print("Detected playlist. Starting batch download...")
        process_playlist(url, downloads_root, output_format, bitrate)
    else:
        print("Detected single track. Starting download...")
        # Jika track satuan, kita bisa kirimkan None atau langsung angka 1 agar tidak acak-acakan.
        # Disini dibiarkan None agar track satuan tidak ada nomornya
        process_entry(url, downloads_root, output_format, bitrate)

    print("\nProcess finished! Check your 'downloads' folder.")


if __name__ == '__main__':
    main()