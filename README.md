# YouTube Music Downloader

Python script untuk mengunduh lagu atau playlist dari YouTube Music dengan dukungan metadata, cover art, dan konversi MP3 menggunakan FFmpeg.

## Fitur

- Download single track dan playlist YouTube Music
- Download langsung dari playlist tanpa pencarian ulang
- Metadata ID3 otomatis (Title, Artist, Album)
- Embed cover art ke file MP3
- Pilihan kualitas:
  - Original
  - MP3 320 kbps
  - MP3 192 kbps
  - MP3 128 kbps
- Skip lagu yang sudah ada berdasarkan urutan playlist
- Validasi cookies sebelum proses download
- Otomatis menggunakan FFmpeg dari `static-ffmpeg` jika tersedia

## Requirements

- Python 3.9 atau lebih baru

Install dependency:

```bash
pip install -r requirements.txt
```

## Dependencies

- yt-dlp
- ytmusicapi
- mutagen
- Pillow
- static-ffmpeg

## Struktur Proyek

```
.
├── main.py
├── requirements.txt
├── cookies.txt          # Opsional
└── downloads/
```

## Penggunaan

Jalankan program:

```bash
python main.py
```

Program akan meminta:

1. URL YouTube Music (lagu atau playlist)
2. Pilihan kualitas output

Hasil download akan disimpan di folder:

```
downloads/
```

## Cookies

Secara default program akan memeriksa keberadaan `cookies.txt`. Jika file tidak ditemukan atau tidak valid, Anda dapat memilih untuk tetap melanjutkan tanpa cookies.

### Menggunakan Cookies

Keuntungan:

- Mengurangi kemungkinan permintaan download dibatasi oleh YouTube.
- Dapat mengakses konten yang memerlukan login.
- Lebih stabil untuk proses download playlist berukuran besar.
- Membantu mengurangi munculnya verifikasi seperti CAPTCHA atau permintaan login.

Kekurangan:

- Perlu memperbarui cookies jika sudah kedaluwarsa.
- Jangan membagikan file `cookies.txt` karena berisi data sesi akun.

### Tanpa Cookies

Keuntungan:

- Tidak memerlukan login atau file tambahan.
- Lebih sederhana untuk penggunaan umum.

Kekurangan:

- Beberapa video mungkin tidak dapat diakses.
- Lebih berisiko terkena pembatasan (rate limit) dari YouTube.
- Pada kondisi tertentu YouTube dapat meminta verifikasi sehingga download gagal.

## Output

Untuk playlist, struktur hasil akan seperti berikut:

```
downloads/
└── Nama Playlist/
    ├── 01 - Artist - Title.mp3
    ├── 02 - Artist - Title.mp3
    └── ...
```

Jika ada lagu yang gagal diunduh, daftar akan disimpan pada:

```
downloads/gagal_download.txt
```

## License

Project ini dibuat untuk penggunaan pribadi dan tujuan pembelajaran. Pastikan mematuhi ketentuan layanan YouTube dan hak cipta yang berlaku.
