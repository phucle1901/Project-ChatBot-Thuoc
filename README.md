# Hệ Thống Chatbot Y Tế - Tư Vấn Thuốc Thông Minh

## 📋 Tổng Quan

Hệ thống chatbot y tế được thiết kế để tư vấn thông tin về thuốc một cách chính xác và cá nhân hóa. Chatbot sử dụng công nghệ RAG (Retrieval-Augmented Generation) kết hợp với bộ nhớ dài hạn để cung cấp câu trả lời phù hợp với từng người dùng.

## 🏗️ Kiến Trúc Hệ Thống

### Sơ Đồ Kiến Trúc
<img width="930" height="534" alt="Ảnh màn hình 2025-11-24 lúc 23 56 27" src="https://github.com/user-attachments/assets/cf4d36ed-ea30-42c5-a5db-add911eb8eef" />




## 🔄 Luồng Hoạt Động Chi Tiết

### 1. **Frontend - Giao Diện Người Dùng** 
📁 `frontend/gradio.ipynb`

- Sử dụng **Gradio ChatInterface** để tạo giao diện chat thân thiện
- Nhận câu hỏi từ người dùng
- Gọi API backend để xử lý câu hỏi
- Hiển thị câu trả lời cho người dùng

**Tính năng:**
- Hỗ trợ lịch sử hội thoại
- Giao diện tùy chỉnh với theme chuyên nghiệp
- Hiển thị logging và error handling

---

### 2. **Backend Orchestrator** 
📁 `backend/chatbot_main.py`

Đây là trung tâm điều phối của hệ thống, thực hiện các bước sau:

#### **Bước 1: Xử Lý Song Song (Parallel Processing)**
Sử dụng `ThreadPoolExecutor` để chạy đồng thời 3 tác vụ:

**a) Cập Nhật Bộ Nhớ Dài Hạn (Long-Term Memory - LTM)**
- 📁 `backend/chatbots/chatbot_update_ltm.py`
- Phân tích câu hỏi để trích xuất thông tin về người dùng
- Thông tin bao gồm: tuổi tác, giới tính, bệnh lý, dị ứng, thuốc đang dùng, etc.
- So sánh với bộ nhớ hiện tại để quyết định cập nhật
- Lưu vào file `backend/memory/long_term_memory.txt`

```python
# Flow cập nhật LTM:
User Query → Extract User Info → Check Need Update → Update Memory File
```

**b) Lấy Dữ Liệu Bộ Nhớ Dài Hạn**
- 📁 `backend/get_doc/get_long_term.py`
- Đọc thông tin người dùng từ `long_term_memory.txt`
- Cung cấp context cá nhân hóa cho câu trả lời

**c) Mở Rộng Câu Hỏi (Query Expansion)**
- 📁 `backend/get_doc/expand_query.py`
- Sử dụng LLM để mở rộng câu hỏi gốc thành 2 câu hỏi:
  - Câu 1: Câu hỏi gốc
  - Câu 2: Câu hỏi mở rộng về thành phần/công dụng/liều lượng
- Mục đích: Tăng độ chính xác khi tìm kiếm tài liệu

**Ví dụ:**
```
Input: "Paracetamol dùng để làm gì?"
Output:
1. Paracetamol dùng để làm gì?
2. Paracetamol có thành phần chính là gì và công dụng chính là gì?
```

---

#### **Bước 2: Truy Xuất Tài Liệu (RAG - Retrieval)**
📁 `backend/get_doc/get_docs.py` + `backend/get_doc/rag.py`

**Quy trình:**
1. Sử dụng các câu hỏi đã mở rộng để tìm kiếm trong vector database
2. Vector Database: **Qdrant Cloud**
3. Embedding Model: **Google Generative AI Embeddings (text-embedding-004)**
4. Tìm kiếm similarity với ngưỡng: `score_threshold=0.7`
5. Lấy top 1 document cho mỗi query
6. Loại bỏ các document trùng lặp

**Cấu hình Qdrant:**
```python
- Collection: "embedding_data"
- Search Type: similarity_score_threshold
- Top K: 1 per query
- Score Threshold: 0.7
```

---

#### **Bước 3: Tóm Tắt Tài Liệu (Document Summarization)**
📁 `backend/chatbots/chatbot_summary.py`

