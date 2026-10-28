import json
import os
from datetime import datetime, timedelta

class Database:
    def __init__(self):
        self.db_file = "database_state.json"
        self.webapp_products_file = "products.json"
        self.load_data()

    def load_data(self):
        if os.path.exists(self.db_file):
            with open(self.db_file, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    self.users = data.get("users", {})
                    self.products = data.get("products", [])
                    self.orders = data.get("orders", [])
                    self.carts = data.get("carts", {})
                    self.admins = data.get("admins", [])
                    self.couriers = data.get("couriers", [])
                    self.admin_contact = data.get("admin_contact", {"name": "Fast Food Admin", "phone": "+998 90 123 45 67", "username": "@admin"})
                    self.categories = data.get("categories", [])
                    self.admin_accounts = data.get("admin_accounts", [{"login": "opetito321", "password": "opetittox555", "name": "Asosiy Admin", "is_superadmin": True}])
                    self.admin_sessions = data.get("admin_sessions", {})
                    self.companies = data.get("companies", [])
                    self.partner_requests = data.get("partner_requests", [])
                    self.promocodes = data.get("promocodes", {})
                    self.admin_location = data.get("admin_location", {"address": "Asaka shahar", "latitude": 40.6415, "longitude": 72.2392})
                except Exception:
                    self._init_default()
        else:
            self._init_default()

        # Eski admin_accounts ga is_superadmin field qo'shish (migratsiya)
        for acc in self.admin_accounts:
            if 'is_superadmin' not in acc:
                if acc.get('login') == 'opetito321':
                    acc['is_superadmin'] = True
                else:
                    acc['is_superadmin'] = False

        if not getattr(self, 'promocodes', None):
            self.promocodes = {
                "ASAKA": {
                    "code": "ASAKA",
                    "amount": 3000,
                    "max_uses": 500,
                    "used_by": [],
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
            }

        if not hasattr(self, 'partner_requests'):
            self.partner_requests = []

        for c in getattr(self, 'companies', []):
            if "category" not in c or not c.get("category"):
                c["category"] = "Fast-food / Kafe"
            if "address" not in c or not c.get("address"):
                c["address"] = "Asaka shahar, Markaz"
            if "latitude" not in c or c.get("latitude") is None:
                c["latitude"] = 40.6415
            if "longitude" not in c or c.get("longitude") is None:
                c["longitude"] = 72.2392

        self.save_data()
        self.export_webapp_products()

    def _init_default(self):
        self.users = {}
        self.products = []
        self.orders = []
        self.carts = {}
        self.admins = []
        self.couriers = []
        self.admin_contact = {"name": "Fast Food Admin", "phone": "+998 90 123 45 67", "username": "@admin"}
        self.categories = []
        self.admin_accounts = [{"login": "opetito321", "password": "opetittox555", "name": "Asosiy Admin", "is_superadmin": True}]
        self.admin_sessions = {}
        self.companies = []
        self.partner_requests = []
        self.promocodes = {
            "ASAKA": {
                "code": "ASAKA",
                "amount": 3000,
                "max_uses": 500,
                "used_by": [],
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
        }
        self.save_data()

    def save_data(self):
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump({
                "users": getattr(self, 'users', {}),
                "products": getattr(self, 'products', []),
                "orders": getattr(self, 'orders', []),
                "carts": getattr(self, 'carts', {}),
                "admins": getattr(self, 'admins', []),
                "couriers": getattr(self, 'couriers', []),
                "admin_contact": getattr(self, 'admin_contact', {"name": "Fast Food Admin", "phone": "+998 90 123 45 67", "username": "@admin"}),
                "categories": getattr(self, 'categories', []),
                "admin_accounts": getattr(self, 'admin_accounts', []),
                "admin_sessions": getattr(self, 'admin_sessions', {}),
                "companies": getattr(self, 'companies', []),
                "partner_requests": getattr(self, 'partner_requests', []),
                "promocodes": getattr(self, 'promocodes', {}),
                "admin_location": getattr(self, 'admin_location', {"address": "Asaka shahar", "latitude": 40.6415, "longitude": 72.2392})
            }, f, ensure_ascii=False, indent=2)

    def export_webapp_products(self):
        """Export all companies' products for WebApp"""
        # Global fallback (barcha kompaniyalar produktlari)
        all_products = [p for p in self.products if p.get('is_active', 1)]
        cats = getattr(self, 'categories', [])

        # Kompaniyalar ro'yxatini ham export qilamiz
        companies_export = []
        for c in self.companies:
            if c.get('is_frozen'): continue
            company_products = [p for p in c.get('products', []) if p.get('is_active', 1)]
            company_cats = c.get('categories', [])
            companies_export.append({
                "id": c['id'],
                "name": c['name'],
                "category": c.get('category', "Do'kon"),
                "address": c.get('address', "Asaka"),
                "categories": company_cats,
                "products": company_products
            })

        data_obj = {
            "categories": cats,
            "products": all_products,
            "companies": companies_export
        }

        dir_name = os.path.dirname(self.webapp_products_file)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        with open(self.webapp_products_file, 'w', encoding='utf-8') as f:
            json.dump(data_obj, f, ensure_ascii=False, indent=4)

    async def connect(self):
        print("JSON bazasi ishga tushdi")

    async def close(self):
        self.save_data()

    # ========================
    # COMPANY METHODS
    # ========================
    async def get_companies(self):
        return getattr(self, 'companies', [])

    async def get_company(self, company_id):
        for c in self.companies:
            if c['id'] == company_id:
                return c
        return None

    async def get_company_by_login(self, login):
        """Admin login bo'yicha kompaniyani topish"""
        for acc in self.admin_accounts:
            if acc.get('login') == login:
                company_id = acc.get('company_id')
                if company_id:
                    return await self.get_company(company_id)
        return None

    async def add_company(self, name, login, password, category="Fast-food / Kafe", address="Asaka shahar"):
        """Yangi kompaniya va uning admin akkauntini qo'shish"""
        c_id = 1
        if self.companies:
            c_id = max(c['id'] for c in self.companies) + 1

        new_company = {
            "id": c_id,
            "name": name,
            "category": category,
            "products": [],
            "categories": [],
            "couriers": [],
            "orders": [],
            "address": address,
            "latitude": 40.6415,
            "longitude": 72.2392,
            "admin_contact": {"name": name, "phone": "", "username": ""},
            "is_frozen": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self.companies.append(new_company)

        # Kompaniya uchun admin akkaunt yaratamiz
        self.admin_accounts.append({
            "login": login,
            "password": password,
            "name": name + " Admin",
            "is_superadmin": False,
            "company_id": c_id
        })

        self.save_data()
        self.export_webapp_products()
        return new_company

    async def delete_company(self, company_id):
        """Kompaniyani va uning admin akkauntini o'chirish"""
        # Kompaniyaning admin akkauntlarini o'chirish
        self.admin_accounts = [
            a for a in self.admin_accounts
            if a.get('company_id') != company_id
        ]
        # Kompaniyani o'chirish
        self.companies = [c for c in self.companies if c['id'] != company_id]
        self.save_data()
        self.export_webapp_products()

    async def toggle_company_freeze(self, company_id):
        """Kompaniyani muzlatish yoki faollashtirish"""
        for c in self.companies:
            if c['id'] == company_id:
                c['is_frozen'] = not c.get('is_frozen', False)
                break
        self.save_data()
        self.export_webapp_products()

    # ========================
    # PARTNER REQUEST METHODS
    # ========================
    async def add_partner_request(self, user_id, store_name, category, phone, address, comment="", username=None, fullname=None):
        if not hasattr(self, 'partner_requests'):
            self.partner_requests = []
        req_id = 1
        if self.partner_requests:
            req_id = max(r.get('id', 0) for r in self.partner_requests) + 1

        req = {
            "id": req_id,
            "user_id": int(user_id),
            "fullname": fullname or "",
            "username": username or "",
            "store_name": store_name,
            "category": category,
            "phone": phone,
            "address": address,
            "comment": comment,
            "status": "pending",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "company_id": None
        }
        self.partner_requests.append(req)
        self.save_data()
        return req

    async def get_partner_requests(self, status=None):
        reqs = getattr(self, 'partner_requests', [])
        if status:
            return [r for r in reqs if r.get('status') == status]
        return reqs

    async def get_partner_request(self, req_id):
        for r in getattr(self, 'partner_requests', []):
            if r.get('id') == int(req_id):
                return r
        return None

    async def approve_partner_request(self, req_id):
        req = await self.get_partner_request(req_id)
        if not req or req.get('status') == 'approved':
            return None, None

        import random
        raw_slug = "".join(ch for ch in req['store_name'].lower() if ch.isalnum())
        if not raw_slug:
            raw_slug = "shop"
        login = f"{raw_slug[:8]}_{req['id']}"
        password = f"asaka{random.randint(100, 999)}"

        company = await self.add_company(
            name=req['store_name'],
            login=login,
            password=password,
            category=req.get('category', "Do'kon"),
            address=req.get('address', "Asaka shahar")
        )
        company['admin_contact'] = {
            "name": req.get('fullname') or req['store_name'],
            "phone": req.get('phone', ''),
            "username": f"@{req['username']}" if req.get('username') else ""
        }
        req['status'] = 'approved'
        req['company_id'] = company['id']
        req['login'] = login
        req['password'] = password
        self.save_data()
        self.export_webapp_products()
        return req, company

    async def reject_partner_request(self, req_id):
        req = await self.get_partner_request(req_id)
        if not req:
            return None
        req['status'] = 'rejected'
        self.save_data()
        return req

    async def get_company_id_for_admin(self, user_id):
        """Admin user_id bo'yicha uning kompaniyasini topish"""
        login = self.admin_sessions.get(str(user_id))
        if not login:
            return None
        for acc in self.admin_accounts:
            if acc.get('login') == login:
                return acc.get('company_id')  # None = superadmin
        return None

    async def is_superadmin_session(self, user_id):
        """Foydalanuvchi superadmin sifatida kirganmi?"""
        login = self.admin_sessions.get(str(user_id))
        if not login:
            return False
        for acc in self.admin_accounts:
            if acc.get('login') == login:
                return acc.get('is_superadmin', False)
        # Agar login topilmasa — eski superadmin
        return True

    # ========================
    # USER METHODS
    # ========================
    async def add_user(self, telegram_id, fullname, phone=None, lang="uz", username=None):
        telegram_id_str = str(telegram_id)
        is_new = False
        if telegram_id_str not in self.users:
            self.users[telegram_id_str] = {
                "id": len(self.users) + 1,
                "telegram_id": telegram_id,
                "fullname": fullname,
                "username": username,
                "phone": phone,
                "lang": lang,
                "balance": 0,
                "referrals_count": 0,
                "referred_by": None,
                "last_bonus_date": None,
                "wheel_spins_today": 0,
                "wheel_last_date": None,
                "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            self.save_data()
            is_new = True
        elif username and self.users[telegram_id_str].get("username") != username:
            self.users[telegram_id_str]["username"] = username
            self.save_data()
        return is_new

    async def get_user_balance(self, telegram_id):
        u = await self.get_user(telegram_id)
        return int(u.get("balance", 0)) if u else 0

    async def update_user_balance(self, telegram_id, amount):
        u = await self.get_user(telegram_id)
        if u:
            current = int(u.get("balance", 0))
            new_bal = max(0, current + int(amount))
            u["balance"] = new_bal
            self.save_data()
            return new_bal
        return 0

    async def can_claim_daily_bonus(self, telegram_id):
        u = await self.get_user(telegram_id)
        if not u:
            return False, 0
        last_bonus = u.get("last_bonus_date")
        if not last_bonus:
            return True, 0
        try:
            last_dt = datetime.fromisoformat(last_bonus)
            diff = (datetime.now() - last_dt).total_seconds()
            wait_seconds = 24 * 3600
            if diff >= wait_seconds:
                return True, 0
            else:
                return False, int(wait_seconds - diff)
        except Exception:
            return True, 0

    async def claim_daily_bonus(self, telegram_id, min_amount=2, max_amount=10000):
        can_claim, wait_sec = await self.can_claim_daily_bonus(telegram_id)
        if not can_claim:
            return False, wait_sec, 0
        import random
        bonus = random.randint(min_amount, max_amount)
        u = await self.get_user(telegram_id)
        u["last_bonus_date"] = datetime.now().isoformat()
        current = int(u.get("balance", 0))
        new_bal = current + bonus
        u["balance"] = new_bal
        self.save_data()
        return True, bonus, new_bal

    async def add_referral(self, referrer_id, new_user_id, bonus=400):
        referrer_id = int(referrer_id)
        new_user_id = int(new_user_id)
        if referrer_id == new_user_id:
            return False, 0, None
        ref_user = await self.get_user(referrer_id)
        new_u = await self.get_user(new_user_id)
        if not ref_user or not new_u:
            return False, 0, None
        if new_u.get("referred_by"):
            return False, 0, None
        new_u["referred_by"] = referrer_id
        current = int(ref_user.get("balance", 0))
        ref_user["balance"] = current + bonus
        ref_user["referrals_count"] = int(ref_user.get("referrals_count", 0)) + 1
        self.save_data()
        return True, bonus, ref_user

    async def can_spin_wheel(self, telegram_id):
        u = await self.get_user(telegram_id)
        if not u:
            return False, 0, 0
        today_str = datetime.now().strftime("%Y-%m-%d")
        last_date = u.get("wheel_last_date")
        if last_date != today_str:
            spins_today = 0
        else:
            spins_today = int(u.get("wheel_spins_today", 0))
        remaining = max(0, 2 - spins_today)
        if remaining > 0:
            return True, remaining, 0
        now = datetime.now()
        midnight = datetime(now.year, now.month, now.day) + timedelta(days=1)
        wait_seconds = int((midnight - now).total_seconds())
        return False, 0, wait_seconds

    async def spin_wheel(self, telegram_id):
        can_spin, remaining, wait_sec = await self.can_spin_wheel(telegram_id)
        if not can_spin:
            u = await self.get_user(telegram_id)
            bal = int(u.get("balance", 0)) if u else 0
            return False, None, 0, bal, wait_sec
        import random
        sectors = [
            {"type": "bankrot", "amount": 0, "name": "💣 Bankrot"},
            {"type": "prize", "amount": 1000, "name": "🥉 1 000 so'm"},
            {"type": "prize", "amount": 3000, "name": "🥈 3 000 so'm"},
            {"type": "prize", "amount": 10000, "name": "🥇 10 000 so'm"}
        ]
        # weights: bankrot 65%, 1 000 som 20%, 3 000 som 12%, 10 000 som 3%
        weights = [65, 20, 12, 3]
        selected = random.choices(sectors, weights=weights, k=1)[0]

        u = await self.get_user(telegram_id)
        today_str = datetime.now().strftime("%Y-%m-%d")
        if u.get("wheel_last_date") != today_str:
            u["wheel_spins_today"] = 0
        u["wheel_spins_today"] = int(u.get("wheel_spins_today", 0)) + 1
        u["wheel_last_date"] = today_str

        current_bal = int(u.get("balance", 0))
        if selected["type"] == "prize":
            new_bal = current_bal + selected["amount"]
            u["balance"] = new_bal
        else:
            new_bal = current_bal

        rem_spins = max(0, 2 - u["wheel_spins_today"])
        self.save_data()
        return True, selected, rem_spins, new_bal, 0

    # ========================
    # PROMOCODE & RETENTION METHODS
    # ========================
    async def get_all_promocodes(self):
        return getattr(self, 'promocodes', {})

    async def add_promocode(self, code: str, amount: int, max_uses: int = 100):
        code_clean = code.strip().upper()
        if not hasattr(self, 'promocodes') or not isinstance(self.promocodes, dict):
            self.promocodes = {}
        self.promocodes[code_clean] = {
            "code": code_clean,
            "amount": int(amount),
            "max_uses": int(max_uses),
            "used_by": [],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        self.save_data()
        return self.promocodes[code_clean]

    async def delete_promocode(self, code: str):
        code_clean = code.strip().upper()
        if hasattr(self, 'promocodes') and code_clean in self.promocodes:
            del self.promocodes[code_clean]
            self.save_data()
            return True
        return False

    async def use_promocode(self, telegram_id: int, code: str):
        code_clean = code.strip().upper()
        if not hasattr(self, 'promocodes') or code_clean not in self.promocodes:
            return False, "❌ Bunday promokod mavjud emas yoki muddati tugagan!", 0, 0
        promo = self.promocodes[code_clean]
        used_by = promo.setdefault("used_by", [])
        if telegram_id in used_by:
            return False, "⚠️ Siz ushbu promokodni allaqachon ishlatgansiz!", 0, 0
        if len(used_by) >= promo.get("max_uses", 100):
            return False, "⚠️ Ushbu promokodning faollashuv limiti tugagan!", 0, 0
        
        amount = int(promo.get("amount", 0))
        used_by.append(telegram_id)
        new_bal = await self.update_user_balance(telegram_id, amount)
        self.save_data()
        return True, f"🎉 Tabriklaymiz! Balansingizga +{amount:,} so'm qo'shildi!".replace(",", " "), amount, new_bal

    async def get_top_referrers(self, limit=10):
        users_list = list(self.users.values())
        sorted_users = sorted(
            [u for u in users_list if int(u.get("referrals_count", 0)) > 0],
            key=lambda x: int(x.get("referrals_count", 0)),
            reverse=True
        )
        return sorted_users[:limit]

    async def set_user_lang(self, telegram_id, lang):
        telegram_id_str = str(telegram_id)
        if telegram_id_str in self.users:
            self.users[telegram_id_str]['lang'] = lang
            self.save_data()

    async def get_user(self, telegram_id):
        return self.users.get(str(telegram_id))

    async def get_all_users(self):
        return list(self.users.values())

    async def add_admin(self, admin_id):
        if admin_id not in self.admins:
            self.admins.append(admin_id)
            self.save_data()

    async def get_admins(self):
        return self.admins

    async def get_admin_contact(self, company_id=None):
        if company_id:
            company = await self.get_company(company_id)
            if company:
                return company.get('admin_contact', {"name": "Admin", "phone": "", "username": ""})
        return getattr(self, 'admin_contact', {"name": "Fast Food Admin", "phone": "+998 90 123 45 67", "username": "@admin"})

    async def update_admin_contact(self, name, phone, username, company_id=None):
        if company_id:
            company = await self.get_company(company_id)
            if company:
                company['admin_contact'] = {"name": name, "phone": phone, "username": username}
        else:
            self.admin_contact = {"name": name, "phone": phone, "username": username}
        self.save_data()

    async def get_categories(self, company_id=None):
        if company_id:
            company = await self.get_company(company_id)
            if company:
                return company.get('categories', [])
            return []
        return getattr(self, 'categories', [])

    async def add_category(self, cat, company_id=None):
        if company_id:
            company = await self.get_company(company_id)
            if company:
                if cat not in company.get('categories', []):
                    if 'categories' not in company:
                        company['categories'] = []
                    company['categories'].append(cat)
                    self.save_data()
                    self.export_webapp_products()
        else:
            if cat not in self.categories:
                self.categories.append(cat)
                self.save_data()

    async def remove_category(self, cat, company_id=None):
        if company_id:
            company = await self.get_company(company_id)
            if company and cat in company.get('categories', []):
                company['categories'].remove(cat)
                self.save_data()
                self.export_webapp_products()
        else:
            if cat in self.categories:
                self.categories.remove(cat)
                self.save_data()
                self.export_webapp_products()

    async def get_admin_accounts(self):
        return getattr(self, 'admin_accounts', [])

    async def add_admin_account(self, login, password, name, company_id=None, is_superadmin=False):
        self.admin_accounts.append({
            "login": login,
            "password": password,
            "name": name,
            "is_superadmin": is_superadmin,
            "company_id": company_id
        })
        self.save_data()

    async def remove_admin_account(self, login):
        self.admin_accounts = [a for a in self.admin_accounts if a['login'] != login]
        self.save_data()

    async def set_admin_session(self, user_id, login):
        if not hasattr(self, 'admin_sessions'):
            self.admin_sessions = {}
        self.admin_sessions[str(user_id)] = login
        if user_id not in self.admins:
            self.admins.append(user_id)
        self.save_data()

    async def get_admin_session(self, user_id):
        if not hasattr(self, 'admin_sessions'):
            return "Noma'lum Admin"
        return self.admin_sessions.get(str(user_id), "Asosiy Admin")

    # ========================
    # PRODUCT METHODS (company-aware)
    # ========================
    async def get_products(self, company_id=None):
        if company_id:
            company = await self.get_company(company_id)
            if company:
                return [p for p in company.get('products', []) if p.get('is_active', 1)]
            return []
        return [p for p in self.products if p.get('is_active', 1)]

    async def add_product(self, name, description, price, category="Boshqa", image="", company_id=None):
        if company_id:
            company = await self.get_company(company_id)
            if not company:
                return
            products_list = company.setdefault('products', [])
            product_id = 1
            if products_list:
                product_id = max(p['id'] for p in products_list) + 1

            products_list.append({
                "id": product_id,
                "name": name,
                "category": category,
                "description": description,
                "price": price,
                "is_active": 1,
                "emoji": "🍽",
                "image": image if image else "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=500&q=80",
                "company_id": company_id
            })
        else:
            product_id = 1
            if self.products:
                product_id = max(p['id'] for p in self.products) + 1
            self.products.append({
                "id": product_id,
                "name": name,
                "category": category,
                "description": description,
                "price": price,
                "is_active": 1,
                "emoji": "🍽",
                "image": image if image else "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?auto=format&fit=crop&w=500&q=80"
            })

        self.save_data()
        self.export_webapp_products()

    async def toggle_product(self, product_id, company_id=None):
        if company_id:
            company = await self.get_company(company_id)
            if company:
                for p in company.get('products', []):
                    if p['id'] == product_id:
                        p['is_active'] = 0 if p.get('is_active', 1) == 1 else 1
                        break
        else:
            for p in self.products:
                if p['id'] == product_id:
                    p['is_active'] = 0 if p.get('is_active', 1) == 1 else 1
                    break
        self.save_data()
        self.export_webapp_products()

    async def edit_product(self, product_id, new_price, new_image, new_desc=None, company_id=None):
        product_list = self.products
        if company_id:
            company = await self.get_company(company_id)
            if company:
                product_list = company.get('products', [])

        for p in product_list:
            if p['id'] == product_id:
                if new_price is not None:
                    p['price'] = new_price
                if new_image:
                    p['image'] = new_image
                if new_desc:
                    p['description'] = new_desc
                break

        self.save_data()
        self.export_webapp_products()

    async def delete_product(self, product_id, company_id=None):
        if company_id:
            company = await self.get_company(company_id)
            if company:
                company['products'] = [p for p in company.get('products', []) if p['id'] != product_id]
        else:
            self.products = [p for p in self.products if p['id'] != product_id]
        self.save_data()
        self.export_webapp_products()

    def get_all_products_for_company(self, company_id):
        """DB sync uchun (non-async)"""
        for c in self.companies:
            if c['id'] == company_id:
                return c.get('products', [])
        return []

    # ========================
    # COURIER METHODS (company-aware)
    # ========================
    async def get_couriers(self, company_id=None):
        if company_id:
            company = await self.get_company(company_id)
            if company:
                return company.get('couriers', [])
            return []
        return getattr(self, 'couriers', [])

    async def add_courier(self, telegram_id, fullname, phone, company_id=None):
        telegram_id = int(telegram_id)
        if company_id:
            company = await self.get_company(company_id)
            if not company:
                return None
            couriers_list = company.setdefault('couriers', [])
            existing = next((c for c in couriers_list if c.get('telegram_id') == telegram_id), None)
            if existing:
                existing['fullname'] = fullname
                existing['phone'] = phone
                self.save_data()
                return existing
            c_id = 1 if not couriers_list else max(c['id'] for c in couriers_list) + 1
            new_courier = {
                "id": c_id,
                "telegram_id": telegram_id,
                "fullname": fullname,
                "phone": phone,
                "company_id": company_id,
                "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            couriers_list.append(new_courier)
        else:
            if not hasattr(self, 'couriers'):
                self.couriers = []
            existing = next((c for c in self.couriers if c.get('telegram_id') == telegram_id), None)
            if existing:
                existing['fullname'] = fullname
                existing['phone'] = phone
                self.save_data()
                return existing
            c_id = 1 if not self.couriers else max(c['id'] for c in self.couriers) + 1
            new_courier = {
                "id": c_id,
                "telegram_id": telegram_id,
                "fullname": fullname,
                "phone": phone,
                "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            self.couriers.append(new_courier)

        self.save_data()
        return new_courier

    async def delete_courier(self, courier_id, company_id=None):
        if company_id:
            company = await self.get_company(company_id)
            if company:
                company['couriers'] = [c for c in company.get('couriers', []) if c['id'] != courier_id]
        else:
            if hasattr(self, 'couriers'):
                self.couriers = [c for c in self.couriers if c['id'] != courier_id]
        self.save_data()

    async def get_courier_company(self, telegram_id):
        """Kuryer qaysi kompaniyaga tegishli ekanini topish"""
        for c in self.companies:
            for courier in c.get('couriers', []):
                if courier['telegram_id'] == telegram_id:
                    return c['id']
        return None

    # ========================
    # ORDER METHODS (company-aware)
    # ========================
    async def create_order(self, user_id, total_price, location, phone, items, order_type="Oddiy", room_table=None, comment="", company_id=None, used_balance=0, original_price=None):
        orig_price = original_price if original_price is not None else total_price
        if company_id:
            company = await self.get_company(company_id)
            if not company:
                return None
            orders_list = company.setdefault('orders', [])
            order_id = 1
            if orders_list:
                order_id = max(o['id'] for o in orders_list) + 1

            orders_list.append({
                "id": order_id,
                "user_id": user_id,
                "total_price": total_price,
                "original_price": orig_price,
                "used_balance": used_balance,
                "location": location,
                "phone": phone,
                "status": "Yangi",
                "items": items,
                "order_type": order_type,
                "room_table": room_table,
                "comment": comment,
                "courier_id": None,
                "company_id": company_id,
                "created_at": datetime.now().strftime('%d.%m.%Y %H:%M')
            })
        else:
            order_id = 1
            if self.orders:
                order_id = max(o['id'] for o in self.orders) + 1

            self.orders.append({
                "id": order_id,
                "user_id": user_id,
                "total_price": total_price,
                "original_price": orig_price,
                "used_balance": used_balance,
                "location": location,
                "phone": phone,
                "status": "Yangi",
                "items": items,
                "order_type": order_type,
                "room_table": room_table,
                "comment": comment,
                "courier_id": None,
                "created_at": datetime.now().strftime('%d.%m.%Y %H:%M')
            })

        self.save_data()
        return order_id

    async def get_user_orders(self, user_id, limit=10):
        all_orders = list(self.orders)
        # Kompaniyalardan ham zakazlarni qo'shamiz
        for c in self.companies:
            all_orders.extend(c.get('orders', []))
        user_orders = [o for o in all_orders if o['user_id'] == user_id]
        return list(reversed(user_orders))[:limit]

    async def get_user_stats(self, user_id):
        all_orders = list(self.orders)
        for c in self.companies:
            all_orders.extend(c.get('orders', []))
        user_orders = [o for o in all_orders if o['user_id'] == user_id and o['status'] != "Bekor qilingan"]
        total_spent = sum(o['total_price'] for o in user_orders)
        return {
            "order_count": len(user_orders),
            "total_spent": total_spent
        }

    async def get_dashboard_stats(self, company_id=None):
        today_str = datetime.now().strftime('%d.%m.%Y')
        if company_id:
            company = await self.get_company(company_id)
            orders = company.get('orders', []) if company else []
        else:
            orders = self.orders

        today_orders = [o for o in orders if o.get('created_at', '').startswith(today_str)]
        total_revenue = sum(o.get('total_price', 0) for o in orders if o.get('status') not in ["Bekor qilingan", "Archivlangan"])
        today_revenue = sum(o.get('total_price', 0) for o in today_orders if o.get('status') not in ["Bekor qilingan", "Archivlangan"])

        if company_id:
            company = await self.get_company(company_id)
            products_count = len([p for p in company.get('products', []) if p.get('is_active', 1)]) if company else 0
        else:
            products_count = len([p for p in self.products if p.get('is_active', 1)])

        return {
            "products": products_count,
            "orders": len(orders),
            "users": len(self.users),
            "today_orders": len(today_orders),
            "total_revenue": total_revenue,
            "today_revenue": today_revenue
        }

    async def update_order_status(self, order_id, status, company_id=None):
        if company_id:
            company = await self.get_company(company_id)
            if company:
                for o in company.get('orders', []):
                    if o['id'] == order_id:
                        o['status'] = status
                        break
        else:
            for o in self.orders:
                if o['id'] == order_id:
                    o['status'] = status
                    break
        self.save_data()

    def find_order(self, order_id, company_id=None):
        """Zakazni topish (sync)"""
        if company_id:
            for c in self.companies:
                if c['id'] == company_id:
                    for o in c.get('orders', []):
                        if o['id'] == order_id:
                            return o
            return None
        return next((o for o in self.orders if o['id'] == order_id), None)

    async def reset_revenue(self, company_id=None):
        if company_id:
            company = await self.get_company(company_id)
            if company:
                for o in company.get('orders', []):
                    if o['status'] not in ["Bekor qilingan"]:
                        o['status'] = "Archivlangan"
        else:
            for o in self.orders:
                if o['status'] not in ["Bekor qilingan"]:
                    o['status'] = "Archivlangan"
        self.save_data()

    # ========================
    # MARKET-WINNING ADVANCED FEATURES
    # ========================
    async def transfer_balance(self, sender_tg_id: int, target_identifier: str, amount: int):
        sender = await self.get_user(sender_tg_id)
        if not sender:
            return False, "Foydalanuvchi hisobi topilmadi!", 0, None
        
        amount = int(amount)
        if amount <= 0:
            return False, "O'tkazma summasi musbat bo'lishi kerak!", int(sender.get("balance", 0)), None
            
        current_bal = int(sender.get("balance", 0))
        if current_bal < amount:
            return False, f"Mablag' yetarli emas! Sizning balansingiz: {current_bal:,} so'm.".replace(",", " "), current_bal, None

        target_clean = str(target_identifier).strip().lstrip("@")
        target_user = None
        for u in self.users.values():
            if str(u.get("telegram_id")) == target_clean:
                target_user = u
                break
            if u.get("username") and u.get("username").lower() == target_clean.lower():
                target_user = u
                break
            if u.get("phone") and target_clean in u.get("phone"):
                target_user = u
                break

        if not target_user:
            return False, "❌ Bunday foydalanuvchi botda topilmadi!\nDo'stingiz avval botga kirib /start bosgan bo'lishi kerak.", current_bal, None

        if int(target_user.get("telegram_id")) == int(sender_tg_id):
            return False, "⚠️ O'zingizning hisobingizga pul o'tkaza olmaysiz!", current_bal, None

        # Transfer
        sender["balance"] = current_bal - amount
        target_user["balance"] = int(target_user.get("balance", 0)) + amount
        self.save_data()
        return True, "Muvaffaqiyatli", sender["balance"], target_user

    async def get_last_user_order(self, user_id: int):
        all_orders = list(self.orders)
        for c in self.companies:
            all_orders.extend(c.get('orders', []))
        user_orders = [o for o in all_orders if o.get('user_id') == user_id and o.get('status') != "Bekor qilingan"]
        if user_orders:
            return user_orders[-1]
        return None

    async def add_order_review(self, order_id: int, user_id: int, stars: int, company_id=None):
        order = self.find_order(order_id, company_id)
        if not order:
            return False, "Buyurtma topilmadi!", 0
        if order.get("reviewed"):
            u = await self.get_user(user_id)
            return False, "Siz ushbu buyurtmaga allaqachon baho bergansiz!", int(u.get("balance", 0)) if u else 0
        order["reviewed"] = True
        order["review_stars"] = stars
        bonus = 500
        new_bal = await self.update_user_balance(user_id, bonus)
        self.save_data()
        return True, "Rahmat! Bahoingiz qabul qilindi.", new_bal

    def search_products(self, query: str):
        q = query.lower().strip()
        if not q or len(q) < 2:
            return []
        results = []
        for p in getattr(self, 'products', []):
            if p.get('is_active', 1) and (q in p.get('name', '').lower() or q in p.get('description', '').lower()):
                p_copy = dict(p)
                p_copy['company_name'] = "Umumiy Kafe"
                p_copy['company_id'] = None
                results.append(p_copy)
        for c in getattr(self, 'companies', []):
            if c.get('is_frozen'): continue
            for p in c.get('products', []):
                if p.get('is_active', 1) and (q in p.get('name', '').lower() or q in p.get('description', '').lower()):
                    p_copy = dict(p)
                    p_copy['company_name'] = c.get('name', 'Kafe')
                    p_copy['company_id'] = c.get('id')
                    results.append(p_copy)
        return results[:8]

    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
        import math
        R = 6371.0 # Yer radiusi km da
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    async def get_nearby_companies(self, user_lat: float, user_lon: float):
        companies = await self.get_companies()
        active = [c for c in companies if not c.get('is_frozen')]
        if not active:
            loc = getattr(self, 'admin_location', {"address": "Asaka shahar", "latitude": 40.6415, "longitude": 72.2392})
            dist_km = self.calculate_distance(float(user_lat), float(user_lon), float(loc.get("latitude", 40.6415)), float(loc.get("longitude", 72.2392)))
            return [{
                "id": None,
                "name": "Asosiy Oshxona",
                "address": loc.get("address", "Asaka shahar"),
                "latitude": loc.get("latitude", 40.6415),
                "longitude": loc.get("longitude", 72.2392),
                "distance_km": dist_km,
                "admin_contact": getattr(self, 'admin_contact', {})
            }]
        with_distance = []
        without_distance = []
        for c in active:
            lat = c.get('latitude')
            lon = c.get('longitude')
            c_dict = dict(c)
            if lat is not None and lon is not None:
                try:
                    dist_km = self.calculate_distance(float(user_lat), float(user_lon), float(lat), float(lon))
                    c_dict['distance_km'] = dist_km
                    with_distance.append(c_dict)
                except Exception:
                    without_distance.append(c_dict)
            else:
                c_dict['distance_km'] = None
                without_distance.append(c_dict)
        with_distance.sort(key=lambda x: x['distance_km'])
        return with_distance + without_distance

    async def update_company_location(self, company_id, address=None, latitude=None, longitude=None):
        if company_id:
            c = await self.get_company(company_id)
            if c:
                if address is not None:
                    c["address"] = address
                if latitude is not None and longitude is not None:
                    c["latitude"] = float(latitude)
                    c["longitude"] = float(longitude)
                self.save_data()
                return c
        else:
            if not hasattr(self, 'admin_location'):
                self.admin_location = {"address": "Asaka shahar", "latitude": 40.6415, "longitude": 72.2392}
            if address is not None:
                self.admin_location["address"] = address
            if latitude is not None and longitude is not None:
                self.admin_location["latitude"] = float(latitude)
                self.admin_location["longitude"] = float(longitude)
            self.save_data()
            return self.admin_location
