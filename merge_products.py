import json

def merge():
    with open('products.json', 'r', encoding='utf-8') as f:
        products_data = json.load(f)
        
    with open('database_state.json', 'r', encoding='utf-8') as f:
        db_data = json.load(f)
        
    db_data['products'] = products_data.get('products', [])
    db_data['categories'] = products_data.get('categories', [])
    
    with open('database_state.json', 'w', encoding='utf-8') as f:
        json.dump(db_data, f, ensure_ascii=False, indent=4)
        
    print("Merged products.json into database_state.json")

if __name__ == '__main__':
    merge()
