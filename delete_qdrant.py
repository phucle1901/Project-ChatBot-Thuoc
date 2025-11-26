import os
import dotenv
from qdrant_client import QdrantClient

def clear_qdrant_collection():
    """Xóa collection trên Qdrant"""
    dotenv.load_dotenv()
    
    client = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY")
    )
    
    collection_name = "embedding_data"
    
    try:
        # Kiểm tra collection có tồn tại không
        collections = client.get_collections().collections
        collection_exists = any(c.name == collection_name for c in collections)
        
        if collection_exists:
            print(f"Đang xóa collection '{collection_name}'...")
            client.delete_collection(collection_name)
            print(f"Đã xóa collection '{collection_name}' thành công!")
        else:
            print(f"ℹCollection '{collection_name}' không tồn tại.")
    
    except Exception as e:
        print(f"Lỗi khi xóa collection: {str(e)}")

if __name__ == "__main__":
    clear_qdrant_collection()