**Điều kiện kích hoạt:**
- Khi tổng độ dài các document > 10,000 ký tự

**Mục đích:**
- Tránh vượt quá giới hạn token của LLM
- Giữ lại thông tin quan trọng nhất
- Tối ưu chi phí API

---

#### **Bước 4: Tạo Câu Trả Lời (LLM Response Generation)**

**Prompt Template:**
```
System: Bạn là một chuyên gia tư vấn về thuốc và y tế.

Input:
- Câu hỏi của người dùng
- Dữ liệu bộ nhớ dài hạn (thông tin cá nhân)
- Tài liệu tham khảo (từ RAG)

Output: Câu trả lời chính xác, chi tiết, cá nhân hóa
```

**LLM Model:** OpenAI GPT-4

---

## 📊 Dữ Liệu và Vector Database

### **Nguồn Dữ Liệu**
📁 `drugs-data-main/data/details/`

Dữ liệu thuốc được phân loại theo danh mục:
- Cơ xương khớp
- Thuốc bổ & vitamin
- Thuốc da liễu
- Thuốc dị ứng
- Thuốc giảm đau, hạ sốt, kháng viêm
- Thuốc hệ thần kinh
- Thuốc hô hấp
- Thuốc kháng sinh, kháng nấm
- Thuốc Mắt, Tai, Mũi, Họng
- Thuốc tiêm chích & dịch truyền
- Thuốc tiết niệu - sinh dục
- Thuốc tiêu hóa & gan mật
- Thuốc tim mạch & máu
- Thuốc trị tiểu đường
- Thuốc ung thư
- Và nhiều danh mục khác...

### **Quy Trình Tạo Embeddings**
📁 `embedding.py` + `embedding_to_qdrant.py`

```
JSON Files → Parse Data → Create Documents → Generate Embeddings → Store in Qdrant
```

**Class DrugEmbedding:**
1. Đọc các file JSON từ thư mục `details/`
2. Kết hợp các thuộc tính thuốc thành văn bản
3. Tạo embeddings bằng Google Generative AI
4. Lưu vào Qdrant Cloud

---

## 🔍 Tính Năng Nổi Bật

### **1. Bộ Nhớ Dài Hạn (Long-Term Memory)**
- Lưu trữ thông tin cá nhân của người dùng
- Tự động cập nhật thông minh
- Cá nhân hóa câu trả lời dựa trên đặc điểm người dùng

### **2. Query Expansion**
- Mở rộng câu hỏi để tăng độ chính xác
- Tìm kiếm đa chiều trong database

### **3. Parallel Processing**
- Xử lý song song 3 tác vụ để tối ưu thời gian phản hồi
- Sử dụng ThreadPoolExecutor

### **4. Document Summarization**
- Tự động tóm tắt khi tài liệu quá dài
- Tối ưu chi phí và hiệu suất

### **5. Tracing và Monitoring**
📁 `backend/tracing.py`
- Sử dụng OpenTelemetry để theo dõi performance
- Logging chi tiết cho mỗi bước

---

## 🛠️ Công Nghệ Sử Dụng

### **Backend**
- **LangChain**: Framework xây dựng ứng dụng LLM
- **OpenAI GPT-4**: Model ngôn ngữ chính
- **Google Generative AI**: Embedding model
- **Qdrant Cloud**: Vector database
- **Python Threading**: Xử lý song song

### **Frontend**
- **Gradio**: Thư viện tạo giao diện web

### **Monitoring**
- **OpenTelemetry**: Distributed tracing
- **Logging**: Python logging module

---

## 📁 Cấu Trúc Thư Mục

```
project/
├── backend/
│   ├── chatbot_main.py           # Orchestrator chính
│   ├── tracing.py                 # OpenTelemetry setup
│   ├── chatbots/
│   │   ├── chatbot_summary.py     # Tóm tắt tài liệu
│   │   └── chatbot_update_ltm.py  # Cập nhật bộ nhớ dài hạn
│   ├── get_doc/
│   │   ├── expand_query.py        # Mở rộng câu hỏi
│   │   ├── get_docs.py            # Lấy documents
│   │   ├── get_long_term.py       # Đọc LTM
│   │   └── rag.py                 # RAG với Qdrant
│   └── memory/
│       └── long_term_memory.txt   # Lưu trữ LTM
├── frontend/
│   └── gradio.ipynb               # Giao diện Gradio
├── drugs-data-main/
│   ├── data/
│   │   ├── details/               # Dữ liệu thuốc (JSON)
│   │   └── urls/                  # URLs nguồn
│   └── main.py                    # Scraper dữ liệu
├── embedding.py                   # Tạo embeddings
├── embedding_to_qdrant.py         # Upload lên Qdrant
└── README.md                      # Tài liệu này
```

