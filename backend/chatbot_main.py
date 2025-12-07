from get_doc.get_docs import get_docs
from get_doc.get_long_term import get_data
from langchain_core.runnables import chain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate   
from get_doc.expand_query import llm_expand_query
from chatbots.chatbot_summary import summary
from tracing import tracer
from chatbots.chatbot_update_ltm import update_ltm_chatbot
from chatbots.chatbot_check_info import check_user_info
import logging
from concurrent.futures import ThreadPoolExecutor
from opentelemetry import context
prompt_template=ChatPromptTemplate.from_messages([
    ('system','Bạn là một chuyên gia tư vấn về thuốc và y tế. Sử dụng thông tin từ bộ nhớ dài hạn và các tài liệu liên quan để trả lời câu hỏi của người dùng một cách chính xác và chi tiết. Khi người dùng hỏi về thuốc cho triệu chứng/bệnh cụ thể, hãy đưa ra tên thuốc cụ thể từ tài liệu tham khảo nếu có.'),
    ('human',"""Câu hỏi của người dùng: {user_query}
     
     Dữ liệu bộ nhớ dài hạn về người dùng: {long_term_memory} 
     
     Tài liệu tham khảo về thuốc: {reference_docs}
     
     Hướng dẫn:
     - Ưu tiên sử dụng thông tin từ tài liệu tham khảo để đưa ra tên thuốc cụ thể
     - Nếu có thông tin trong bộ nhớ dài hạn về người dùng (dị ứng, bệnh lý, v.v.), hãy cân nhắc khi tư vấn
     - Nếu tài liệu tham khảo có thông tin về thuốc phù hợp, hãy đưa ra tên thuốc cụ thể kèm theo hướng dẫn sử dụng
     - Nếu thông tin không đủ, bạn có thể dựa vào kiến thức của bản thân nhưng vẫn ưu tiên thông tin từ tài liệu
     - Luôn nhắc nhở người dùng tham khảo ý kiến bác sĩ trước khi sử dụng thuốc""")
    ])
llm=ChatOpenAI()
@chain
def chatbot_response(user_query):
    with tracer.start_as_current_span("chatbot_response"):
        # Kiem tra thong tin nguoi dung truoc khi xu ly
        with tracer.start_as_current_span("Check_information"):
            logging.info("Kiem tra thong tin nguoi dung \n\n")
            check_result = check_user_info.invoke(user_query)
            
            # Neu khong lien quan hoac khong du thong tin, tra ve thong bao va dung xu ly
            if not check_result.get('should_continue', False):
                logging.info("Thong tin khong du hoac khong lien quan, tra ve thong bao \n\n")
                return check_result.get('response_message', 'Xin lỗi, tôi không thể xử lý câu hỏi này.')
        
        # Chay song song 3 luong: cap nhat longterm, lay data longterm, mo rong query
        executor = ThreadPoolExecutor(max_workers=3)
        
        # Lay context hien tai de truyen sang cac thread khac
        current_context = context.get_current()
        
        def update_ltm_task():
            # Attach context tu thread chinh
            context.attach(current_context)
            try:
                with tracer.start_as_current_span("Update_long_term_memory"):
                    logging.info("Cap nhat long term memory \n\n")
                    update_ltm_chatbot.invoke(user_query)
            except Exception as e:
                logging.error(f"Lỗi khi cập nhật long-term memory: {e}")
        
        def get_longterm_task():
            # Attach context tu thread chinh
            context.attach(current_context)
            with tracer.start_as_current_span("Get_long_term"):
                logging.info("Lay data long term memory \n\n")
                return get_data()
        
        def expand_query_task():
            # Attach context tu thread chinh
            context.attach(current_context)
            with tracer.start_as_current_span("Expand_query"):
                logging.info("Mo rong query \n\n")
                return llm_expand_query.invoke(user_query)
        
        # Chay song song 3 tasks
        # CHỈ chạy update_ltm trong background, KHÔNG chờ kết quả (tránh block)
        future_update_ltm = executor.submit(update_ltm_task)
        
        # Chờ 2 tasks quan trọng: longterm và expand query
        future_longterm = executor.submit(get_longterm_task)
        future_expand = executor.submit(expand_query_task)
        
        # Chỉ chờ 2 tasks cần thiết, không chờ update_ltm
        data_longterm = future_longterm.result()
        expand_query = future_expand.result()
        
        # Shutdown executor nhưng không chờ update_ltm task (nó sẽ chạy trong background)
        executor.shutdown(wait=False)

        # lay docs
        with tracer.start_as_current_span("get_docs"):
            logging.info("Lay document phu hop \n\n")
            docs = get_docs.invoke(expand_query)

        # kiem tra do dai + summarize khi cần
        combined_doc_content = ""
        with tracer.start_as_current_span("Summarize"):
            logging.info("Kiem tra do dai document")
            for doc in docs:
                combined_doc_content += doc.page_content + "\n"
                if len(combined_doc_content) > 10000:
                    combined_doc_content = summary.invoke(combined_doc_content)

        # tra loi (LLM invocation)
        with tracer.start_as_current_span("LLM_invoke"):
            logging.info("Tra loi nguoi dung")
            chatbot = prompt_template | llm
            
            chatbot_response = chatbot.invoke({
                'user_query': user_query,
                'long_term_memory': data_longterm if data_longterm else "Chưa có thông tin về người dùng trong bộ nhớ dài hạn.",
                'reference_docs': combined_doc_content if combined_doc_content else "Không tìm thấy tài liệu tham khảo phù hợp."
            })


        return chatbot_response.content