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

```text
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

```text
downloads/
```

---

# Cookies

Secara default program akan memeriksa keberadaan `cookies.txt`. Jika file tidak ditemukan atau tidak valid, Anda dapat memilih untuk tetap melanjutkan tanpa cookies.

## Menggunakan Cookies

### Keuntungan

- Mengurangi kemungkinan permintaan download dibatasi oleh YouTube.
- Dapat mengakses konten yang memerlukan login.
- Lebih stabil untuk proses download playlist berukuran besar.
- Membantu mengurangi munculnya verifikasi seperti CAPTCHA atau permintaan login.

### Kekurangan

- Perlu memperbarui cookies jika sudah kedaluwarsa.
- Jangan membagikan file `cookies.txt` karena berisi data sesi akun.

---

## Cara Mendapatkan `cookies.txt`

Cara paling mudah adalah menggunakan ekstensi browser yang dapat mengekspor cookies dalam format **Netscape**, yaitu format yang digunakan oleh `yt-dlp`.

### Google Chrome / Microsoft Edge / Brave

1. Login ke akun YouTube atau YouTube Music.
2. Buka **Chrome Web Store**.
3. Install ekstensi **Get cookies.txt LOCALLY**.
4. Buka salah satu halaman berikut:
   - https://music.youtube.com/
   - https://www.youtube.com/
5. Pastikan Anda sudah login.
6. Klik ikon ekstensi **Get cookies.txt LOCALLY**.
7. Pilih **Export**.
8. Simpan file dengan nama:

```text
cookies.txt
```

9. Letakkan file tersebut di folder project:

```text
.
├── main.py
├── cookies.txt
├── requirements.txt
└── downloads/
```

### Mozilla Firefox

1. Login ke YouTube atau YouTube Music.
2. Install ekstensi **Get cookies.txt LOCALLY** dari Firefox Add-ons.
3. Buka halaman YouTube yang sudah login.
4. Klik ikon ekstensi.
5. Pilih **Export**.
6. Simpan sebagai `cookies.txt`.
7. Pindahkan file ke folder project.

### Catatan

- Pastikan file menggunakan format **Netscape cookies**.
- Jangan mengubah isi file secara manual.
- Jangan membagikan file `cookies.txt` kepada siapa pun karena berisi data sesi login akun Anda.
- Jika proses download mulai gagal atau YouTube meminta login kembali, buat ulang file `cookies.txt`.

---

## Tanpa Cookies

### Keuntungan

- Tidak memerlukan login atau file tambahan.
- Lebih sederhana untuk penggunaan umum.

### Kekurangan

- Beberapa video mungkin tidak dapat diakses.
- Lebih berisiko terkena pembatasan (rate limit) dari YouTube.
- Pada kondisi tertentu YouTube dapat meminta verifikasi sehingga download gagal.

---

# Output

Untuk playlist, struktur hasil akan seperti berikut:

```text
downloads/
└── Nama Playlist/
    ├── 01 - Artist - Title.mp3
    ├── 02 - Artist - Title.mp3
    └── ...
```

Jika ada lagu yang gagal diunduh, daftar akan disimpan pada:

```text
downloads/
└── gagal_download.txt
```

---

## License

Project ini dibuat untuk penggunaan pribadi dan tujuan pembelajaran.

Pastikan penggunaan aplikasi ini mematuhi Ketentuan Layanan YouTube serta menghormati hak cipta dari setiap konten yang diunduh. Pemilik proyek tidak bertanggung jawab atas penyalahgunaan aplikasi ini.
