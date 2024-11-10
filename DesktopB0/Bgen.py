import os
import tkinter as tk
from tkinter import messagebox, Toplevel
from tkinter import PhotoImage
import requests
import json
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageTk
from io import BytesIO

# สร้างโฟลเดอร์ "Barcode" หากยังไม่มี
barcode_folder = "Barcode"
if not os.path.exists(barcode_folder):
    os.makedirs(barcode_folder)

# สร้างหน้าต่างหลัก
root = tk.Tk()
root.title("Bscan Desktop App")  # ตั้งชื่อหน้าต่าง
root.geometry("400x450")  # กำหนดขนาดหน้าต่าง
root.config(bg="#A7D8FF")  # ตั้งพื้นหลังเป็นสีฟ้าอ่อน

# ตัวแปรเก็บแถวที่ถูกเลือกก่อนหน้านี้
previous_selected_row = None

# ฟังก์ชันสร้าง Barcode โดยการรวมข้อมูลรหัสสินค้า ราคา และวันหมดอายุ
def generate_barcode(product_id, price, expiry_date):
    # สร้างรหัส Barcode จากการรวมข้อมูล
    barcode_data = f"{product_id}-{price}-{expiry_date}"
    return barcode_data

def create_barcode_image(product_id, product_name, barcode_data):
    # สร้าง Barcode จากข้อมูลที่ได้
    code128 = barcode.get_barcode_class('code128')
    barcode_instance = code128(barcode_data, writer=ImageWriter())
    
    # ตั้งชื่อไฟล์เป็น "รหัสสินค้า-ชื่อสินค้า.png"
    filename = f"{product_id}-{product_name}.png"
    file_path = os.path.join(barcode_folder, filename)

    # ตรวจสอบว่าไฟล์มีอยู่แล้วหรือไม่
    if os.path.exists(file_path):
        # ถ้ามีให้เปิดไฟล์ที่มีอยู่แล้ว
        image = Image.open(file_path)
    else:
        # ถ้าไม่มี ให้สร้างใหม่
        # สร้าง Barcode image ในหน่วยความจำ
        buffer = BytesIO()
        barcode_instance.write(buffer)
        buffer.seek(0)  # เลื่อน pointer ไปที่ตำแหน่งเริ่มต้นของ buffer
        
        # เปิด Barcode image จากหน่วยความจำ
        image = Image.open(buffer)
        
        # บันทึกไฟล์ Barcode
        image.save(file_path)
    
    return image

def open_list_window():
    # สร้างหน้าต่างใหม่ (Toplevel) เพื่อแสดงข้อมูลจาก Google Sheets
    list_window = Toplevel()
    list_window.title("List of Products")
    list_window.geometry("1000x1000")
    
    # ดึงข้อมูลจาก Google Sheets
    url = "https://script.google.com/macros/s/YOR_ID/exec"
    response = requests.get(url)
    
    # ตรวจสอบว่าได้รับการตอบกลับและสถานะคือ 200 หรือไม่
    if response.status_code == 200:
        try:
            data = response.json().get('data', [])
            
            if data:  # ตรวจสอบว่ามีข้อมูลหรือไม่
                # สร้างตารางในหน้าต่างใหม่
                labels = []  # สร้างตัวแปรเก็บ Label สำหรับแต่ละแถว
                for i, row in enumerate(data):
                    row_labels = []  # เก็บ Labels ของแถว
                    for j, value in enumerate(row):
                        # ถ้าเป็นแถวแรก (i == 0) จะเปลี่ยนสีพื้นหลังเป็นสีเขียวอ่อน
                        bg_color = "DarkSeaGreen1" if i == 0 else "white"
                        
                        label = tk.Label(list_window, text=value, relief="solid", width=20, height=2, bg=bg_color)
                        label.grid(row=i, column=j)
                        row_labels.append(label)  # เก็บ Label ของแถวนี้
                        
                        # ถ้าเป็นแถวที่ไม่ใช่แถวแรก (i > 0) ให้เพิ่มฟังก์ชันคลิกที่แถว
                        if i > 0:
                            label.bind("<Button-1>", lambda event, row_labels=row_labels: on_item_click(event, row_labels, list_window))
                            label.bind("<Double-1>", lambda event, barcode_value=row[4], product_id=row[0], product_name=row[1]: on_item_double_click(event, barcode_value, product_id, product_name))  # Double Click บนแถวที่มี Barcode
                list_window.row_labels = labels  # เก็บไว้ใน list_window สำหรับการใช้ภายใน
            else:
                messagebox.showinfo("No Data", "ไม่มีข้อมูลในตาราง")
        except requests.exceptions.JSONDecodeError:
            messagebox.showerror("Error", "ไม่สามารถแปลงข้อมูลเป็น JSON ได้: " + response.text)
    else:
        messagebox.showerror("Error", f"ไม่สามารถเชื่อมต่อกับ Google Sheets ได้ (สถานะ: {response.status_code})")