---

## 🚀 Hướng Dẫn Sử Dụng

### **1. Cài Đặt Môi Trường**

```bash
# Clone repository
git clone <repository-url>
cd project

# Cài đặt dependencies
pip install -r requirements.txt
```

### **2. Cấu Hình Environment Variables**

Tạo file `.env`:
```env
OPENAI_API_KEY=your_openai_api_key
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key
GOOGLE_API_KEY=your_google_api_key
```

### **3. Khởi Chạy Hệ Thống**

**Backend:**
```python
# Trong backend/chatbot_main.py
from chatbot_main import chatbot_response
response = chatbot_response.invoke("Paracetamol có tác dụng gì?")
```

**Frontend:**
```bash
# Chạy Jupyter notebook
jupyter notebook frontend/gradio.ipynb
# Sau đó chạy các cells
```

---

## 📸 Screenshots

### Tracing
<img width="1470" height="415" alt="Ảnh màn hình 2025-11-26 lúc 09 27 37" src="https://github.com/user-attachments/assets/dbaf899c-774c-4490-8909-49c481770f1f" />

### Logging
![Uploading Ảnh màn hình 2025-11-26 lúc 09.27.57.png…]()

---

## 🔐 Bảo Mật và Quyền Riêng Tư

- Thông tin cá nhân người dùng được lưu cục bộ trong `long_term_memory.txt`
- Không lưu trữ lịch sử chat lâu dài
- API keys được quản lý qua biến môi trường

---

## 📈 Tối Ưu Hóa Performance

1. **Parallel Processing**: 3 tác vụ chạy song song giảm thời gian phản hồi
2. **Caching**: Qdrant vector search nhanh với similarity search
3. **Smart Summarization**: Chỉ tóm tắt khi cần thiết
4. **Query Expansion**: Tăng độ chính xác mà không tăng số lần gọi API

---

## 🐛 Troubleshooting

### **Lỗi kết nối Qdrant:**
- Kiểm tra `QDRANT_URL` và `QDRANT_API_KEY`
- Tăng timeout nếu cần (hiện tại: 120s)

### **Lỗi OpenAI API:**
- Kiểm tra `OPENAI_API_KEY`
- Kiểm tra quota và billing

### **Lỗi Embedding:**
- Kiểm tra `GOOGLE_API_KEY`
- Đảm bảo model `text-embedding-004` có sẵn

---

## 📝 Ghi Chú Phát Triển

### **Các File Hỗ Trợ:**
- `delete_qdrant.py`: Xóa collection trong Qdrant
- `testchatbot.py`: Test chatbot cơ bản
- `drugs-data-main/main.py`: Scraper để thu thập dữ liệu thuốc

### **Tracing:**
Hệ thống sử dụng OpenTelemetry để theo dõi:
- Thời gian mỗi bước xử lý
- Lỗi và exceptions
- Flow của request

---

## 🎯 Hướng Phát Triển Tương Lai

1. **Multi-modal**: Thêm khả năng xử lý hình ảnh thuốc
2. **Voice Input**: Tích hợp speech-to-text
3. **History Management**: Quản lý lịch sử chat tốt hơn
4. **A/B Testing**: Test các prompt templates khác nhau
5. **Fine-tuning**: Fine-tune model trên dữ liệu y tế Việt Nam
6. **Mobile App**: Phát triển ứng dụng di động

---

## 👥 Đóng Góp

Mọi đóng góp đều được hoan nghênh! Vui lòng tạo issue hoặc pull request.

---

## 📄 License

[Thêm thông tin license của bạn]

---

## 📞 Liên Hệ

[Thêm thông tin liên hệ của bạn]

---

**Lưu ý:** Hệ thống này chỉ mang tính chất tham khảo. Luôn tham khảo ý kiến bác sĩ hoặc dược sĩ trước khi sử dụng thuốc.
