import os
import streamlit as st
from openai import OpenAI

# 初始化客户端
client = OpenAI(
    api_key=st.secrets["openai"]["api_key"],  # 使用环境变量中的API密钥
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"  # DashScope服务base_url
)

def longresponse_page():
    # 用户输入的文章内容
    article_content = st.text_area("请输入文章内容:", height=300)
    
    if st.button('获取摘要'):
        if article_content.strip() != '':
            messages=[
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': '这篇文章讲了什么？'},
                {'role': 'user', 'content': article_content}
            ]
            
            try:
                completion = client.chat.completions.create(
                    model="qwen-long",
                    messages=messages,
                    stream=True,
                    stream_options={"include_usage": True}
                )
                
                full_content = ""
                for chunk in completion:
                    if chunk.choices and chunk.choices[0].delta.content:
                        full_content += chunk.choices[0].delta.content
                        st.write(full_content)  # 实时显示每个chunk的内容
                
                st.write("全文摘要: ", full_content)
            except Exception as e:
                st.error(f"发生错误: {e}")
        else:
            st.warning("请输入文章内容！")
