# Pixel Noel AR

เว็บ AR ต้นคริสต์มาส voxel สไตล์ 8-bit หมุนได้ ทำงานเป็นหน้าเว็บมือถือ โดยเปิดกล้องหลังเป็นฉากหลังและวาดโมเดลพิกเซลทับแบบเรียลไทม์

## ใช้งาน

1. ไปที่ **Settings → Pages** ของ repo แล้วเลือก **GitHub Actions** เป็นแหล่งเผยแพร่
2. ไปที่ **Actions → Publish Pixel Noel AR → Run workflow** เพื่อเริ่มเผยแพร่ครั้งแรก
3. เปิด URL ผ่าน Safari บน iPhone หรือ Chrome บน Android
4. แตะ **เริ่มประสบการณ์ AR** และอนุญาตกล้อง

การเปิดกล้องบนมือถือจำเป็นต้องเปิดผ่าน HTTPS และแตะปุ่มเริ่มหนึ่งครั้งเพื่ออนุญาตกล้องของเบราว์เซอร์

## ไฟล์ส่งงาน

- `index.html`, `style.css`, `app.js`: เว็บ AR
- `target-poster.svg`: โปสเตอร์สแกน QR สำหรับเปิดหน้าเว็บ (ไม่ใช่ marker ที่ต้องส่องกล้อง)
- `.github/workflows/pages.yml`: workflow สำหรับเผยแพร่เว็บด้วย GitHub Pages

URL สำหรับเว็บ: https://nichanancha-png.github.io/xmas-ar/

หน้าเว็บใช้ภาพกล้องเป็นฉากหลังและวาดต้นไม้ voxel หมุนทับหน้าจอ จึงไม่ต้องพิมพ์ภาพ marker แยก