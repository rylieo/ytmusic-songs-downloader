# YouTube Music Downloader - Cara Pakai

## Instalasi
1. **Python**: Pastikan Python 3.x terinstal di komputer Anda.
2. **Librari**: Instal paket yang dibutuhkan:
   ```bash
   pip install yt-dlp mutagen pillow
   ```
3. **FFmpeg**: Pastikan FFmpeg terinstal dan tersedia di PATH sistem Anda.  
   - Download: 
   ```bash
   winget install Gyan.FFmpeg
   ```

## Penggunaan
1. **Jalankan Skrip**:
   - Buka terminal atau CMD.
   - Jalankan skrip: `python main.py`
2. **Masukkan URL**:
   - Masukkan URL YouTube Music (track atau playlist).
3. **Pilih Kualitas**:
   - Pilih opsi:
     1. Kualitas asli (format asli)
     2. MP3 320 kbps
     3. MP3 192 kbps
     4. MP3 128 kbps
4. **Proses**:
   - Skrip akan mendownload dan menyimpan file di folder `downloads/`.
   - Jika ada file duplikat, skrip akan mengabaikan.

## Fitur
- **Download Playlist**: Mendownload semua lagu dalam playlist.
- **Metadata**: Menyisipkan judul, artis, dan album ke file audio.
- **Thumbnail**: Menggambarkan cover 1:1 (jika Pillow terinstal).
- **Anti-Duplikat**: Mengabaikan file yang sudah ada.
- **Laporan Gagal**: Menyimpan daftar lagu gagal di `gagal_download.txt`.

## Catatan
- Pastikan FFmpeg terinstal untuk konversi ke MP3.
- Jika Pillow tidak terinstal, cover tidak akan di-crop 1:1.
- File hasil disimpan di folder `downloads/`.

## Struktur Output
- File audio: `downloads/[nama_artis] - [judul].mp3` (atau format asli).
- Cover: `downloads/cover_[id_video].jpg` (jika ada).

## Lainnya
- Skrip otomatis mengatur nama file dan menghindari konflik.
- Jika ada masalah, cek file `gagal_download.txt` untuk detail.
