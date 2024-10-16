import cv2
from ultralytics import YOLO
import time
import numpy as np
import shutil
import os

# insiasi awal model YOLOv8
model = YOLO('./Predict/runs/detect/train7/weights/best.pt')

# path video yang akan diuji
video_path = './Predict/Video/Kali Banteng.mp4'
output_path = 'Kali Banteng.mp4'

# baca video
cap = cv2.VideoCapture(video_path)

# dapetin ukuran frame dan frame rate dari video
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

# bikin VideoWriter untuk menyimpan output video
out = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (frame_width, frame_height))

# nentuin koordinat untuk garis miring (koordinat titik)
p1 = (20, 150)  # Titik kiri atas
p2 = (430, 160) # Titik kanan atas
p3 = (520, 360)  # Titik kanan bawah
p4 = (170, 370)  # Titik kiri bawah

# pengukuran waktu
prev_time = 0
new_fps = fps
array_motor = []
array_mobil = []
array_total_objects_in_box = []
total_frame = []
total_motor = []
total_car = []

# iteraiin setiap frame dari video
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break  # kalau udah tidak ada frame lagi, keluar dari loop

    # ukur waktu sekarang
    current_time = time.time()
    
    # dicek apakah frame udah cepet untuk di-update berdasarkan target FPS
    if (current_time - prev_time) >= 1./new_fps:
        # kalau udah jalanin deteksi objek pada setiap frame
        results = model.predict(frame, device='mps')
        # hitung total objek yang terdeteksi dan objek yang masuk kotak deteksi
        total_objects = 0
        objects_in_box = 0
        class_counts = {}
        x = 0
        class_counts_in_box = {}  # nyimpen jumlah objek per kelas yang berada dalam kotak deteksi

        # proses setiap hasil dalam list
        for result in results:
            annotated_img = result.plot()

            # garis miring pada detection box
            cv2.line(annotated_img, p1, p2, (0, 255, 0), thickness=3)  # Garis atas
            cv2.line(annotated_img, p2, p3, (0, 255, 0), thickness=3)  # Garis kanan
            cv2.line(annotated_img, p3, p4, (0, 255, 0), thickness=3)  # Garis bawah
            cv2.line(annotated_img, p4, p1, (0, 255, 0), thickness=3)  # Garis kiri

            # dapetin jumlah objek yang terdeteksi dari jumlah bounding boxes
            total_objects += len(result.boxes)  # Jumlah bounding box = jumlah objek yang terdeteks
        # looping untuk setiap bounding box yang terdeteksi
        for box in result.boxes:
            # dapetin kelas (label) dari hasil deteksi
            class_id = int(box.cls[0])
            class_name = model.names[class_id]  # nama kelasnya dari id

            # dihitung jumlah per kelas
            if class_name in class_counts:
                class_counts[class_name] += 1
            else:
                class_counts[class_name] = 1

            # dapetin koordinat bounding box (xmin, ymin, xmax, ymax)
            xmin, ymin, xmax, ymax = box.xyxy[0]

            # hitung koordinat tengah dari bounding box
            center_x = int((xmin + xmax) / 2)
            center_y = int((ymin + ymax) / 2)

            # gambar titik di tengah bounding box
            cv2.circle(annotated_img, (center_x, center_y), radius=5, color=(0, 0, 255), thickness=-1)
            
            # diperiksa apakah titik pusat berada di dalam kotak deteksi
            if p1[0] <= center_x <= p3[0] and p1[1] <= center_y <= p3[1]:
                objects_in_box += 1  # kalau sudah hitungan objek yang masuk kotak

                # hitung jumlah objek per kelas dalam kotak deteksi
                if class_name in class_counts_in_box:
                    class_counts_in_box[class_name] += 1
                else:
                    class_counts_in_box[class_name] = 1
                
    # tambahin teks total objek dan jumlah per kelas di sudut kiri atas
    cv2.putText(annotated_img, f'Total objek: {total_objects}', (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                1, (0, 255, 0), 2, cv2.LINE_AA)

    # tampilin jumlah per kelas di sudut kiri atas gambar (di bawah total objek)
    y_offset = 80
    for class_name, count in class_counts.items():
        cv2.putText(annotated_img, f'{class_name}: {count}', (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 
                    1, (0, 255, 0), 2, cv2.LINE_AA)
        y_offset += 30  # geser teks ke bawah setiap kelas nambah

    # tambahin total objek dalam kotak dan jumlah per kelas dalam kotak di bawah teks jumlah objek berdasarkan kelas
    cv2.putText(annotated_img, f'Objek dalam kotak: {objects_in_box}', (20, y_offset + 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    array_total_objects_in_box.append(objects_in_box)
    # tampilin jumlah per kelas dalam kotak di bawah total objek dalam kotak (warna putih)
    y_offset_box = y_offset + 60  # Setel posisi Y di bawah total objek dalam kotak
    
    for class_name, count in class_counts_in_box.items():
        # hitung jumlah per kelas
        if class_name == "Motorcycle" in class_counts:
            class_counts[class_name] += 1
            array_motor.append(class_counts_in_box)
        else:
            class_counts[class_name] = 1
        if class_name == 'Car' in class_counts:
            class_counts[class_name] += 1
            array_mobil.append(class_counts_in_box)
        else:
            class_counts[class_name] = 1
        cv2.putText(annotated_img, f'{class_name} dalam kotak: {count}', (20, y_offset_box), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        y_offset_box += 30  # geser lagi teks ke bawah setiap kelas dalam kotak nambah


    # tulis semuanya ke output video
    out.write(annotated_img)

    # tampilin frame hasil deteksi di layar
    resized_frame = cv2.resize(annotated_img, (frame_width // 2, frame_height // 2))
    cv2.imshow("Deteksi YOLOv8", annotated_img)

    # update waktu terakhir frame diproses
    prev_time = current_time
    # Hentikan jika sudah mencapai waktu maksimum
    
    # untuk mudahin kalau gamau sampe selesai, tekan 'q' untuk keluar dari proses
    if cv2.waitKey(2) & 0xFF == ord('q'):
        break

# tutup video
cap.release()

np.set_printoptions(threshold=np.inf)

cv2.destroyAllWindows()

def move_file(source_file, destination_folder):
    # cek apakah file sumber ada
    if not os.path.exists(source_file):
        print(f"File '{source_file}' tidak ditemukan.")
        return

    # cek apakah folder tujuan ada, kalau engga, buat folder
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

source = output_path  # ganti dengan path file yang ingin dipindahin
destination = 'video_result/Kali Banteng'  # ganti dengan folder tujuan
move_file(source, destination)

# Analisisnya ya GAES
data = array_motor + array_mobil 
totaldata= {}
count_motor_mobil = len(data)

# jumlahin nilai dari setiap kelas
for obj in data:
    for key, value in obj.items():
        if key in totaldata:
            totaldata[key] += value
        else:
            totaldata[key] = value
total_car = 0
total_motorcycle = 0
count = len(data)

for obj in data:
    total_car += obj.get('Car', 0)
    total_motorcycle += obj.get('Motorcycle', 0)

mean = {key: value / count for key, value in totaldata.items()}
mean_car = round(total_car / count)
mean_motorcycle = round(total_motorcycle / count)

# print hasil, insyaaallah menang
print('rata-rataobjek dalam objek :', round(np.mean(np.array(array_total_objects_in_box))))
print('panjang array objek:', len(array_total_objects_in_box))
print('panjang array 1:', len(array_motor))
print('panjang array 2:', len(array_mobil))
print('rata-rata kendaraan:', mean)
print('rata-rata Motor  :', mean_motorcycle)
print('rata-rata Mobil:', mean_car)
