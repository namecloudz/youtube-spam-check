import re
import requests
import json
import os
from datetime import datetime

class YouTubeSpamDetector:
    def __init__(self, config, test_mode=False):
        """
        config: dict จาก ConfigManager
        test_mode: bool สำหรับโหมดทดสอบ
        """
        self.test_mode = test_mode
        if not test_mode:
            self.api_key = config["youtube_api_key"]
            if not self.api_key:
                raise ValueError("กรุณาระบุ YouTube API key")
        
        # ตั้งค่า AI provider
        self.ai_config = config["ai_provider"]
        self.llm_url = self.ai_config["url"]
        
        self.spam_db_file = "spam_patterns_db.json"
        self.load_spam_patterns()
        
    def load_spam_patterns(self):
        """โหลด patterns จากฐานข้อมูล"""
        try:
            if os.path.exists(self.spam_db_file):
                with open(self.spam_db_file, 'r', encoding='utf-8') as f:
                    self.spam_patterns = json.load(f)
            else:
                self.spam_patterns = []
                self.save_spam_patterns()
        except Exception as e:
            print(f"ไม่สามารถโหลดฐานข้อมูลได้: {e}")
            self.spam_patterns = []

    def save_spam_patterns(self):
        """บันทึก patterns ลงฐานข้อมูล"""
        try:
            with open(self.spam_db_file, 'w', encoding='utf-8') as f:
                json.dump(self.spam_patterns, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"ไม่สามารถบันทึกฐานข้อมูลได้: {e}")

    def add_new_pattern(self, text, pattern_type="gambling"):
        """เพิ่ม pattern ใหม่ลงฐานข้อมูล"""
        # ตรวจสอบว่ามี pattern นี้อยู่แล้วหรือไม่
        if not any(p['pattern'] == text for p in self.spam_patterns):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_pattern = {
                "pattern": text,
                "type": pattern_type,
                "added_date": timestamp
            }
            self.spam_patterns.append(new_pattern)
            self.save_spam_patterns()
            print(f"\n🔄 เพิ่ม pattern ใหม่: {text}")

    def analyze_with_llm(self, text):
        """วิเคราะห์ข้อความด้วย LLM"""
        try:
            prompt = f"""กรุณาวิเคราะห์ข้อความนี้ว่าเป็นการโฆษณาเว็บพนันหรือไม่:

            ข้อความ: {text}

            ตอบในรูปแบบนี้เท่านั้น:
            คะแนน: [0-100] (ให้คะแนนความน่าจะเป็นโฆษณาเว็บพนัน)
            ผลวิเคราะห์: [สแปม/ไม่ใช่สแปม/ไม่แน่ใจ]
            เหตุผล: [อธิบายเหตุผลประกอบการวิเคราะห์]

            หมายเหตุ: กรุณาตอบเป็นภาษาไทยเท่านั้น ไม่ต้องใส่ข้อความอื่นนอกเหนือจากที่กำหนด
            """

            # สร้าง payload ตาม provider
            if self.ai_config["name"] == "ollama":
                payload = {
                    "model": self.ai_config["model"],
                    "messages": [
                        {"role": "system", "content": "คุณเป็น AI ที่ช่วยวิเคราะห์ข้อความภาษาไทย ตอบเป็นภาษาไทยเท่านั้น"},
                        {"role": "user", "content": prompt}
                    ]
                }
            elif self.ai_config["name"] == "openai":
                payload = {
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": "คุณเป็น AI ที่ช่วยวิเคราะห์ข้อความภาษาไทย ตอบเป็นภาษาไทยเท่านั้น"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 200
                }
            elif self.ai_config["name"] == "deepseek":
                payload = {
                    "model": self.ai_config["model"],
                    "messages": [
                        {"role": "system", "content": "คุณเป็น AI ที่ช่วยวิเคราะห์ข้อความภาษาไทย ตอบเป็นภาษาไทยเท่านั้น"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 200
                }
            elif self.ai_config["name"] == "grok":
                payload = {
                    "model": self.ai_config["model"],
                    "messages": [
                        {"role": "system", "content": "คุณเป็น AI ที่ช่วยวิเคราะห์ข้อความภาษาไทย ตอบเป็นภาษาไทยเท่านั้น"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 200,
                    "stream": False
                }
            else:
                # LM Studio และ providers อื่นๆ
                payload = {
                    "messages": [
                        {"role": "system", "content": "คุณเป็น AI ที่ช่วยวิเคราะห์ข้อความภาษาไทย ตอบเป็นภาษาไทยเท่านั้น"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 200
                }

            # เพิ่ม headers ตาม provider
            headers = {
                "Content-Type": "application/json"
            }
            if "api_key" in self.ai_config:
                if self.ai_config["name"] == "grok":
                    headers["Authorization"] = self.ai_config["api_key"]  # Grok ใช้ key โดยตรง
                else:
                    headers["Authorization"] = f"Bearer {self.ai_config['api_key']}"

            # ส่ง request
            try:
                response = requests.post(self.llm_url, json=payload, headers=headers)
                response.raise_for_status()
                
                # แยกการอ่านผลลัพธ์ตาม provider
                if self.ai_config["name"] == "ollama":
                    full_answer = response.json()['message']['content'].strip()
                else:
                    full_answer = response.json()['choices'][0]['message']['content'].strip()

            except requests.exceptions.RequestException as e:
                print(f"❌ ไม่สามารถเชื่อมต่อกับ {self.ai_config['name'].upper()} ได้")
                if hasattr(e.response, 'text'):
                    print(f"เหตุผล: {e.response.text}")
                if self.ai_config["name"] == "grok":
                    print("โปรดตรวจสอบ API Key และ model name ที่ถูกต้องจาก Grok")
                return None

            # ลบข้อความที่ไม่ต้องการออก
            full_answer = re.sub(r'<\|im_start\|>|<\|im_end\|>|上下文|assistant|user', '', full_answer)
            
            # แยกส่วนประกอบของคำตอบ
            lines = [line.strip() for line in full_answer.split('\n') if line.strip()]
            ai_score = 0
            ai_result = "ไม่แน่ใจ"
            ai_reason = ""
            
            for line in lines:
                if line.startswith("คะแนน:"):
                    try:
                        ai_score = int(re.search(r'\d+', line).group())
                    except:
                        ai_score = 0
                elif line.startswith("ผลวิเคราะห์:"):
                    result_text = line.split(":", 1)[1].strip().lower()
                    if "สแปม" in result_text:
                        ai_result = "สแปม"
                    elif "ไม่ใช่" in result_text:
                        ai_result = "ไม่ใช่สแปม"
                    else:
                        ai_result = "ไม่แน่ใจ"
                elif line.startswith("เหตุผล:"):
                    ai_reason = line.split(":", 1)[1].strip()
            
            # แสดงผลการวิเคราะห์
            print(f"💡 คะแนนจาก AI: {ai_score}/100")
            print(f"🤖 ผลวิเคราะห์: {ai_result}")
            if ai_reason:
                print(f"💬 เหตุผล: {ai_reason}")
            
            # ถ้าเป็น spam ให้เพิ่มลงฐานข้อมูล
            if ai_score >= 80 and len(text) > 10:
                self.add_new_pattern(text)
                return True
            elif ai_score > 50:
                return True
            elif ai_score <= 20:
                return False
            else:
                return None if ai_result == "ไม่แน่ใจ" else (ai_result == "สแปม")
            
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาด: {str(e)}")
            return None

    def is_spam(self, comment):
        """ตรวจสอบว่าข้อความเป็น spam หรือไม่"""
        print(f"\n🔍 กำลังวิเคราะห์: {comment[:100]}...")
        
        # เริ่มต้นด้วย score = 0
        pattern_score = 0
        matched_patterns = []
        
        # ตรวจสอบด้วย patterns spam
        for pattern_obj in self.spam_patterns:
            pattern = pattern_obj['pattern']
            pattern_type = pattern_obj['type']
            try:
                if re.search(pattern, comment):
                    if pattern_type == "gambling_site_name":
                        pattern_score += 3
                    elif pattern_type == "gambling_keywords":
                        pattern_score += 2
                    else:
                        pattern_score += 1
                    matched_patterns.append(pattern)
            except Exception as e:
                continue
        
        # ตรวจสอบ patterns พื้นฐาน
        if self._check_basic_spam_patterns(comment):
            pattern_score += 2
            matched_patterns.append("basic_spam_pattern")
        
        # แสดงผลการตรวจสอบเบื้องต้น
        if matched_patterns:
            print(f"⚠️ พบ patterns ที่ตรงกัน {len(matched_patterns)} รูปแบบ")
            print(f"📊 Pattern Score: {pattern_score}")
        
        # ถ้าคะแนนต่ำ (0) และข้อความสั้น ถือว่าไม่ใช่ spam
        if pattern_score == 0 and len(comment.split()) < 20:
            print("✅ ไม่พบรูปแบบที่น่าสงสัย")
            return False
        
        # ให้ AI ช่วยวิเคราะห์ทุกกรณีที่มี pattern score ตั้งแต่ 1 ขึ้นไป
        if pattern_score > 0:
            print("🤖 ใช้ AI ตรวจสอบเพิ่มเติม...")
            llm_result = self.analyze_with_llm(comment)
            
            if llm_result is True:
                print("🚫 AI ยืนยันว่าเป็น Spam!")
                return True
            elif llm_result is False:
                print("✅ AI ยืนยันว่าไม่ใช่ Spam")
                return False
            else:
                # ถ้า AI ไม่แน่ใจ ให้ใช้ pattern score ตัดสิน
                is_spam = pattern_score >= 2
                print(f"❓ AI ไม่แน่ใจ {'🚫 ถือว่าเป็น Spam' if is_spam else '✅ ถือว่าไม่ใช่ Spam'} (ใช้ Pattern Score ตัดสิน)")
                return is_spam
        
        return False
    
    def preprocess_text(self, text):
        """ทำความสะอาดข้อความและแปลงอักขระพิเศษ"""
        # แปลงอักขระพิเศษเป็นตัวอักษรปกติ
        special_chars_map = {
            # ตัวอักษรพิเศษแบบคล้ายตัวพิมพ์ใหญ่
            '𝐀-𝐙': 'A-Z', '𝕬-𝖅': 'A-Z', '𝔸-𝕐': 'A-Z',
            '𝒜-𝒵': 'A-Z', '𝓐-𝓩': 'A-Z', 'Ａ-Ｚ': 'A-Z',
            
            # ตัวอักษรพิเศษแบบคล้ายตัวพิมพ์เล็ก
            '𝐚-𝐳': 'a-z', '𝕒-𝕫': 'a-z', '𝖆-𝖟': 'a-z',
            '𝒶-𝓏': 'a-z', '𝓪-𝔃': 'a-z', 'ａ-ｚ': 'a-z',
            '𝙖-𝙯': 'a-z', '𝚊-𝚣': 'a-z', 
            
            # ตัวเลขพิเศษ
            '𝟎-𝟗': '0-9', '𝟘-𝟡': '0-9', '０-９': '0-9',
            '𝟢-𝟫': '0-9', '𝟬-𝟵': '0-9', '𝟶-𝟿': '0-9',
            
            # สัญลักษณ์พิเศษ
            '＠': '@', '＿': '_', '．': '.',
            '👉': ' ', '🔥': ' ', '🎮': ' ',
            '💎': ' ', '💰': ' ', '💵': ' ',
            '🎲': ' ', '🎯': ' ', '🎰': ' ',
        }
        
        # แทนที่อักขระพิเศษ
        for special, normal in special_chars_map.items():
            text = re.sub(f'[{special}]', lambda m: normal[0], text)
        
        # แปลงตัวอักษรพิเศษที่ไม่อยู่ในช่วง
        text = re.sub(r'[𝐀-𝐙𝕬-𝖅𝔸-𝕐]', lambda m: chr(ord('A') + (ord(m.group()) - ord('𝐀'))), text)
        text = re.sub(r'[𝐚-𝐳𝕒-𝕫𝖆-𝖟]', lambda m: chr(ord('a') + (ord(m.group()) - ord('𝐚'))), text)
        text = re.sub(r'[𝟎-𝟡]', lambda m: str(ord(m.group()) - ord('𝟎')), text)
        
        # ทำความสะอาดข้อความ แต่เก็บอักขระสำคัญไว้
        text = re.sub(r'[^\w\s@._]', '', text)
        text = text.lower().strip()
        return text

    def _check_basic_spam_patterns(self, comment):
        """ตรวจสอบรูปแบบพื้นฐานของ spam"""
        # ทำความสะอาดข้อความก่อน
        cleaned_comment = self.preprocess_text(comment)
        
        patterns = [
            # รูปแบบ ID/เบอร์ติดต่อ
            r'(?i)[@＠][a-z0-9._]+',  # รูปแบบ ID
            r'(?i)(?:line|ไลน์|id|ไอดี|แอด)[\s]*?[:\s]*?[@＠]?[a-z0-9._]+',  # Line ID
            
            # ตัวเลขและสัญลักษณ์เงิน
            r'(?i)(?:ฝาก|เล่น).*?[0-9๐-๙]+.*?(?:บาท|฿|บ)',
            r'(?i)[0-9๐-๙]+.*?(?:บาท|฿|บ).*?(?:ฝาก|เล่น)',
            
            # คำที่เกี่ยวกับการพนัน (รวมรูปแบบอักขระพิเศษ)
            r'(?i)(สล็อต|บาคาร่า|คาสิโน|เว็[บพ]พนัน|sa\s*gaming)',
            r'(?i)(เว็[บพ]ตรง.*?(?:ฝาก.*?ถอน|ถอน.*?ฝาก))',
            r'(?i)(เครดิต.*?ฟรี.*?(?:สล็อต|บาคาร่า|คาสิโน|เว็[บพ]))',
            
            # รูปแบบที่ใช้หลบเลี่ยงการตรวจจับ
            r'(?i)[a-z0-9๐-๙]*?[^\w\s]*?(?:สล็อต|บาคาร่า|คาสิโน)[^\w\s]*?[a-z0-9๐-๙]*',
            r'(?i)[@＠][a-z0-9._]+[^\w\s]*?(?:สล็อต|บาคาร่า|คาสิโน)',
            r'(?i)(?:[0-9๐-๙]+[^a-z0-9\s]{1,2}){2,}',  # ตัวเลขสลับกับสัญลักษณ์
        ]
        
        # ตรวจสอบทั้งข้อความดิบและข้อความที่ทำความสะอาดแล้ว
        return any(re.search(pattern, comment) for pattern in patterns) or \
               any(re.search(pattern, cleaned_comment) for pattern in patterns)

    def delete_comment(self, comment_id):
        """ลบความคิดเห็น"""
        if not self.api_key or self.test_mode:
            print("❌ ไม่สามารถลบความคิดเห็นได้ในโหมดทดสอบ")
            return False
        
        try:
            url = "https://www.googleapis.com/youtube/v3/comments"
            params = {
                'id': comment_id,
                'key': self.api_key
            }
            
            response = requests.delete(url, params=params)
            response.raise_for_status()
            
            print(f"✅ ลบความคิดเห็น {comment_id} สำเร็จ")
            return True
        
        except Exception as e:
            print(f"❌ ไม่สามารถลบความคิดเห็นได้: {str(e)}")
            return False

    def mark_as_spam(self, comment_id):
        """มาร์คความคิดเห็นเป็น spam"""
        if not self.api_key or self.test_mode:
            print("❌ ไม่สามารถมาร์ค spam ได้ในโหมดทดสอบ")
            return False
        
        try:
            url = "https://www.googleapis.com/youtube/v3/comments/markAsSpam"
            params = {
                'id': comment_id,
                'key': self.api_key
            }
            
            response = requests.post(url, params=params)
            response.raise_for_status()
            
            print(f"✅ มาร์คความคิดเห็น {comment_id} เป็น spam สำเร็จ")
            return True
        
        except Exception as e:
            print(f"❌ ไม่สามารถมาร์ค spam ได้: {str(e)}")
            return False 