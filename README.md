
## Tracing
<img width="2940" height="830" alt="image" src="https://github.com/user-attachments/assets/1c239421-d14b-47b9-9c67-3946af172b2c" />


## Loging
<img width="2078" height="728" alt="image" src="https://github.com/user-attachments/assets/44a50bb3-5d10-4132-8ad6-9ed63b39c217" />

## Architect
<img width="944" height="521" alt="Ảnh màn hình 2025-11-26 lúc 13 16 43" src="https://github.com/user-attachments/assets/22369775-c7c3-4957-a1bb-bdc026b249d4" />


## Luồng hoạt động của hệ thống
#### **Bước 1: Xử Lý Song Song (Parallel Processing)**
Sử dụng `ThreadPoolExecutor` để chạy đồng thời 3 tác vụ:

**a) Cập Nhật Bộ Nhớ Dài Hạn (Long-Term Memory - LTM)**
- `backend/chatbots/chatbot_update_ltm.py`
- Ở bước này ta sẽ sử dụng LLM để kiểm tra xem query của người dùng có chưa thông tin nên được lưu vào LTM không( các thông tin như sở thích thói quen ,...)
- Nếu như ta phát hiện query chưa thống tin cần lưu thì ta cần kiểm tra trong bộ nhớ hiện tại đã có thông tin này chưa , nêu chưa có thì tiến hành cập nhật
```
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
