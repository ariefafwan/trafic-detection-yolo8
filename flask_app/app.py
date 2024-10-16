from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from config import Config
from werkzeug.utils import secure_filename
from ultralytics import YOLO
import cv2
import numpy as np
import shutil
import time

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

# model database hasil deteksi YOLO
class DetectionResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    upload_datetime = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(50), nullable=False)
    mean_motorcycle = db.Column(db.Float, nullable=False)
    mean_car = db.Column(db.Float, nullable=False)
    mean_total_objects_in_box = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<DetectionResult {self.id} - {self.upload_datetime}>'

# inisiasi model YOLO
yolo_model = YOLO('./runs/detect/train7/weights/best.pt')
VALID_LOCATIONS = ["Pasar Banyumanik", "Kali Banteng", "Tugu Muda 3"]

# folder upload
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # dapetin data dari form
        video = request.files.get('video')
        date = request.form.get('date')
        time_input = request.form.get('time')
        location = request.form.get('location')

        # validasi
        if not video:
            flash('Tidak ada file video yang diunggah.', 'danger')
            return redirect(request.url)
        
        if not date:
            flash('Harap Masukkan Tanggal.', 'danger')
            return redirect(request.url)
        
        if not date:
            flash('Harap Masukkan Waktu.', 'danger')
            return redirect(request.url)
        
        if location not in VALID_LOCATIONS:
            flash('Lokasi yang dipilih tidak valid.', 'danger')
            return redirect(request.url)

        if video and allowed_file(video.filename):
            # inisiasi nama file
            filename = secure_filename(video.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # simpen video untuk diproses sesuai nama
            video.save(filepath)

            # gabungin tanggal dan waktu menjadi objek datetime
            try:
                datetime_str = f"{date} {time_input}"
                upload_datetime = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            except ValueError:
                flash('Format tanggal atau waktu tidak valid.', 'danger')
                os.remove(filepath)  # hapus file td
                return redirect(request.url)

            # deteksi YOLO
            try:
                detection_result = run_yolo_detection(filepath, location)
            except Exception as e:
                flash(f'Error saat menjalankan deteksi YOLO: {e}', 'danger')
                os.remove(filepath)  # hapus file di folder upload
                return redirect(request.url)

            # simpen hasil deteksi ke database
            new_result = DetectionResult(
                upload_datetime=upload_datetime,
                location=location,
                mean_motorcycle=detection_result['mean_motorcycle'],
                mean_car=detection_result['mean_car'],
                mean_total_objects_in_box=detection_result['mean_total_objects_in_box']
            )
            try:
                db.session.add(new_result)
                db.session.commit()
                flash('Berhasil Menambahkan Ke Tren Data!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error saat menyimpan hasil ke database: {e}', 'danger')
            finally:
                # hapus file video setelah diproses
                os.remove(filepath)

            return redirect(url_for('index'))
        else:
            flash('File yang diunggah bukan video yang valid.', 'danger')
            return redirect(request.url)

    # query tabel hasil deteksi terakhir
    results = DetectionResult.query.order_by(DetectionResult.upload_datetime.desc()).limit(10).all()
    return render_template('index.html', results=results)

@app.route('/trends', methods=['GET', 'POST'])
def trends():
    # all lokasi
    locations = db.session.query(DetectionResult.location).distinct().all()
    locations = [loc[0] for loc in locations]

    # filter lokasi
    selected_location = request.args.get('location')

    if selected_location:
        # filter lokasi yang dipilih
        results = DetectionResult.query.filter_by(location=selected_location).order_by(DetectionResult.upload_datetime).all()
    else:
        # kalau tidak ada lokasi yang dipilih, tampilkan semua
        results = DetectionResult.query.order_by(DetectionResult.upload_datetime).all()

    # data untuk Chart.js
    labels = [result.upload_datetime.strftime('%Y-%m-%d %H:%M') for result in results]
    mean_motorcycle = [result.mean_motorcycle for result in results]
    mean_car = [result.mean_car for result in results]
    mean_total_objects_in_box = [result.mean_total_objects_in_box for result in results]

    return render_template('trends.html', labels=labels, mean_motorcycle=mean_motorcycle,
                           mean_car=mean_car, mean_total_objects_in_box=mean_total_objects_in_box,
                           locations=locations, selected_location=selected_location)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def run_yolo_detection(video_path, location):
    """
    Ini Sesuai yang kita bikin ya gaes, cuman aku apus yang tulisan-tulisan sama garis-garis box aja aja.
    """
    # baca video
    cap = cv2.VideoCapture(video_path)

    # dapetin ukuran frame dan frame rate dari video
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # tentuin koordinat untuk garis miring (koordinat titik) sesuai lokasi, ini koordinatnya aku ambil dari yang kalian bikin jugak
    if location == 'Pasar Banyumanik':
        p1 = (800, 100)  # Titik kiri atas
        p2 = (940, 100)  # Titik kanan atas
        p3 = (950, 340)  # Titik kanan bawah
        p4 = (650, 300)  # Titik kiri bawah
    elif location == 'Tugu Muda 3':
        p1 = (280, 200)  # Titik kiri atas
        p2 = (430, 190)  # Titik kanan atas
        p3 = (630, 510)  # Titik kanan bawah
        p4 = (290, 550)  # Titik kiri bawah
    elif location == 'Kali Banteng':
        p1 = (20, 150)  # Titik kiri atas
        p2 = (430, 160) # Titik kanan atas
        p3 = (520, 360)  # Titik kanan bawah
        p4 = (170, 370)  # Titik kiri bawah

    # mulai pengukuran waktu
    prev_time = 0
    new_fps = fps  # Target FPS yang lebih tinggi
    array_motor = []
    array_mobil = []
    array_total_objects_in_box = []

    # iterasiin setiap frame dari video
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break  # kalau udah tidak ada frame lagi, keluar dari loop

        # ukur waktu saat ini
        current_time = time.time()

        # cek apakah frame cukup cepat untuk di-update berdasarkan target FPS
        if (current_time - prev_time) >= 1./new_fps:
            # jalanin deteksi objek pada setiap frame
            results = yolo_model.predict(frame, device='mps')

            # hitung total objek yang terdeteksi dan objek yang masuk kotak deteksi
            total_objects = 0
            objects_in_box = 0
            class_counts = {}
            class_counts_in_box = {}

            # proses setiap hasil dalam list
            for result in results:
                # dapetin jumlah objek yang terdeteksi dari jumlah bounding boxes
                total_objects += len(result.boxes)

                # looping untuk setiap bounding box yang terdeteksi
                for box in result.boxes:
                    # dapetin class index (label) dari hasil deteksi
                    class_id = int(box.cls[0])
                    class_name = yolo_model.names[class_id]  # Nama kelas dari ID

                    # hitung jumlah per kelas
                    if class_name in class_counts:
                        class_counts[class_name] += 1
                    else:
                        class_counts[class_name] = 1

                    # dapetin koordinat bounding box (xmin, ymin, xmax, ymax)
                    xmin, ymin, xmax, ymax = box.xyxy[0]

                    # hitung koordinat tengah dari bounding box
                    center_x = int((xmin + xmax) / 2)
                    center_y = int((ymin + ymax) / 2)

                    # periksa apakah titik pusat berada di dalam kotak deteksi
                    if p1[0] <= center_x <= p3[0] and p1[1] <= center_y <= p3[1]:
                        objects_in_box += 1  # Tambah hitungan objek yang masuk kotak

                        # hitung jumlah objek per kelas dalam kotak deteksi
                        if class_name in class_counts_in_box:
                            class_counts_in_box[class_name] += 1
                        else:
                            class_counts_in_box[class_name] = 1

            array_total_objects_in_box.append(objects_in_box)

            # kumpulin data untuk kendaraan
            if 'Motorcycle' in class_counts_in_box:
                array_motor.append(class_counts_in_box['Motorcycle'])
            else:
                array_motor.append(0)

            if 'Car' in class_counts_in_box:
                array_mobil.append(class_counts_in_box['Car'])
            else:
                array_mobil.append(0)

            # update waktu terakhir frame yang diproses
            prev_time = current_time

    # tutup video
    cap.release()
    cv2.destroyAllWindows()

    # Analisis ya GAES
    data = list(zip(array_motor, array_mobil))
    total_motorcycle = sum(m for m, c in data)
    total_car = sum(c for m, c in data)
    count = len(data)

    if count > 0:
        mean_motorcycle = total_motorcycle / count
        mean_car = total_car / count
    else:
        mean_motorcycle = 0
        mean_car = 0

    mean_total_objects_in_box = np.mean(array_total_objects_in_box) if array_total_objects_in_box else 0

    # ruturn hasil
    return {
        'mean_motorcycle': round(mean_motorcycle, 2),
        'mean_car': round(mean_car, 2),
        'mean_total_objects_in_box': round(mean_total_objects_in_box, 2)
    }

def move_file(source_file, destination_folder):
    # cek apakah file sumber ada
    if not os.path.exists(source_file):
        print(f"File '{source_file}' tidak ditemukan.")
        return

    # cek apakah folder tujuan ada, kalau tidak, buat folder
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
        print(f"Folder '{destination_folder}' telah dibuat.")

    # dapetin nama file dari path
    file_name = os.path.basename(source_file)
    base_name, extension = os.path.splitext(file_name)

    # tentuin path lengkap untuk file tujuan
    destination_file = os.path.join(destination_folder, file_name)

    # kalau file sudah ada, tambahkan angka ke nama file
    counter = 1
    while os.path.exists(destination_file):
        destination_file = os.path.join(destination_folder, f"{base_name}{counter}{extension}")
        counter += 1

    # pindahin file
    shutil.move(source_file, destination_file)

if __name__ == '__main__':
    # buat tabel jika belum ada dan jalanin
    with app.app_context():
        db.create_all()
    app.run(debug=True)