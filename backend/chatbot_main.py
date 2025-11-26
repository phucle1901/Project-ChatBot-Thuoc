from get_doc.get_docs import get_docs
from get_doc.get_long_term import get_data
from langchain_core.runnables import chain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate   
from get_doc.expand_query import llm_expand_query
from chatbots.chatbot_summary import summary
from tracing import tracer
from chatbots.chatbot_update_ltm import update_ltm_chatbot
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from opentelemetry import context
prompt_template=ChatPromptTemplate.from_messages([
    ('system','Bạn là một chuyên gia tư vấn về thuốc và y tế. Sử dụng thông tin từ bộ nhớ dài hạn và các tài liệu liên quan để trả lời câu hỏi của người dùng một cách chính xác và chi tiết.'),
    ('human',"""Câu hỏi của người dùng: {user_query}
     Dữ liệu bộ nhớ dài hạn: {long_term_memory} 
     Tài liệu tham khảo: {reference_docs}
     Trong trường hợp nếu cảm thấy thông tin từ bộ nhớ dài hạn và tài liệu tham khảo không đủ để trả lời câu hỏi , bạn hãy dựa vào kiến thức của bản thân để tra lời câu hỏi(trong câu trả lời cho người dùng thì không cần nói tài liệu tham khảo không có thông tin )""")
    ])
llm=ChatOpenAI()
@chain
def chatbot_response(user_query):
    with tracer.start_as_current_span("chatbot_response"):
        # Chay song song 3 luong: cap nhat longterm, lay data longterm, mo rong query
        executor = ThreadPoolExecutor(max_workers=3)
        
        # Lay context hien tai de truyen sang cac thread khac
        current_context = context.get_current()
        
        def update_ltm_task():
            # Attach context tu thread chinh
            context.attach(current_context)
            with tracer.start_as_current_span("Update_long_term_memory"):
                logging.info("Cap nhat long term memory \n\n")
                update_ltm_chatbot.invoke(user_query)
        
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
        future_update_ltm = executor.submit(update_ltm_task)
        future_longterm = executor.submit(get_longterm_task)
        future_expand = executor.submit(expand_query_task)
        
        future_update_ltm.result()  
        data_longterm = future_longterm.result()
        expand_query = future_expand.result()
        
        executor.shutdown(wait=True)

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
                'long_term_memory': data_longterm,
                'reference_docs': combined_doc_content
            })

        return chatbot_response.content