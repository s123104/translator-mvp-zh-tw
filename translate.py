#!/usr/bin/env python3
import os
import sys
import json
import datetime
import argparse
import requests
from google.cloud import translate_v2 as translate
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()

# 使用 UTC 時間來判斷月份（避免本地時間偏差導致計費邏輯錯亂）
utc_now = datetime.datetime.utcnow()
current_month = utc_now.strftime("%Y-%m")
# (DEBUG 訊息僅在測試模式下由 main() 印出)

# 從環境變數取得 Microsoft Translator API 的金鑰與區域設定
MS_KEY = os.getenv("MS_TRANSLATOR_KEY")
MS_REGION = os.getenv("MS_TRANSLATOR_REGION")
# 取得 Google Cloud Translation API 的憑證檔路徑
GOOGLE_CRED = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if not MS_KEY:
    print("錯誤：未設定 Microsoft Translator API 金鑰，請檢查 .env 檔案")
    sys.exit(1)
if not GOOGLE_CRED:
    print("錯誤：未設定 Google Cloud Translation 憑證路徑，請檢查 .env 檔案")
    sys.exit(1)

# 定義免費額度與 90% 門檻值
MS_FREE_LIMIT = 2000000         # Microsoft 每月免費 2,000,000 字符
GOOGLE_FREE_LIMIT = 500000       # Google 每月免費 500,000 字符
MS_THRESHOLD = int(MS_FREE_LIMIT * 0.9)       # 約 1,800,000 字符
GOOGLE_THRESHOLD = int(GOOGLE_FREE_LIMIT * 0.9)  # 約 450,000 字符

# state.json 檔案（用來累計使用量）
state_file = "state.json"

def load_state():
    """
    載入 state.json，如果發現跨月（以 UTC 判斷）則重置免費額度。
    """
    if os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
        if state.get("month") != current_month:
            state = {"month": current_month, "microsoft_usage": 0, "google_usage": 0}
    else:
        state = {"month": current_month, "microsoft_usage": 0, "google_usage": 0}
    return state

def save_state(state):
    """
    將 state 寫回 state.json。
    """
    try:
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"警告：更新 {state_file} 時發生錯誤: {e}")

def translate_with_microsoft(text: str) -> str:
    """
    使用 Microsoft Translator API 將英文翻譯成繁體中文。
    """
    base_url = os.getenv("TRANSLATOR_TEXT_ENDPOINT", "https://api.cognitive.microsofttranslator.com")
    url = f"{base_url}/translate?api-version=3.0&from=en&to=zh-Hant"
    headers = {"Ocp-Apim-Subscription-Key": MS_KEY}
    if MS_REGION:
        headers["Ocp-Apim-Subscription-Region"] = MS_REGION
    body = [{"text": text}]
    try:
        response = requests.post(url, headers=headers, json=body, timeout=5)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Microsoft 翻譯請求錯誤: {e}")
        return None
    try:
        data = response.json()
        translated_text = data[0]["translations"][0]["text"]
    except (IndexError, KeyError) as e:
        print(f"解析 Microsoft 翻譯結果時發生錯誤: {e}")
        return None
    return translated_text

def translate_with_google(text: str, debug: bool = False) -> str:
    """
    使用 Google Cloud Translation API 將英文翻譯成繁體中文。
    若 debug=True，則印出詳細 debug 訊息。
    """
    try:
        client = translate.Client()  # 從 GOOGLE_APPLICATION_CREDENTIALS 載入憑證
        if debug:
            print("[DEBUG] Google 客戶端初始化成功")
    except Exception as e:
        print(f"Google 翻譯用戶端初始化失敗: {e}")
        return None
    try:
        result = client.translate(text, target_language="zh-TW", source_language="en")
        if debug:
            print("[DEBUG] Google API 回傳結果:", result)
    except Exception as e:
        print(f"Google 翻譯請求錯誤: {e}")
        return None
    return result.get("translatedText")

def main():
    parser = argparse.ArgumentParser(description="英文翻譯繁體中文 MVP 專案")
    parser.add_argument("text", nargs="*", help="待翻譯的英文文本")
    # 模式選項：正式模式 production（預設）或 test-google（測試 Google 翻譯，顯示 DEBUG 訊息，強制使用 Google）
    parser.add_argument("--mode", choices=["production", "test-google"], default="production",
                        help="執行模式：production（正式模式）或 test-google（測試 Google 翻譯，顯示 DEBUG 訊息，強制使用 Google）")
    args = parser.parse_args()

    # 判斷是否啟用 debug，test-google 模式下 debug 為 True
    debug = (args.mode == "test-google")

    if args.text:
        english_text = " ".join(args.text)
    else:
        english_text = input("請輸入要翻譯的英文文本: ")

    # 載入累計使用量狀態
    state = load_state()

    # 在 test-google 模式下，強制選用 Google 翻譯 (不考慮 Microsoft 使用量)
    if debug:
        print("==== 測試模式：強制使用 Google 翻譯（DEBUG 模式） ====")
        # 印出 debug 時間資訊
        print(f"[DEBUG] UTC 現在時間：{utc_now.isoformat()}")
        print(f"[DEBUG] 當前月份 (UTC)：{current_month}")
        use_ms = False
    else:
        # 正式模式根據累計使用量自動選擇 API
        use_ms = True
        if state["microsoft_usage"] >= MS_THRESHOLD and state["google_usage"] < GOOGLE_THRESHOLD:
            use_ms = False

    translated_text = None
    if use_ms:
        translated_text = translate_with_microsoft(english_text)
        service_used = "microsoft_usage"
    else:
        translated_text = translate_with_google(english_text, debug=debug)
        service_used = "google_usage"

    if translated_text is not None:
        # 輸出翻譯結果，正式模式和測試模式均印出
        print(f"翻譯結果: {translated_text}")
    else:
        sys.exit(1)

    # 更新使用量：依據原英文字符數累計，不論模式皆更新 state.json
    state[service_used] += len(english_text)
    save_state(state)

if __name__ == "__main__":
    main()
