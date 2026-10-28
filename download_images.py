import json
import os
import urllib.request
import re

# Rasmlar bazasi (kategoriyalar va nomlar bo'yicha)
IMAGES = {
    "СУЮҚ ОВҚАТЛАР": "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=500&q=80",
    "ҚЎЙИҚ ОВҚАТЛАР": "https://images.unsplash.com/photo-1600891964092-4316c288032e?auto=format&fit=crop&w=500&q=80",
    "АССОРТИМЕНТЛАР": "https://images.unsplash.com/photo-1496116218417-1a781b1c416c?auto=format&fit=crop&w=500&q=80",
    "СОМСАЛАР": "https://images.unsplash.com/photo-1626200419188-f14237c58850?auto=format&fit=crop&w=500&q=80",
    "САЛАТЛАР": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=500&q=80",
    "НОНЛАР": "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=500&q=80",
    "ИЧИМЛИКЛАР": "https://images.unsplash.com/photo-1556679343-c7306c1976bc?auto=format&fit=crop&w=500&q=80",
    "ШИРИНЛИКЛАР": "https://images.unsplash.com/photo-1528207776546-384cb1119b71?auto=format&fit=crop&w=500&q=80",
    "ШАШЛИКЛАР": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=500&q=80",
    "СУТ МАХСУЛОТЛАРИ": "https://images.unsplash.com/photo-1563636619-e9143da7973b?auto=format&fit=crop&w=500&q=80",
    "DEFAULT": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=500&q=80"
}

SPECIFIC_IMAGES = {
    "Лағмон": "https://images.unsplash.com/photo-1552611052-33e04de081de?auto=format&fit=crop&w=500&q=80",
    "Ош": "https://images.unsplash.com/photo-1627308595229-7830f5c90656?auto=format&fit=crop&w=500&q=80",
    "Гриль": "https://images.unsplash.com/photo-1598514982205-f36b96d1e8d4?auto=format&fit=crop&w=500&q=80",
    "Товуқ": "https://images.unsplash.com/photo-1598514982205-f36b96d1e8d4?auto=format&fit=crop&w=500&q=80",
    "Манти": "https://images.unsplash.com/photo-1496116218417-1a781b1c416c?auto=format&fit=crop&w=500&q=80",
    "Шашлик": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=500&q=80"
}

def get_image_url(name, category):
    for key, img in SPECIFIC_IMAGES.items():
        if key.lower() in name.lower():
            return img
    return IMAGES.get(category, IMAGES["DEFAULT"])

def download_and_update():
    img_dir = "images"
    os.makedirs(img_dir, exist_ok=True)
    
    print("🌐 Internetdan rasmlar yuklab olinmoqda va images papkasiga saqlanmoqda...")
    
    # Rasmlarni yuklab olib, maxalliy pathlarni saqlash
    url_to_local = {}

    def process_data(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for p in data.get('products', []):
                prod_name = p.get('name', 'Nomsiz')
                cat_name = p.get('category', 'Boshqa')
                url = get_image_url(prod_name, cat_name)
                
                # Fayl nomini chiroyli qilish (faqat harf va raqamlar)
                safe_name = re.sub(r'[^a-zA-Z0-9]', '_', prod_name.lower())
                safe_name = safe_name.strip('_') + ".jpg"
                local_path = f"{img_dir}/{safe_name}"
                
                if url not in url_to_local:
                    try:
                        print(f"📥 Yuklanmoqda: {prod_name} -> {local_path}")
                        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req) as response, open(local_path, 'wb') as out_file:
                            out_file.write(response.read())
                        url_to_local[url] = local_path
                    except Exception as e:
                        print(f"⚠️ {prod_name} rasmini yuklashda xatolik: {e}")
                        url_to_local[url] = url # Xato bo'lsa URL ni o'zini qoldiramiz
                        
                p['image'] = url_to_local[url]

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                
            print(f"✅ {file_path} muvaffaqiyatli yangilandi!")
        except Exception as e:
            print(f"❌ {file_path} da xatolik: {e}")

    process_data('products.json')
    process_data('database_state.json')

if __name__ == '__main__':
    download_and_update()
    print("🎉 Barcha internet rasmlari 'images' papkasiga yuklab olindi va bazaga ulandi!")
