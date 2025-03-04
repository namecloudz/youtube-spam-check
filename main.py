from spam_detector import YouTubeSpamDetector
import getpass
import os
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup
import json
import re
from config_manager import ConfigManager

def get_api_key():
    """รับ API key จากผู้ใช้หรือใช้ค่าเริ่มต้น"""
    # ลองอ่าน API key จาก environment variable ก่อน
    api_key = os.getenv('YOUTUBE_API_KEY')
    
    if not api_key:
        # ถ้าไม่มีใน environment variable ให้ถามผู้ใช้
        print("\n=== YouTube API Key ===")
        print("1. ใช้ API Key เริ่มต้น")
        print("2. ใส่ API Key ของตัวเอง")
        
        choice = input("\nเลือกตัวเลือก (1-2): ")
        
        if choice == '1':
            api_key = "AIzaSyAKcxbEE8Ta_y3tthEwtYrhLxQNRyBQxx0"
            print("ใช้ API Key เริ่มต้น")
        else:
            api_key = getpass.getpass("กรุณาใส่ API Key ของคุณ: ")
    
    return api_key

def extract_video_id(url):
    """แปลง YouTube URL เป็น video ID"""
    parsed_url = urlparse(url)
    
    if parsed_url.hostname in ('youtu.be', 'www.youtu.be'):
        return parsed_url.path[1:]
    if parsed_url.hostname in ('youtube.com', 'www.youtube.com'):
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query)['v'][0]
    
    raise ValueError("URL ไม่ถูกต้อง กรุณาใส่ URL ของ YouTube video")

def get_video_comments(api_key, video_id):
    """ดึงความคิดเห็นทั้งหมดจาก YouTube video"""
    base_url = "https://www.googleapis.com/youtube/v3/commentThreads"
    comments = []
    
    params = {
        'part': 'snippet',
        'videoId': video_id,
        'key': api_key,
        'maxResults': 100,
        'textFormat': 'plainText'
    }
    
    try:
        print("\nกำลังดึงข้อมูลความคิดเห็น...")
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        items = data.get('items', [])
        
        for item in items:
            comment = item['snippet']['topLevelComment']['snippet']
            comment_data = {
                'id': item['snippet']['topLevelComment']['id'],
                'text': comment['textDisplay'],
                'author': comment['authorDisplayName'],
                'published_at': comment['publishedAt']
            }
            comments.append(comment_data)
        
        # ถ้ามีหน้าถัดไป ดึงข้อมูลเพิ่ม
        while 'nextPageToken' in data and len(comments) < 500:
            params['pageToken'] = data['nextPageToken']
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            items = data.get('items', [])
            
            for item in items:
                comment = item['snippet']['topLevelComment']['snippet']
                comment_data = {
                    'id': item['snippet']['topLevelComment']['id'],
                    'text': comment['textDisplay'],
                    'author': comment['authorDisplayName'],
                    'published_at': comment['publishedAt']
                }
                comments.append(comment_data)
        
        print(f"ดึงข้อมูลสำเร็จ! พบความคิดเห็นทั้งหมด {len(comments)} ข้อความ")
        return comments
        
    except requests.RequestException as e:
        if "quotaExceeded" in str(e):
            print("\nโควต้าการใช้งาน API หมดแล้ว กรุณาลองใหม่ในวันพรุ่งนี้")
        raise Exception(f"ไม่สามารถดึงความคิดเห็นได้: {str(e)}")

def test_single_comment(detector):
    """ทดสอบข้อความเดี่ยว"""
    comment = input("\nใส่ข้อความที่ต้องการตรวจสอบ: ")
    is_spam = detector.is_spam(comment)
    print(f"ผลการตรวจสอบ: {'🚫 Spam' if is_spam else '✅ ไม่ใช่ Spam'}\n")

def analyze_video(detector, url):
    """วิเคราะห์ความคิดเห็นในวิดีโอ"""
    try:
        video_id = extract_video_id(url)
        comments = get_video_comments(detector.api_key, video_id)
        
        if comments:
            spam_comments = []
            total_comments = len(comments)
            spam_count = 0
            
            for comment in comments:
                if detector.is_spam(comment['text']):
                    spam_count += 1
                    spam_comments.append(comment)
            
            spam_percentage = (spam_count / total_comments * 100) if total_comments > 0 else 0
            
            print(f"\n📊 ผลการวิเคราะห์:")
            print(f"💬 จำนวนความคิดเห็นทั้งหมด: {total_comments}")
            print(f"🚫 จำนวน Spam: {spam_count}")
            print(f"📈 เปอร์เซ็นต์ Spam: {spam_percentage:.1f}%")
            
            if spam_comments:
                print("\n🚫 ความคิดเห็นที่เป็น Spam ทั้งหมด:")
                for i, comment in enumerate(spam_comments, 1):
                    print(f"\n{i}. โดย: {comment['author']}")
                    print(f"   เมื่อ: {comment['published_at']}")
                    print(f"   ข้อความ: {comment['text']}")
                    print(f"   ID: {comment['id']}")
                    
                # ถามว่าต้องการจัดการ spam หรือไม่
                action = input("\nต้องการจัดการความคิดเห็น Spam หรือไม่? (1=ลบ, 2=มาร์คเป็น spam, 0=ข้าม): ")
                if action in ['1', '2']:
                    for comment in spam_comments:
                        if action == '1':
                            detector.delete_comment(comment['id'])
                        else:
                            detector.mark_as_spam(comment['id'])
        else:
            print("\nไม่พบความคิดเห็นในวิดีโอนี้")
    except Exception as e:
        print(f"\nเกิดข้อผิดพลาด: {str(e)}")

