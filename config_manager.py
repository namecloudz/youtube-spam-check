import json
import os
import requests
from getpass import getpass

class ConfigManager:
    def __init__(self):
        self.config_file = "config.json"
        self.config = self.load_config()

    def load_config(self):
        """โหลดการตั้งค่าจากไฟล์"""
        config = {
            "youtube_api_keys": {},  # เปลี่ยนเป็น dict เก็บหลาย key ได้
            "current_youtube_key": "",  # key ที่ใช้งานปัจจุบัน
            "ai_providers": {
                "openai": {"api_key": "", "model": "gpt-3.5-turbo"},
                "deepseek": {"api_key": "", "model": "deepseek-chat"},
                "grok": {"api_key": "", "model": "grok-2"},
                "lmstudio": {"host": "localhost", "port": "1234"},
                "ollama": {"host": "localhost", "port": "11434", "model": "mistral"}
            },
            "current_provider": "lmstudio"
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    old_config = json.load(f)
                    
                    # อัพเกรดจากโครงสร้างเก่า
                    if "youtube_api_key" in old_config and old_config["youtube_api_key"]:
                        config["youtube_api_keys"]["default"] = old_config["youtube_api_key"]
                        config["current_youtube_key"] = "default"
                    
                    # คงค่าเดิมถ้ามีโครงสร้างใหม่แล้ว
                    if "youtube_api_keys" in old_config:
                        config["youtube_api_keys"] = old_config["youtube_api_keys"]
                    if "current_youtube_key" in old_config:
                        config["current_youtube_key"] = old_config["current_youtube_key"]
                    if "ai_providers" in old_config:
                        config["ai_providers"] = old_config["ai_providers"]
                    if "current_provider" in old_config:
                        config["current_provider"] = old_config["current_provider"]
                    
                    return config
            except:
                pass
        
        return config

    def save_config(self):
        """บันทึกการตั้งค่าลงไฟล์"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)

    def show_saved_settings(self):
        """แสดงการตั้งค่าที่บันทึกไว้"""
        print("\n=== การตั้งค่าที่บันทึกไว้ ===")
        
        # แสดง YouTube API Key
        if self.config['youtube_api_keys']:
            print("\nAPI Keys ที่บันทึกไว้:")
            for name, key in self.config["youtube_api_keys"].items():
                if name == self.config["current_youtube_key"]:
                    print(f"{name}: {key[:6]}... (กำลังใช้งาน)")
                else:
                    print(f"{name}: {key[:6]}...")
        else:
            print("YouTube API Key: ไม่ได้ตั้งค่า")
        
        # แสดงข้อมูล AI Providers
        print("\nAI Providers:")
        for provider, settings in self.config["ai_providers"].items():
            print(f"\n{provider.upper()}:")
            if "api_key" in settings and settings["api_key"]:
                print(f"  API Key: {settings['api_key'][:6]}...")
            if "model" in settings:
                print(f"  Model: {settings['model']}")
            if "host" in settings:
                print(f"  Host: {settings['host']}")
            if "port" in settings:
                print(f"  Port: {settings['port']}")

        print(f"\nProvider ที่ใช้งานอยู่: {self.config['current_provider'].upper()}")
        
        # เพิ่มตัวเลือกแสดง key เต็ม
        print("\nต้องการดู API Key เต็มหรือไม่?")
        print("1. แสดง API Key ทั้งหมด")
        print("2. ดำเนินการต่อ")
        choice = input("\nเลือกตัวเลือก (1-2): ")
        
        if choice == '1':
            print("\n=== API Keys ทั้งหมด ===")
            if self.config['youtube_api_keys']:
                print("\nAPI Keys ที่บันทึกไว้:")
                for name, key in self.config["youtube_api_keys"].items():
                    if name == self.config["current_youtube_key"]:
                        print(f"\n{name} (กำลังใช้งาน):")
                    else:
                        print(f"\n{name}:")
                    print(f"Key: {key}")
            
            input("\nกด Enter เพื่อดำเนินการต่อ...")

    def setup_youtube_api(self):
        """ตั้งค่า YouTube API"""
        print("\n=== YouTube API Keys ===")
        
        # แสดง keys ที่มีอยู่
        if self.config["youtube_api_keys"]:
            print("\nAPI Keys ที่บันทึกไว้:")
            for name, key in self.config["youtube_api_keys"].items():
                if name == self.config["current_youtube_key"]:
                    print(f"{name}: {key[:6]}... (กำลังใช้งาน)")
                else:
                    print(f"{name}: {key[:6]}...")
        
        print("\nตัวเลือก:")
        print("1. ใช้ API Key ที่บันทึกไว้")
        print("2. เพิ่ม API Key ใหม่")
        print("3. แสดง API Keys ทั้งหมด")
        print("4. ลบ API Key")
        choice = input("\nเลือกตัวเลือก (1-4): ")
        
        if choice == '1':
            if not self.config["youtube_api_keys"]:
                print("ไม่มี API Key ที่บันทึกไว้")
                return self.setup_youtube_api()
            
            print("\nเลือก API Key ที่ต้องการใช้:")
            keys = list(self.config["youtube_api_keys"].items())
            for i, (name, key) in enumerate(keys, 1):
                print(f"{i}. {name}: {key[:6]}...")
            
            try:
                key_choice = int(input("\nเลือกหมายเลข: "))
                if 1 <= key_choice <= len(keys):
                    name, key = keys[key_choice-1]
                    self.config["current_youtube_key"] = name
                    self.save_config()
                    return key
            except:
                print("เลือกไม่ถูกต้อง")
            return self.setup_youtube_api()
        
        elif choice == '2':
            name = input("\nตั้งชื่อให้ API Key (เช่น personal, work): ")
            while name in self.config["youtube_api_keys"]:
                print(f"มีชื่อ {name} อยู่แล้ว กรุณาตั้งชื่อใหม่")
                name = input("ตั้งชื่อให้ API Key: ")
            
            api_key = getpass("กรุณาใส่ YouTube API Key: ")
            self.config["youtube_api_keys"][name] = api_key
            self.config["current_youtube_key"] = name
            self.save_config()
            return api_key
        
        elif choice == '3':
            print("\n=== YouTube API Keys ทั้งหมด ===")
            for name, key in self.config["youtube_api_keys"].items():
                if name == self.config["current_youtube_key"]:
                    print(f"\n{name} (กำลังใช้งาน):")
                else:
                    print(f"\n{name}:")
                print(f"Key: {key}")
            input("\nกด Enter เพื่อดำเนินการต่อ...")
            return self.setup_youtube_api()
        
        elif choice == '4':
            if not self.config["youtube_api_keys"]:
                print("ไม่มี API Key ที่จะลบ")
                return self.setup_youtube_api()
            
            print("\nเลือก API Key ที่ต้องการลบ:")
            keys = list(self.config["youtube_api_keys"].items())
            for i, (name, key) in enumerate(keys, 1):
                print(f"{i}. {name}: {key[:6]}...")
            
            try:
                key_choice = int(input("\nเลือกหมายเลข: "))
                if 1 <= key_choice <= len(keys):
                    name, _ = keys[key_choice-1]
                    if name == self.config["current_youtube_key"]:
                        self.config["current_youtube_key"] = ""
                    del self.config["youtube_api_keys"][name]
                    self.save_config()
                    print(f"\nลบ API Key '{name}' แล้ว")
            except:
                print("เลือกไม่ถูกต้อง")
            return self.setup_youtube_api()
        
        return self.setup_youtube_api()

    def setup_ai_provider(self):
        """ตั้งค่า AI Provider"""
        print("\n=== เลือก AI Provider ===")
        self.show_saved_settings()
        
        print("\nเลือก Provider:")
        print("1. LM Studio")
        print("2. Ollama")
        print("3. OpenAI")
        print("4. Deepseek API")
        print("5. Grok API")
        
        choice = input("\nเลือก Provider (1-5): ")
        
        if choice == '1':
            return self.setup_lmstudio()
        elif choice == '2':
            return self.setup_ollama()
        elif choice == '3':
            return self.setup_openai()
        elif choice == '4':
            return self.setup_deepseek()
        elif choice == '5':
            return self.setup_grok()
        else:
            print("เลือกไม่ถูกต้อง ใช้ LM Studio เป็นค่าเริ่มต้น")
            return self.setup_lmstudio()

    def setup_lmstudio(self):
        """ตั้งค่า LM Studio"""
        print("\n=== LM Studio Setup ===")
        host = input("Host (กด Enter ใช้ localhost): ") or "localhost"
        port = input("Port (กด Enter ใช้ 1234): ") or "1234"
        
        config = {
            "name": "lmstudio",
            "host": host,
            "port": port,
            "url": f"http://{host}:{port}/v1/chat/completions"
        }
        
        self.config["ai_providers"]["lmstudio"] = config
        self.config["current_provider"] = "lmstudio"
        self.save_config()
        return config

    def setup_ollama(self):
        """ตั้งค่า Ollama"""
        print("\n=== Ollama Setup ===")
        host = input("Host (กด Enter ใช้ localhost): ") or "localhost"
        port = input("Port (กด Enter ใช้ 11434): ") or "11434"
        
        # ดึงรายชื่อ models
        try:
            url = f"http://{host}:{port}/api/tags"
            response = requests.get(url)
            models = [model['name'] for model in response.json()['models']]
            
            print("\nModels ที่มี:")
            for i, model in enumerate(models, 1):
                print(f"{i}. {model}")
            
            choice = int(input("\nเลือก Model (1-{len(models)}): "))
            model = models[choice-1] if 1 <= choice <= len(models) else "mistral"
        except:
            print("ไม่สามารถดึงรายชื่อ models ได้ ใช้ mistral เป็นค่าเริ่มต้น")
            model = "mistral"
        
        config = {
            "name": "ollama",
            "host": host,
            "port": port,
            "model": model,
            "url": f"http://{host}:{port}/api/chat"
        }
        
        self.config["ai_providers"]["ollama"] = config
        self.config["current_provider"] = "ollama"
        self.save_config()
        return config

    def setup_openai(self):
        """ตั้งค่า OpenAI"""
        print("\n=== OpenAI Setup ===")
        settings = self.config["ai_providers"]["openai"]
        
        if settings["api_key"]:
            print(f"API Key ที่บันทึกไว้: {settings['api_key'][:6]}...")
            print("1. ใช้ API Key ที่บันทึกไว้")
            print("2. ใส่ API Key ใหม่")
            choice = input("\nเลือกตัวเลือก (1-2): ")
            
            if choice == '1':
                self.config["current_provider"] = "openai"
                self.save_config()
                return {
                    "name": "openai",
                    "api_key": settings["api_key"],
                    "model": settings["model"],
                    "url": "https://api.openai.com/v1/chat/completions"
                }
        
        api_key = getpass("กรุณาใส่ OpenAI API Key: ")
        self.config["ai_providers"]["openai"]["api_key"] = api_key
        self.config["current_provider"] = "openai"
        self.save_config()
        
        return {
            "name": "openai",
            "api_key": api_key,
            "model": "gpt-3.5-turbo",
            "url": "https://api.openai.com/v1/chat/completions"
        }

    def setup_deepseek(self):
        """ตั้งค่า Deepseek"""
        print("\n=== Deepseek Setup ===")
        settings = self.config["ai_providers"]["deepseek"]
        
        if settings["api_key"]:
            print(f"API Key ที่บันทึกไว้: {settings['api_key'][:6]}...")
            print("1. ใช้ API Key ที่บันทึกไว้")
            print("2. ใส่ API Key ใหม่")
            choice = input("\nเลือกตัวเลือก (1-2): ")
            
            if choice == '1':
                self.config["current_provider"] = "deepseek"
                self.save_config()
                return {
                    "name": "deepseek",
                    "api_key": settings["api_key"],
                    "model": settings["model"],
                    "url": "https://api.deepseek.com/v1/chat/completions"
                }
        
        api_key = getpass("กรุณาใส่ Deepseek API Key: ")
        
        # เลือก model
        print("\nเลือก Model:")
        print("1. deepseek-chat")
        print("2. deepseek-coder")
        model_choice = input("เลือก Model (1-2): ")
        
        model = "deepseek-chat"
        if model_choice == "2":
            model = "deepseek-coder"
        
        self.config["ai_providers"]["deepseek"]["api_key"] = api_key
        self.config["ai_providers"]["deepseek"]["model"] = model
        self.config["current_provider"] = "deepseek"
        self.save_config()
        
        return {
            "name": "deepseek",
            "api_key": api_key,
            "model": model,
            "url": "https://api.deepseek.com/v1/chat/completions"
        }

    def setup_grok(self):
        """ตั้งค่า Grok"""
        print("\n=== Grok Setup ===")
        if self.config["ai_providers"]["grok"].get("api_key") and self.config["ai_providers"]["grok"].get("name") == "grok":
            print("1. ใช้ API Key ที่บันทึกไว้")
            print("2. ใส่ API Key ใหม่")
            choice = input("\nเลือกตัวเลือก (1-2): ")
            
            if choice == '1':
                return self.config["ai_providers"]["grok"]
        
        api_key = getpass("กรุณาใส่ Grok API Key: ")
        
        # เลือก model
        print("\nเลือก Model:")
        print("1. grok-2")
        print("2. grok-3")
        model_choice = input("เลือก Model (1-2): ")
        
        model = "grok-2"
        if model_choice == "2":
            model = "grok-3"
        
        self.config["ai_providers"]["grok"] = {
            "name": "grok",
            "api_key": api_key,
            "model": model,
            "url": "https://api.grok.x.ai/v1/chat/completions"
        }
        self.config["current_provider"] = "grok"
        self.save_config()
        return self.config["ai_providers"]["grok"] 