import json

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

# Maxsus nomlar uchun rasmlar
SPECIFIC_IMAGES = {
    "Лағмон": "https://images.unsplash.com/photo-1552611052-33e04de081de?auto=format&fit=crop&w=500&q=80",
    "Ош": "https://images.unsplash.com/photo-1627308595229-7830f5c90656?auto=format&fit=crop&w=500&q=80",
    "Гриль": "https://images.unsplash.com/photo-1598514982205-f36b96d1e8d4?auto=format&fit=crop&w=500&q=80",
    "Товуқ": "https://images.unsplash.com/photo-1598514982205-f36b96d1e8d4?auto=format&fit=crop&w=500&q=80",
    "Манти": "https://images.unsplash.com/photo-1496116218417-1a781b1c416c?auto=format&fit=crop&w=500&q=80",
    "Шашлик": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=500&q=80"
}

def get_image(name, category):
    for key, img in SPECIFIC_IMAGES.items():
        if key.lower() in name.lower():
            return img
    return IMAGES.get(category, IMAGES["DEFAULT"])

def update_images():
    print("Rasmlar o'zgartirilmoqda...")
    
    # Update products.json
    try:
        with open('products.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for p in data.get('products', []):
            p['image'] = get_image(p.get('name', ''), p.get('category', ''))
            
        with open('products.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print("✅ products.json muvaffaqiyatli yangilandi.")
    except Exception as e:
        print(f"❌ products.json da xatolik: {e}")

    # Update database_state.json
    try:
        with open('database_state.json', 'r', encoding='utf-8') as f:
            db_data = json.load(f)
            
        for p in db_data.get('products', []):
            p['image'] = get_image(p.get('name', ''), p.get('category', ''))
            
        with open('database_state.json', 'w', encoding='utf-8') as f:
            json.dump(db_data, f, ensure_ascii=False, indent=4)
        print("✅ database_state.json muvaffaqiyatli yangilandi.")
    except Exception as e:
        print(f"❌ database_state.json da xatolik: {e}")

if __name__ == '__main__':
    update_images()
    print("🎉 Barcha maxsulotlarga internetdan chiroyli rasmlar biriktirildi!")
