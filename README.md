# Texnobrend Telegram Bot

Texnobrend — bu maishiy texnika va smartfonlar do'koni uchun yaratilgan professional, ko'p funksiyali Telegram bot. Bot orqali foydalanuvchilar mahsulotlarni ko'rishlari, qidirishlari, savatchaga qo'shishlari va buyurtma berishlari mumkin. Adminlar esa statistika, foydalanuvchilar, mahsulotlar va buyurtmalarni to'liq nazorat qila oladilar.

## 🚀 Imkoniyatlar va Xususiyatlar
- **📦 Mahsulotlar katalogi**: Brend ➔ Kategoriya ➔ Model tizimi bo'yicha tartiblangan katalog.
- **💾 SQLite + Avtomatik Seeding**: Ma'lumotlar bazasi SQLite-da (`aiosqlite`) bo'lib, birinchi ishga tushishda 59 ta tayyor mahsulot bilan to'ldiriladi.
- **🔍 Aqlli Qidiruv**: Foydalanuvchi yozgan kalit so'zlar bo'yicha mahsulotlarni qidirish (sinonimlar va xatolarga chidamlilik bilan).
- **🛒 Savatcha va Buyurtma**: Savatchaga mahsulot qo'shish, sonini o'zgartirish, tezkor buyurtma (fast order) va Click/Payme/Naqd to'lov tizimlari.
- **📢 Majburiy Obuna (Middleware)**: Botdan foydalanishdan oldin ma'lum kanallarga obuna bo'lishni talab qilish.
- **🧮 Kalkulyator**: Mahsulotlar narxini hisoblash uchun sodda kalkulyator.
- **🤖 Zamonaviy Bot API Imkoniyatlari**:
  - Message Effects (API 7.4) — confetti, otashin va boshqalar.
  - CopyTextButton (API 7.11) — matnlarni tez nusxalash tugmasi.
  - Premium stikerlar tizimi.
- **👑 Admin Panel (`/panel`)**:
  - Statistika (foydalanuvchilar, bugungi buyurtmalar, umumiy daromad).
  - Foydalanuvchilarni bloklash va ularga xabar yuborish.
  - Mahsulot qo'shish, o'chirish, tahrirlash va rasmini yangilash.
  - Buyurtmalarni boshqarish (holatini yangilash: pending, processing, completed, cancelled).
  - Broadcast xabarlar yuborish.

## 🛠 Mahalliy ishga tushirish (Local Setup)
1. Python 3.9+ o'rnatilgan bo'lishi kerak.
2. Kutubxonalarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```
3. Loyihaning ildiz papkasida `.env` faylini yarating va quyidagi ma'lumotlarni yozing:
   ```env
   BOT_TOKEN=sizning_bot_tokeningiz
   ADMIN_IDS=5027595868
   ```
4. Botni ishga tushiring:
   ```bash
   python main.py
   ```

## ☁️ Railway orqali Deploy qilish
Railway-da deploy qilish uchun quyidagi muhit o'zgaruvchilarini (Environment Variables) sozlang:
- `BOT_TOKEN`: Telegram bot tokeni.
- `ADMIN_IDS`: Adminlarning Telegram ID raqamlari (vergul bilan ajratilgan, masalan: `5027595868,12345678`).

*Eslatma: Railway-da bot uzluksiz ishlashi uchun uni "Worker" (Background Service) sifatida ishga tushiring yoki Start command sifatida `python main.py` ni belgilang.*

# firstrepo

