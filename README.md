<img width="953" height="551" alt="Ảnh màn hình 2025-11-26 lúc 13 13 01" src="https://github.com/user-attachments/assets/499c3395-cd2d-4efb-8d8c-af366c78c79b" /># chatbotthuoc

## Tracing
<img width="1470" height="415" alt="Ảnh màn hình 2025-11-26 lúc 09 27 37" src="https://github-production-user-asset-6210df.s3.amazonaws.com/127717381/518957074-dbaf899c-774c-4490-8909-49c481770f1f.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAVCODYLSA53PQK4ZA%2F20251126%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20251126T054924Z&X-Amz-Expires=300&X-Amz-Signature=d7bcb945b458d56b418544c36e011b18beb47ce4c0c28ce4b11419a97e8c2cd2&X-Amz-SignedHeaders=host" />

## Loging
<img width="1039" height="364" alt="Ảnh màn hình 2025-11-26 lúc 09 32 50" src="https://github-production-user-asset-6210df.s3.amazonaws.com/127717381/518958300-bdf09176-6cff-4ff9-8cb7-fd255b227256.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAVCODYLSA53PQK4ZA%2F20251126%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20251126T054924Z&X-Amz-Expires=300&X-Amz-Signature=25292525db071af5dc40f8bf77b423d3373e8942004cfd9b560d4f1593ad4c22&X-Amz-SignedHeaders=host" />

## Architect
<img width="978" height="525" alt="Ảnh màn hình 2025-11-26 lúc 13 13 24" src="https://github.com/user-attachments/assets/339b93d8-107c-4bbf-b1b9-64faf25d8bfb" />


## Luồng hoạt động của hệ thống
#### **Bước 1: Xử Lý Song Song (Parallel Processing)**
Sử dụng `ThreadPoolExecutor` để chạy đồng thời 3 tác vụ:

**a) Cập Nhật Bộ Nhớ Dài Hạn (Long-Term Memory - LTM)**
- `backend/chatbots/chatbot_update_ltm.py`
- Ở bước này ta sẽ sử dụng LLM để kiểm tra xem query của người dùng có chưa thông tin nên được lưu vào LTM không( các thông tin như sở thích thói quen ,...)
- Nếu như ta phát hiện query chưa thống tin cần lưu thì ta cần kiểm tra trong bộ nhớ hiện tại đã có thông tin này chưa , nêu chưa có thì tiến hành cập nhật
# Flow cập nhật LTM:
User Query → Extract User Info → Check Need Update → Update Memory File
```

**b) Lấy Dữ Liệu Bộ Nhớ Dài Hạn**
- `backend/get_doc/get_long_term.py`
- Đọc thông tin người dùng từ `long_term_memory.txt`
- Cung cấp context cá nhân hóa cho câu trả lời

**c) Mở Rộng Câu Hỏi (Query Expansion)**
- `backend/get_doc/expand_query.py`
- Sử dụng LLM để mở rộng câu hỏi gốc thành 2 câu hỏi:
  - Câu 1: Câu hỏi gốc
  - Câu 2: Câu hỏi mở rộng về thành phần/công dụng/liều lượng
- Mục đích: Tăng độ chính xác khi tìm kiếm tài liệu

#### **Bước 2: Truy Xuất Tài Liệu (RAG - Retrieval)**
`backend/get_doc/get_docs.py` + `backend/get_doc/rag.py`

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

#### **Bước 3: Tổng hợp doc + longterm memory + short term memory **
-Sau khi lấy được các tài liệu retrival ở bước 2 , ta tiến hành kết hợp query ban đầu của người dùng + tài liệu truy vấn + long term memory và short term memory (short term memory ở đấy chính là lịch sử của cuộc hội thoại)
- Nếu như context sau khi tổng hợp vượt quá 1 số lượng ký tự thì sẽ gọi tới thành phần summury (ở đây em cho là không vươt qua 10000 từ ). Lý do em phải làm vậy là vì mô hinh chatbot ở đây em sử dụng nhận đầu vào không quá 16.384 token.

**Điều kiện kích hoạt:**
- Khi tổng độ dài các document > 10,000 từ

**Mục đích:**
- Tránh vượt quá giới hạn token của LLM
- Giữ lại thông tin quan trọng nhất


---

#### **Bước 4: Tạo Câu Trả Lời (LLM Response Generation)**
**LLM Model:** OpenAI GPT-4
Ở bước này ta sẽ gửi câu truy vấn lấy được từ bước 3 đến LLM
Sau khi nhận được câu phản hồi thì ta sẽ gửi output cho user đồng thời cập nhật short term memory (chính là lịch sử của đoạn hội thoại)
## Cấu Trúc Thư Mục

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