def test_url_only():
    """โหมดทดสอบด้วย URL อย่างเดียว"""
    url = input("\nใส่ URL ของวิดีโอ YouTube: ")
    try:
        # สร้าง detector ในโหมดทดสอบ
        detector = YouTubeSpamDetector(None, test_mode=True)
        
        # ดึงข้อมูลจากหน้าเว็บ
        print("\nกำลังดึงข้อมูลความคิดเห็น...")
        response = requests.get(url)
        response.raise_for_status()
        
        # ดึง comments จากหน้าเว็บ
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        
        # ค้นหา script ที่มี comments data
        pattern = r'ytInitialData = ({.*?});'
        script = re.search(pattern, html)
        if script:
            data = json.loads(script.group(1))
            comments = []
            
            # ดึง comments จาก ytInitialData
            try:
                items = data['contents']['twoColumnWatchNextResults']['results']['results']['contents']
                for item in items:
                    if 'commentThreadRenderer' in str(item):
                        comment_thread = item['commentThreadRenderer']
                        comment = comment_thread['comment']['commentRenderer']['contentText']['runs'][0]['text']
                        comments.append(comment)
            except (KeyError, IndexError):
                pass
            
            # วิเคราะห์ comments ที่พบ
            if comments:
                total_comments = len(comments)
                spam_comments = []
                
                print(f"\nกำลังวิเคราะห์ความคิดเห็นทั้งหมด {total_comments} ข้อความ...")
                print("-" * 60)
                
                for i, comment in enumerate(comments, 1):
                    print(f"\nกำลังตรวจสอบความคิดเห็นที่ {i}/{total_comments}")
                    if detector.is_spam(comment):
                        spam_comments.append(comment)
                        print("🚫 พบ Spam!")
                    else:
                        print("✅ ไม่ใช่ Spam")
                
                spam_count = len(spam_comments)
                spam_percentage = (spam_count / total_comments * 100) if total_comments > 0 else 0
                
                print(f"\n📊 ผลการวิเคราะห์:")
                print(f"💬 จำนวนความคิดเห็นทั้งหมด: {total_comments}")
                print(f"🚫 จำนวน Spam: {spam_count}")
                print(f"📈 เปอร์เซ็นต์ Spam: {spam_percentage:.1f}%")
                
                if spam_comments:
                    print("\n🚫 ความคิดเห็นที่เป็น Spam ทั้งหมด:")
                    for i, comment in enumerate(spam_comments, 1):
                        print(f"\n{i}. {comment}")
            else:
                print("\nไม่พบความคิดเห็นในวิดีโอนี้")
                
        else:
            print("\nไม่สามารถดึงข้อมูลความคิดเห็นได้")
            
    except Exception as e:
        print(f"\nเกิดข้อผิดพลาด: {str(e)}")

def main():
    print("\n=== YouTube Comment Spam Analyzer ===")
    
    # โหลดและตั้งค่า
    config_manager = ConfigManager()
    
    print("1. ใช้งานระบบเต็มรูปแบบ")
    print("2. ทดสอบตรวจจับ Spam (ไม่ต้องใช้ API key)")
    print("3. ดูความคิดเห็นจาก URL")
    
    mode = input("\nเลือกโหมดการใช้งาน (1-3): ")
    
    if mode == '1':
        # โหมดเต็มรูปแบบ
        youtube_api = config_manager.setup_youtube_api()
        ai_config = config_manager.setup_ai_provider()
        
        config = {
            "youtube_api_key": youtube_api,
            "ai_provider": ai_config
        }
        
        try:
            detector = YouTubeSpamDetector(config)
            print("\nเริ่มต้นระบบสำเร็จ!")
            
            while True:
                print("\n=== เมนูหลัก ===")
                print("1. วิเคราะห์ความคิดเห็นจาก URL")
                print("2. ทดสอบข้อความ")
                print("3. ออกจากโปรแกรม")
                
                choice = input("\nเลือกเมนู (1-3): ")
                
                if choice == '1':
                    url = input("\nใส่ URL ของวิดีโอ YouTube: ")
                    analyze_video(detector, url)
                elif choice == '2':
                    test_single_comment(detector)
                elif choice == '3':
                    print("\nขอบคุณที่ใช้บริการ!")
                    break
                else:
                    print("\nกรุณาเลือกเมนู 1-3")
                    
        except Exception as e:
            print(f"\nเกิดข้อผิดพลาด: {str(e)}")
            print("โปรดตรวจสอบ API key และลองใหม่อีกครั้ง")
            
    elif mode == '2':
        # โหมดทดสอบ
        try:
            detector = YouTubeSpamDetector(None, test_mode=True)
            print("\nเริ่มต้นระบบทดสอบสำเร็จ!")
            
            while True:
                print("\n=== เมนูทดสอบ ===")
                print("1. ทดสอบข้อความ")
                print("2. ออกจากโปรแกรม")
                
                choice = input("\nเลือกเมนู (1-2): ")
                
                if choice == '1':
                    test_single_comment(detector)
                elif choice == '2':
                    print("\nขอบคุณที่ใช้บริการ!")
                    break
                else:
                    print("\nกรุณาเลือกเมนู 1-2")
                    
        except Exception as e:
            print(f"\nเกิดข้อผิดพลาด: {str(e)}")
    
    elif mode == '3':
        test_url_only()
    
    else:
        print("\nกรุณาเลือกโหมด 1-3")

if __name__ == "__main__":
    main() 
