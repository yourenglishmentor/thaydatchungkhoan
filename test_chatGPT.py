import streamlit as st
from openai import OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# completion = client.chat.completions.create(
#   model="gpt-5-mini",
#   messages=[
#     {"role": "system", "content": "Bạn là một chuyên gia phân tích tài chính."},
#     {"role": "user", "content": "Hãy phân tích hoạt động kinh doanh của công ty BIDV"}
#   ],
#   max_completion_tokens=500
# )

def ask_chatGPT(question):

    response = client.responses.create(
    model="gpt-5-mini",
    tools=[{"type": "web_search"}],
    instructions = "Bạn là một chuyên gia phân tích tài chính, trả lời câu hỏi đủ ý, không hỏi thêm câu hỏi nào khác",
    input=question
    )
    # print(response)
    print(f"Input Tokens da su dung: {response.usage.input_tokens}")
    print(f"Output Tokens da su dung: {response.usage.output_tokens}")
    print(f"Tong cong Tokens da su dung: {response.usage.total_tokens}")
    # print(response.output_text)
    return response.output_text

def chatBot_answer(st):
    # send user's message to GPT-4o and get a response
    response = client.responses.create(
        model="gpt-5-mini",  # hoặc "gpt-5", reasoning mạnh hơn
        tools=[{"type": "web_search"}],  # có thể bỏ nếu không muốn tra web
        input=[
            {"role": "system", "content": "Bạn là một chuyên gia phân tích tài chính"},
            *st.session_state.chat_history
        ]
    )

    assistant_response = response.output_text
    st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
    
    return assistant_response

# MOAT_grade = ask_chatGPT(f"Bản tóm tắt nội dung cuộc gọi công bố kết quả kinh doanh gần đây của công ty MSFT.")
# print(MOAT_grade)

