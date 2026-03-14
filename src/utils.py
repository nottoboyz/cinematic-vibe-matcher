import time
import logging
import requests

# ตั้งค่า logging — ดีกว่า print เพราะบอก timestamp และ level
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)

# __name__ คืออะไร?
# → ชื่อ module ปัจจุบัน เช่น "utils"
# → ทำให้รู้ว่า log มาจากไฟล์ไหน


def safe_request(url, headers=None, params=None, max_attempts=3, delay=2):
    """
    ยิง GET request พร้อม retry logic
    
    Args:
        url: URL ที่จะยิง
        headers: HTTP headers
        params: query parameters
        max_attempts: จำนวนครั้งที่จะลองสูงสุด
        delay: วินาทีที่รอระหว่าง retry
    
    Returns:
        response object ถ้าสำเร็จ
    
    Raises:
        requests.exceptions.HTTPError ถ้าล้มเหลวทุก attempt
    """
    
    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(f"Request: {url} (attempt {attempt}/{max_attempts})")
            
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=10  # รอไม่เกิน 10 วินาที
                # ทำไมต้องมี timeout?
                # → ถ้าไม่มี server ไม่ตอบ = รอไปเรื่อยๆ ตลอดกาล
            )
            
            # จัดการ status code แต่ละประเภท
            if response.status_code == 200:
                logger.info(f"✅ สำเร็จ")
                return response
            
            elif response.status_code == 429:
                # Rate limit — ต้องรอก่อน retry
                wait = int(response.headers.get("Retry-After", delay * attempt))
                logger.warning(f"⚠️ Rate limit! รอ {wait} วินาที...")
                time.sleep(wait)
                continue  # ← ข้ามไป attempt ถัดไป
            
            elif response.status_code in [500, 502, 503, 504]:
                # Server error — retry ได้ เพราะอาจหายเองได้
                logger.warning(f"⚠️ Server error {response.status_code} รอ {delay * attempt} วิ...")
                time.sleep(delay * attempt)
                # ทำไม delay * attempt?
                # → Exponential backoff: 2, 4, 6 วิ
                # → ยิ่งล้มเหลวมาก รอนานขึ้น ไม่รุมยิง server
                continue
            
            else:
                # 4xx อื่นๆ (400, 401, 403, 404) — ไม่ควร retry
                # เพราะปัญหาอยู่ที่ request เรา ไม่ใช่ server
                response.raise_for_status()
        
        except requests.exceptions.Timeout:
            logger.warning(f"⏱️ Timeout! (attempt {attempt}/{max_attempts})")
            if attempt < max_attempts:
                time.sleep(delay * attempt)
                continue
            raise  # attempt สุดท้าย → raise ต่อ
        
        except requests.exceptions.ConnectionError:
            logger.warning(f"🔌 Connection error! (attempt {attempt}/{max_attempts})")
            if attempt < max_attempts:
                time.sleep(delay * attempt)
                continue
            raise
    
    # ถ้าออกมาจาก loop โดยไม่ return = ล้มเหลวทุก attempt
    raise requests.exceptions.HTTPError(
        f"ล้มเหลวหลังจากพยายาม {max_attempts} ครั้ง: {url}"
    )


def safe_json(response, key=None):
    """
    แกะ JSON จาก response อย่างปลอดภัย
    
    ทำไมต้องมี function นี้?
    → response.json() อาจ fail ถ้า server ส่ง HTML มาแทน JSON
    → data[key] อาจ KeyError ถ้า structure เปลี่ยน
    """
    try:
        data = response.json()
        if key:
            return data[key]
        return data
    
    except ValueError as e:
        # response.json() fail → body ไม่ใช่ JSON
        logger.error(f"❌ Response ไม่ใช่ JSON: {response.text[:100]}")
        raise
    
    except KeyError as e:
        # key ไม่มีใน response
        logger.error(f"❌ ไม่พบ key '{key}' ใน response: {list(data.keys())}")
        raise


if __name__ == "__main__":
    # ทดสอบ safe_request
    print("=== ทดสอบ safe_request ===")
    
    # ทดสอบ URL ปกติ
    response = safe_request("https://httpbin.org/get")
    print(f"Status: {response.status_code}")
    
    # ทดสอบ URL ที่ไม่มี (404)
    print("\n=== ทดสอบ 404 ===")
    try:
        response = safe_request("https://httpbin.org/status/404")
    except Exception as e:
        print(f"จับ error ได้: {type(e).__name__}: {e}")
    
    # ทดสอบ 500 (จะ retry 3 รอบ)
    print("\n=== ทดสอบ 500 (retry) ===")
    try:
        response = safe_request(
            "https://httpbin.org/status/500",
            max_attempts=2,
            delay=1
        )
    except Exception as e:
        print(f"จับ error ได้: {type(e).__name__}: {e}")