from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import chain
from langchain_core.output_parsers import JsonOutputParser

llm = ChatOpenAI(model="gpt-4", temperature=0)

# Prompt để kiểm tra thông tin người dùng
check_info_prompt = ChatPromptTemplate.from_messages([
    ('system', """Bạn là một AI chuyên phân tích câu hỏi của người dùng trong lĩnh vực tư vấn thuốc.

Nhiệm vụ của bạn:
1. Kiểm tra xem câu hỏi có liên quan đến tư vấn thuốc không:
   - Câu hỏi về thuốc (tên thuốc, công dụng, liều lượng, tác dụng phụ, cách sử dụng)
   - Câu hỏi về triệu chứng/bệnh cần tư vấn thuốc
   - Câu hỏi y tế có thể liên quan đến việc sử dụng thuốc
   - KHÔNG liên quan: câu hỏi về thời tiết, thể thao, giải trí, v.v. (trừ khi có liên quan đến thuốc)

2. Kiểm tra xem có đủ thông tin để tư vấn thuốc không:
   - Nếu câu hỏi có đề cập đến triệu chứng/bệnh cụ thể (dù chỉ một triệu chứng): coi là đủ để tư vấn
   - Nếu câu hỏi về tên thuốc, công dụng, cách dùng: luôn coi là đủ
   - Nếu câu hỏi chỉ là "muốn mua thuốc" hoặc "thuốc gì": kiểm tra xem có lịch sử hội thoại trước đó đề cập đến triệu chứng/bệnh không. Nếu có trong lịch sử, coi là đủ.
   - Chỉ coi là chưa đủ khi: câu hỏi hoàn toàn chung chung, không có triệu chứng/bệnh, và không có lịch sử hội thoại liên quan

3. Nếu không liên quan hoặc không đủ thông tin:
   - Tạo thông báo thân thiện, rõ ràng
   - Nếu không liên quan: thông báo đây là chatbot tư vấn thuốc và chỉ trả lời câu hỏi trong phạm vi
   - Nếu không đủ thông tin: hỏi thêm thông tin còn thiếu một cách cụ thể

Trả về JSON với format:
{{
    "is_related": true/false,
    "has_sufficient_info": true/false,
    "missing_info": ["danh sách thông tin còn thiếu nếu có"],
    "response_message": "thông báo cần trả về nếu không đủ hoặc không liên quan (để trống nếu đủ và liên quan)",
    "should_continue": true/false
}}

Lưu ý:
- should_continue = true khi is_related = true VÀ (has_sufficient_info = true HOẶC câu hỏi có thể trả lời dựa trên lịch sử hội thoại)
- Nếu câu hỏi liên quan đến thuốc nhưng chưa đủ thông tin VÀ không có lịch sử hội thoại, mới trả về response_message để hỏi thêm
- response_message nên thân thiện, hướng dẫn người dùng, và bằng tiếng Việt
- Ưu tiên cho phép tiếp tục xử lý nếu có thể trả lời được (dù thông tin chưa hoàn chỉnh)"""),
    ('human', 'Câu hỏi của người dùng: {user_query}')
])

parser = JsonOutputParser()

@chain
def check_user_info(user_query: str):
    """
    Kiểm tra thông tin người dùng:
    - Có liên quan đến tư vấn thuốc không
    - Có đủ thông tin để tư vấn không
    
    Args:
        user_query: Câu hỏi của người dùng
        
    Returns:
        dict: Kết quả kiểm tra với các field:
            - is_related: có liên quan đến tư vấn thuốc không
            - has_sufficient_info: có đủ thông tin không
            - missing_info: danh sách thông tin còn thiếu
            - response_message: thông báo cần trả về
            - should_continue: có nên tiếp tục xử lý không
    """
    chain_check = check_info_prompt | llm | parser
    result = chain_check.invoke({"user_query": user_query})
    return result

