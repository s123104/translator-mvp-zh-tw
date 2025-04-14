# 英文翻譯繁體中文 MVP 專案

👉 本專案是一個使用 Microsoft 與 Google API 所製作的「英文 → 繁體中文」翻譯工具，具備免費額度自動切換與使用量追蹤功能，適合用於 CLI、自動翻譯工具與批次處理。

這是一個使用 Python 製作的 MVP（Minimal Viable Product）翻譯工具，能夠將英文翻譯成繁體中文。專案結合 **Microsoft Translator Text API** 與 **Google Cloud Translation API**，利用各自的免費額度自動切換 API，避免超出免費額度產生費用。系統會依據每月累計的翻譯字符數進行判斷，並在每月 UTC 的 1 號重置免費額度。

> **重點說明：**
>
> - **Microsoft Translator**：每月 2,000,000 字符免費（F0 免費層）
> - **Google Cloud Translation (Basic 版 v2)**：每月 500,000 字符免費  
>   當某一服務的使用量達到免費額度 90%（Microsoft 約 1,800,000 字，Google 約 450,000 字）時，程式會自動切換到另一服務，同時累計使用量會依照原文字符數更新到 `state.json`。

---

## 專案結構

```
translator_mvp/
├── key/                 # 存放所有 API 金鑰與憑證的資料夾（例如：translate-key.json ）
├── .env-example         # 範例環境變數設定檔
├── .gitignore           # Git 忽略設定（忽略虛擬環境、.env 與 state.json）
├── README.md            # 本文件：專案詳細說明
├── requirements.txt     # 必要套件列表（requests, google-cloud-translate, python-dotenv）
├── state.json           # 每月 API 使用量的狀態檔（程式自動生成、記錄累計字符數）
└── translate.py         # 主程式，包含詳細繁體中文註解與模式切換功能
```

**注意：** 你所有的金鑰與憑證（例如，Google JSON 金鑰）都放在 `translator_mvp/key/` 資料夾內。記得在 .env 文件中使用相對路徑指向這些金鑰檔案。

---

## 環境建置與準備

### 1. 安裝 Python

請確認你已安裝 Python 3.7 以上版本：

```bash
python3 --version
```

### 2. 建立虛擬環境

為避免套件衝突，建議建立虛擬環境：

```bash
python3 -m venv venv
```

啟動虛擬環境：

- **Linux/macOS**:
  ```bash
  source venv/bin/activate
  ```
- **Windows**:
  ```batch
  venv\Scripts\activate
  ```

### 3. 安裝必要套件

在虛擬環境中執行下列指令安裝所需套件：

```bash
pip install -r requirements.txt
```

`requirements.txt` 內容如下：

```
requests
google-cloud-translate
python-dotenv
```

---

## API 金鑰與憑證申請說明

### A. Microsoft Translator Text API

