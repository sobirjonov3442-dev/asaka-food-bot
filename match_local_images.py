import json
import os
import re

def normalize_name(name):
    # Harflarni kichik qilib, bo'shliqlarni olib tashlaymiz
    name = name.lower()
    name = re.sub(r'[^a-z0-9а-яёўқғҳ]', '', name)
    return name

def match_images():
    img_dir = "images"
    if not os.path.exists(img_dir):
        print("❌ 'images' papkasi topilmadi!")
        return

    # Papkadagi barcha rasmlarni o'qiymiz
    image_files = [f for f in os.listdir(img_dir) if f.endswith(('.jpg', '.jpeg', '.png', '.webp'))]
    
    if not image_files:
        print("❌ 'images' papkasi ichida rasmlar yo'q!")
        return

    # Rasm nomlarini normallashtirib lug'at (dictionary) ga joylaymiz
    # Masalan: "lagmon.jpg" -> {"lagmon": "lagmon.jpg"}
    images_map = {}
    for img in image_files:
        base_name = os.path.splitext(img)[0]
        norm_name = normalize_name(base_name)
        images_map[norm_name] = img

    print(f"Topilgan rasmlar ({len(image_files)} ta): {list(images_map.keys())}")

    def process_data(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            updated_count = 0
            for p in data.get('products', []):
                prod_name = normalize_name(p.get('name', ''))
                
                # Mos rasm bormi qidiramiz
                matched_img = None
                
                # 1. Aniq mos kelishi
                if prod_name in images_map:
                    matched_img = images_map[prod_name]
                else:
                    # 2. Qisman mos kelishi (masalan, maxsulot "Qovurma lagmon", rasm "lagmon.jpg")
                    for img_name, img_file in images_map.items():
                        if img_name in prod_name or prod_name in img_name:
                            matched_img = img_file
                            break
                            
                if matched_img:
                    p['image'] = f"images/{matched_img}"
                    updated_count += 1

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                
            print(f"✅ {file_path} da {updated_count} ta maxsulotga rasm ulandi!")
        except Exception as e:
            print(f"❌ {file_path} da xatolik: {e}")

    process_data('products.json')
    process_data('database_state.json')

if __name__ == '__main__':
    match_images()
