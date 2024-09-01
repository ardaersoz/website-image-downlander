import tkinter as tk
from tkinter import messagebox, filedialog
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote
import base64
import re
from PIL import Image
from io import BytesIO
import os
import threading

# Global değişkenler
output_folder = ""

# Geçersiz dosya karakterlerini temizleme fonksiyonu
def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename)

# Resim doğrulama fonksiyonu
def is_valid_image(img_data):
    try:
        with Image.open(BytesIO(img_data)) as img:
            img.verify()  # Dosyanın geçerli bir resim olup olmadığını kontrol et
            img = Image.open(BytesIO(img_data))
            if img.size[0] == 1 and img.size[1] == 1:
                return False
            return True
    except Exception as e:
        print(f"Image validation error: {e}")
        return False

# Resimleri indir ve kaydet
def download_images(keyword, url):
    global output_folder
    if not output_folder:
        messagebox.showerror("Error", "Output folder not selected.")
        return

    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        images = soup.find_all("img")

        for img in images:
            img_src = img.get('src')
            img_alt = img.get('alt', '')

            # Alt text'te anahtar kelime var mı
            if keyword.lower() in img_alt.lower():
                if img_src:
                    img_url = urljoin(url, img_src)
                    
                    if img_src.startswith("data:image"):  # Base64 formatında bir resim mi?
                        try:
                            header, encoded = img_src.split(",", 1)
                            file_extension = header.split(";")[0].split("/")[1]
                            
                            # Base64 string'e eksik padding'i ekle
                            missing_padding = len(encoded) % 4
                            if missing_padding:
                                encoded += '=' * (4 - missing_padding)
                            
                            img_data = base64.b64decode(encoded)
                            if is_valid_image(img_data):
                                img_name = sanitize_filename(img_alt) + ".png"
                                img_path = os.path.join(output_folder, img_name)
                                
                                # Base64 verisini png olarak kaydet
                                with open(img_path, 'wb') as handler:
                                    handler.write(img_data)
                                
                                print(f"Saved: {img_path}")
                            else:
                                print(f"Skipped invalid or 1x1 pixel image: {img_alt}")
                        
                        except Exception as e:
                            print(f"Error saving base64 image {img_name}: {e}")

                    else:  # Normal bir URL mi?
                        try:
                            img_data = requests.get(img_url).content
                            if is_valid_image(img_data):
                                img_name = sanitize_filename(img_alt) + ".png"
                                img_path = os.path.join(output_folder, img_name)
                                
                                # Resmi indir ve doğrula
                                with open(img_path, 'wb') as handler:
                                    handler.write(img_data)
                                
                                print(f"Saved: {img_path}")
                            else:
                                print(f"Skipped invalid or 1x1 pixel image from URL: {img_url}")
                        
                        except Exception as e:
                            print(f"Error saving image from URL {img_url}: {e}")
        
        messagebox.showinfo("Success", "Images have been downloaded successfully.")
    
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

# Arka plan iş parçacığı
def download_thread(keyword, url):
    status_label.config(text="Yükleniyor...")
    root.update_idletasks()  # GUI'nin güncellenmesini sağlar
    download_images(keyword, url)
    status_label.config(text="İşlem tamamlandı!")

# Klasör seçme fonksiyonu
def select_folder():
    global output_folder
    output_folder = filedialog.askdirectory()
    if output_folder:
        folder_label.config(text=f"Output Folder: {output_folder}")

# GUI için fonksiyon
def on_download_button_click():
    keyword = keyword_entry.get()
    url = url_entry.get()
    if keyword and url:
        if output_folder:
            threading.Thread(target=download_thread, args=(keyword, url)).start()
        else:
            messagebox.showwarning("Folder Error", "Please select an output folder.")
    else:
        messagebox.showwarning("Input Error", "Please provide both keyword and URL.")

# GUI oluşturma
root = tk.Tk()
root.title("Image Downloader")

# Siyah tema
root.configure(bg='black')

# Anahtar kelime girişi
tk.Label(root, text="Keyword:", bg='black', fg='white').grid(row=0, column=0, padx=10, pady=10)
keyword_entry = tk.Entry(root, width=50)
keyword_entry.grid(row=0, column=1, padx=10, pady=10)

# URL girişi
tk.Label(root, text="URL:", bg='black', fg='white').grid(row=1, column=0, padx=10, pady=10)
url_entry = tk.Entry(root, width=50)
url_entry.grid(row=1, column=1, padx=10, pady=10)

# Klasör seçme butonu
select_folder_button = tk.Button(root, text="Select Output Folder", command=select_folder, bg='gray', fg='white')
select_folder_button.grid(row=2, column=0, columnspan=2, pady=10)

# Çıktı klasörü etiketi
folder_label = tk.Label(root, text="Output Folder: Not selected", bg='black', fg='white')
folder_label.grid(row=3, column=0, columnspan=2, pady=10)

# İndirme butonu
download_button = tk.Button(root, text="Download Images", command=on_download_button_click, bg='gray', fg='white')
download_button.grid(row=4, column=0, columnspan=2, pady=20)

# Durum etiketi
status_label = tk.Label(root, text="", bg='black', fg='white')
status_label.grid(row=5, column=0, columnspan=2, pady=10)

root.mainloop()