1. **建立 Azure 帳號**：  
   若你還沒有 Azure 帳號，請前往 [Azure 免費帳號申請頁面](https://azure.microsoft.com/free) 申請免費帳號，新用戶常有免費試用以及 F0 免費層級。

2. **建立 Translator 資源**：

   - 登入 [Azure Portal](https://portal.azure.com/) 後，點選「建立資源」。
   - 搜尋「Translator」或「Cognitive Services」內的 Translator 資源，然後選擇建立。
   - 在資源建立過程中注意：
     - **訂閱**：選擇你的訂閱。
     - **資源群組**：可使用現有資源群組，或自行建立一個，但注意資源群組的區域必須選擇支援 Translator API 的地區（例如 `eastasia`、`southeastasia`），**Global 不適用**。
     - **資源名稱**：例如 `MyTranslatorService`。
     - **區域**：請選擇 `eastasia` 或 `southeastasia`。
     - **定價層**：選擇 **F0（免費層）**，每月可免費翻譯 2,000,000 字符。
   - 建立成功後，部署可能需要數分鐘。

3. **取得金鑰與端點**：
   - 進入你建立的 Translator 資源頁面，點選左側的「金鑰與端點 (Keys and Endpoint)」。
   - 複製其中一個金鑰（例如 Key1），這就是你的 `MS_TRANSLATOR_KEY`。
   - 記下 **端點 URL**（例如 `https://api.cognitive.microsofttranslator.com/`）和資源所在區域（例如 `eastasia`）。

### B. Google Cloud Translation API (Basic 版)

1. **建立 Google Cloud 專案**：  
   登入 [Google Cloud Console](https://console.cloud.google.com/)，若無專案，請建立一個新的專案。

2. **啟用 Cloud Translation API**：

   - 在左側選單中點選「API 與服務」>「啟用 API 與服務」。
   - 搜尋「Cloud Translation API」，點選後啟用。請確認啟用的是 Basic 版 API（v2 版），此版本每月享有 500,000 字符免費配額。

3. **建立服務帳戶並下載憑證**：
   - 前往「API 與服務」>「憑證」。
   - 點選「建立憑證」>「服務帳戶」，按照指示建立服務帳戶，並授予 Cloud Translation API 使用權限。
   - 為服務帳戶建立一個 JSON 金鑰檔案，下載後保存至 `translator_mvp/key/` 內（例如，命名為 `translate-key.json`）。

---

## 環境變數設定 (.env 檔案)

請根據以下 `.env-example` 文件建立一個 `.env` 文件（此檔案已列入 .gitignore，不會上傳 GitHub）。

```ini
# .env-example
# 請將以下參數替換為你從 Azure 與 Google Cloud 取得的實際值

# Azure Translator API 設定
MS_TRANSLATOR_KEY=你的Azure訂閱金鑰
MS_TRANSLATOR_REGION=eastasia
TRANSLATOR_TEXT_ENDPOINT=https://api.cognitive.microsofttranslator.com/

# Google Cloud Translation API 設定
# 注意：金鑰檔案放在專案的 key/ 資料夾內，請使用相對路徑
GOOGLE_APPLICATION_CREDENTIALS=key/translate-key.json
```

---

## 使用方法

### 執行翻譯

在虛擬環境中、於專案根目錄執行：

```bash
python translate.py "Hello, how are you?"
```

系統會根據 `state.json` 中累計的 API 使用量自動選擇 Microsoft 或 Google 翻譯服務，並輸出翻譯結果（繁體中文）。

若執行 `python translate.py` 而無參數，程式將提示你輸入英文文本。

### 模式選項

本程式支援兩種模式（透過 `--mode` 參數設定），皆會更新累計使用量：

- **正式模式 (production, 預設)**  
  程式會根據累計使用量自動決定使用哪個 API，輸出乾淨的翻譯結果：

  ```bash
  python translate.py "Hello, how are you?"
  ```

- **測試模式 (test-google)**  
  強制使用 Google 翻譯，並印出詳細 DEBUG 訊息以便檢查 Google API 回應，同時也會更新累計使用量：
  ```bash
  python translate.py "Hello, how are you?" --mode test-google
  ```

---

## 常見問題與故障排除

- **環境變數未正確讀取**：  
  請確認專案根目錄已正確建立 `.env` 文件，且內容無誤。程式使用 [python-dotenv](https://pypi.org/project/python-dotenv/) 自動讀取 `.env`，注意這些變數只在 Python 程式中可用，不會影響 shell 環境。

- **API 金鑰／憑證錯誤**：  
  請重新檢查 `.env` 中的金鑰、區域以及 Google JSON 憑證的路徑是否正確，避免多餘空格或錯誤字元。

- **state.json 權限問題**：  
  確保專案目錄具有足夠權限寫入 `state.json`。如出現權限錯誤，請調整目錄權限或將專案移至有寫入權限的位置。

- **免費額度超限**：  
  請定期檢查 `state.json` 中的累計使用量，確保單月翻譯字符數不超出免費額度。當某 API 使用量達到免費額度 90% 時，程式會自動切換到另一服務；但若兩者均超出免費額度，後續請求可能會產生費用。

---

## 專案擴充與貢獻

- **擴充應用**：  
  本專案使用 `state.json` 記錄每月的翻譯字符數，你可以根據需求擴充功能，例如「剩餘免費額度查詢」介面、更多語言支持或其他 API 整合。

- **貢獻指南**：  
  歡迎 fork 此專案、提出問題或提交 pull request 來一起優化工具，共同打造更完善的翻譯解決方案！

---

## 授權

本專案以 [MIT 授權](https://opensource.org/licenses/MIT) 釋出。

---

希望這份詳細的說明能夠幫助你順利設置與運行翻譯工具，保障你在開發與串接過程中不出現計費上的意外！如有任何問題，歡迎發 issue 或聯絡，祝你開發愉快！