# ฟังก์ชันเมื่อคลิกที่แถวในตาราง
def on_item_click(event, row_labels, list_window):
    global previous_selected_row

    # ถ้ามีแถวที่ถูกเลือกอยู่แล้ว (previous_selected_row) ให้ยกเลิกการไฮไลต์
    if previous_selected_row:
        for label in previous_selected_row:
            label.config(bg="white")
    
    # ไฮไลต์แถวใหม่
    for label in row_labels:
        label.config(bg="light yellow")
    
    # เก็บแถวที่เลือกไว้
    previous_selected_row = row_labels

# ฟังก์ชันเมื่อ Double Click ที่แถวที่มี Barcode
def on_item_double_click(event, barcode_value, product_id, product_name):
    # สร้าง Barcode Image จากข้อมูล
    image = create_barcode_image(product_id, product_name, barcode_value)
    
    # สร้าง Popup window สำหรับแสดงภาพ
    popup = Toplevel()
    popup.title("Barcode Image")
    
    # เปลี่ยนภาพที่สร้างเป็น PhotoImage สำหรับแสดงใน Tkinter
    photo = ImageTk.PhotoImage(image)
    
    label_image = tk.Label(popup, image=photo)
    label_image.photo = photo  # ต้องเก็บอ้างอิงไปยัง image object
    label_image.pack()
    
    # แสดงหน้าต่าง Popup
    popup.mainloop()

# ฟังก์ชันสำหรับปุ่ม Save
def save_data():
    # รับข้อมูลจากฟอร์ม (ตัวอย่างค่า)
    product_id = entry_product_id.get()
    product_name = entry_product_name.get()
    price = entry_price.get()
    expiry_date = entry_expiry_date.get()
    
    # สร้าง Barcode จากข้อมูล
    barcode = generate_barcode(product_id, price, expiry_date)  # สร้าง Barcode โดยใช้ฟังก์ชันนี้
    print(barcode)
    # สร้างข้อมูลเป็น dictionary
    data = {
        "productId": product_id,
        "productName": product_name,
        "price": price,
        "expiryDate": expiry_date,
        "barcode": barcode  # เพิ่ม Barcode
    }
    
    # URL ของ Web App ที่ได้จาก Google Apps Script
    url = "https://script.google.com/macros/s/YOR_ID/exec"
    
    try:
        # ส่งข้อมูลไปยัง Google Apps Script ด้วย POST request
        response = requests.post(url, json=data)

        # ตรวจสอบว่า HTTP status code เป็น 200 (OK) หรือไม่
        if response.status_code == 200:
            try:
                # รับผลลัพธ์จาก Google Apps Script
                result = response.json()
                message = result.get('message', 'ไม่ทราบข้อผิดพลาด')
                print(message)  # แสดงข้อความใน console (หรือทำอย่างอื่นตามต้องการ)
                messagebox.showinfo("!", message)  # แสดงข้อความใน popup
            except requests.exceptions.JSONDecodeError:
                print("Error: Response is not in valid JSON format")
                print("Response text: ", response.text)
        else:
            print(f"Error: {response.status_code}")
            print(response.text)  # แสดงข้อความจาก response ที่ได้รับ

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

# สร้างคำอธิบายและช่องป้อนข้อความ
label_product_id = tk.Label(root, text="รหัสสินค้า:", bg="#A7D8FF", font=("Arial", 12))
label_product_id.pack(pady=10)  # เพิ่มช่องว่าง

entry_product_id = tk.Entry(root, font=("Arial", 12))
entry_product_id.pack(pady=5)

label_product_name = tk.Label(root, text="ชื่อสินค้า:", bg="#A7D8FF", font=("Arial", 12))
label_product_name.pack(pady=10)

entry_product_name = tk.Entry(root, font=("Arial", 12))
entry_product_name.pack(pady=5)

label_price = tk.Label(root, text="ราคา:", bg="#A7D8FF", font=("Arial", 12))
label_price.pack(pady=10)

entry_price = tk.Entry(root, font=("Arial", 12))
entry_price.pack(pady=5)

label_expiry_date = tk.Label(root, text="วันหมดอายุ:", bg="#A7D8FF", font=("Arial", 12))
label_expiry_date.pack(pady=10)

entry_expiry_date = tk.Entry(root, font=("Arial", 12))
entry_expiry_date.pack(pady=5)

save_button = tk.Button(root, text="บันทึกข้อมูล", command=save_data, font=("Arial", 12), bg="lightgreen")
save_button.pack(pady=20)

list_button = tk.Button(root, text="เปิดรายการสินค้า", command=open_list_window, font=("Arial", 12), bg="lightblue")
list_button.pack(pady=10)

root.mainloop()
