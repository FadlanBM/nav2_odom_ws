# nav2_odom_ws

Paket ROS 2 untuk navigasi robot menggunakan Nav2 dengan strategi **Odometry-Only** (hanya menggunakan wheel odometry, tanpa LiDAR/SLAM).

## Fitur Utama
- **Navigasi Tanpa LiDAR:** Menggunakan frame `odom` sebagai referensi global.
- **Rolling Window Costmap:** Costmap selalu mengikuti posisi robot karena tidak ada peta statis.
- **Static Map-to-Odom TF:** Menyediakan transform statis `map -> odom` untuk memenuhi persyaratan Nav2.
- **Waypoint Navigation:** Skrip untuk menyimpan dan menjalankan navigasi berbasis titik (waypoints).
- **Simulasi Ignition Gazebo:** Konfigurasi siap pakai untuk simulasi.

## Persiapan
Pastikan Anda telah menginstal Nav2 dan dependensi terkait:
```bash
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup ros-humble-ros-gz
```

## Cara Menjalankan

### 1. Bangun Paket
```bash
colcon build --packages-select nav2_odom_ws
source install/setup.bash
```

### 2. Jalankan Simulasi
```bash
ros2 launch nav2_odom_ws launch_sim_ign.launch.py
```

### 3. Jalankan Navigasi
Di terminal baru:
```bash
ros2 launch nav2_odom_ws navigation_odom_only.launch.py use_sim_time:=true
```

### 4. Manajemen Waypoints

#### Menyimpan Waypoint (Save)
Gunakan skrip ini untuk merekam posisi robot saat ini. Gerakkan robot ke titik yang diinginkan terlebih dahulu (misalnya menggunakan teleop).
```bash
python3 src/nav2_odom_ws/scripts/save_waypoints.py
```
*   Tekan **Ctrl+C** untuk menangkap koordinat saat ini.
*   Masukkan nama waypoint saat diminta.
*   Pilih `y` jika ingin berpindah ke titik lain dan menyimpannya lagi.

#### Menjalankan Waypoint (Run)
Setelah waypoint tersimpan di `config/waypoints.yaml`, robot dapat dijalankan secara otomatis:

**Mode Otomatis (Tanpa Berhenti):**
```bash
python3 src/nav2_odom_ws/scripts/run_waypoints.py --auto
```

**Mode Loop (Kembali ke awal):**
```bash
python3 src/nav2_odom_ws/scripts/run_waypoints.py --auto --loop
```

**Mode Interaktif (Konfirmasi manual tiap titik):**
```bash
python3 src/nav2_odom_ws/scripts/run_waypoints.py
```

## Struktur Folder
- `config/`: Berisi parameter Nav2 (`nav2_params_odom_only.yaml`), RViz, dan bridge simulasi.
- `launch/`: File launch untuk simulasi dan navigasi.
- `scripts/`: Skrip Python untuk manajemen waypoints.
- `worlds/`: (Jika ada) File dunia simulasi.

## Catatan
Strategi navigasi ini sangat bergantung pada presisi odometry roda. Drift pada odometry akan mengakibatkan kesalahan posisi pada frame `map`.