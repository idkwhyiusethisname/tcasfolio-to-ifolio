# 📚 mytcas-to-ifolio

สคริปต์ Python คัดลอกผลงานจากแฟ้ม TCASFOLIO (student.mytcas.com) ไปใส่ใน iFolio ของ KMITL (ifolio.kmitl.ac.th) อัตโนมัติ (สิ่งนี้ไม่เกี่ยวอะไรกับ ทปอ และลาดกระบัง นะจัฟ use at your own risk) 

# ⭐ Star This Repo 

⭐ ถ้าดาวเยอะๆ เดียวมาอัพเดตต่อ ให้รองรับหลายๆอย่าง กดเร็วๆๆๆ 

## Why ?
ขีเกียจก๊อปวางเอง แม่งเยอะ

## How Does it work ?

| ใน mytcas | ไป iFolio |
|---|---|
| รางวัล (awards) | การแข่งขัน |
| กิจกรรม (activities) | กิจกรรม |
| ผลงาน/โปรเจกต์ (projects) | กิจกรรม |

- ใส่รูปแรกของแต่ละรายการ (iFolio รับรูปเดียว) ถ้าไม่มีรูปจะใส่รูปขาวเปล่าแทน เพราะ iFolio ไม่ยอมให้สร้างรายการที่ไม่มีรูป
- บันทึกรายการที่คัดลอกแล้วไว้ใน `copied_to_ifolio.json` รันซ้ำจะข้ามรายการเดิม

> ### ⚠️ เรื่องวันที่ 
> **mytcas ไม่เก็บวันที่** แต่ iFolio บังคับให้ใส่ สคริปต์จึง **ไม่ได้ดึงวันที่จริง** แต่เดาให้:
> - ถ้าชื่อรายการมีปี (เช่น `2025` หรือ `2568`) จะใช้ **1 ม.ค. ของปีนั้น**
> - ถ้าไม่มีปีในชื่อ จะใช้ `DEFAULT_DATE` ในไฟล์ (ค่าเริ่มต้น `2026-01-01`)
>
> **ควรเข้าไปแก้วันที่ของแต่ละรายการใน iFolio ภายหลังเสมอ**

## วิธีใช้

1. ติดตั้ง `pip install requests` /  โหลด Exe ใน [Release](https://github.com/idkwhyiusethisname/tcasfolio-to-ifolio/releases)
2. ล็อกอินทั้งสองเว็บในเบราว์เซอร์ กด F12 > Network > กด F5 ที่หน้าไหนก็ได้ > Request Headers แล้วคัดลอกค่า `Cookie:`
3. ใส่ลงใน `cookies.json`
   ```json
   {
     "MYTCAS_COOKIE": "ค่า accessToken ที่อยู่ใน Requests Headers ของ student.mytcas.com",
     "IFOLIO_COOKIE": "ทั้งบรรทัด Cookie ของ ifolio.kmitl.ac.th"
   }
   ```
4. รัน `python mytcas_to_ifolio.py` / กดเปิด EXE แล้วใส่
   - ลิงก์แฟ้ม mytcas เช่น `https://student.mytcas.com/profile/folios/<id>` <img width="1392" height="630" alt="image (10)" src="https://github.com/user-attachments/assets/3fb46174-0c1a-4845-99f4-1bb5f28ecae0" />
   - ชื่อพอร์ตโฟลิโอใน iFolio ที่จะก๊อปงานลงไป <img width="2066" height="647" alt="image (8)" src="https://github.com/user-attachments/assets/7b1b27ee-5397-4017-8f8c-555c98bf7953" />


## Warning

- `cookies.json` คือรหัสเข้าบัญชีของคุณ ห้ามแชร์หรืออัปโหลดขึ้นที่สาธารณะ cookie หมดอายุได้ ถ้าเจอ 403 ให้ล็อกอินใหม่แล้วคัดลอกใหม่
- สคริปต์ไม่ตรวจรายการซ้ำที่มีอยู่ใน iFolio ก่อนแล้ว ถ้าพอร์ตโฟลิโอปลายทางมีรายการเดิมอยู่ อาจซ้ำ
- ใช้ endpoint ภายในของเว็บ (`/_serverFn/<hash>`) ซึ่งเปลี่ยนเมื่อ iFolio อัปเดต ถ้าเจอ 404/500 ต้องเก็บค่า hash ใหม่ใส่ในไฟล์
- ใช้กับบัญชีของตัวเองเท่านั้น โปรเจกต์นี้ไม่เกี่ยวข้องกับ TCAS หรือ KMITL

## Future Plan

- [ ] ดึงวันที่จริง (ถ้ามีที่มา แบบดีๆ หรือ Phrase มาตาม format) หรือถามวันที่ทีละรายการ แทนการเดาจากปี
- [ ] ตรวจรายการซ้ำใน iFolio ก่อนสร้าง
- [ ] บัคบางอันที่บอกเพิ่มรูปไม่ได้ แต่จริงๆเพิ่มได้ปกติ 
- [ ] มี GUI ทำให้ใช้งานได้ง่ายขึ้น
- [ ] แยก ผลงานกับโปรเจก ออกจากกิจกรรม (ขี้เกียจทำ)
- [ ] ออโต้ดึง Cookie (ขี้เกียจทำ)
- [ ] เลือกพอร์ดได้เลยภายในแอพไม่ต้องไปนั่งก๊อปลิ้ง/สร้าง ifolio
- [ ] recode เป็น Chrome Extentions (ขี้เกียจ)

## Contributing

Open For Pull Request หรือ ถ้าเจอปัญหาหรืออยากได้ฟีเจอร์ เปิด Issue ได้เลย (ถ้าแนบ error ด้วย ให้ลบ cookie และข้อมูลส่วนตัวออกก่อน)

## License

MIT License © 2026. Free to use, modify and distribute, with no warranty of any kind.
