import os
import json
import openai
from typing import Optional
import gradio as gr
from datetime import datetime
import base64

# 프롬프트 읽어오기
with open("../prompts/v2.2.txt", "r", encoding="utf-8") as f:
    system_prompt = f.read()

openai.api_key = os.environ.get("OPENAI_API_KEY")

class Chat:
    def __init__(self, system: Optional[str] = None):
        self.system = system
        self.messages = []
        self.log_file = None

        if system is not None:
            self.messages.append({"role": "system", "content": system})

    def prompt(self, content: str) -> str:
        self.messages.append({"role": "user", "content": content})
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=self.messages
        )
        response_content = response["choices"][0]["message"]["content"]
        self.messages.append({"role": "assistant", "content": response_content})
        self.save_log()
        return response_content

    def save_log(self):
        """현재 채팅 기록을 JSON 파일로 저장"""
        if self.log_file is None:
            now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self.log_file = f"chat_log_{now}.json"
        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(self.messages, f, ensure_ascii=False, indent=2)

    def load_log(self, file_path: str):
        """JSON 파일에서 채팅 기록을 불러와 복원"""
        with open(file_path, "r", encoding="utf-8") as f:
            self.messages = json.load(f)

    def clear_log(self):
        self.messages = []
        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write("")  # 파일 비우기

chat = Chat(system=system_prompt)

def respond(message, chat_history):
    # 이미지 경로
    bot_profile_path = "../assets/bot_profile.png"
    
    # 이미지를 Base64로 인코딩
    with open(bot_profile_path, "rb") as f:
        encoded_image = base64.b64encode(f.read()).decode("utf-8")

    # 이미지와 텍스트를 같은 줄에 표시하기 위한 HTML/CSS
    image_html = f"""
    <div style="display: flex; align-items: center;">
        <img src='data:image/png;base64,{encoded_image}' 
             style='max-width: 30px; max-height: 30px; margin-right: 10px;' 
             alt='bot_profile'/>
        <span>{chat.prompt(content=message)}</span>
    </div>
    """

    # 메시지 기록 업데이트
    chat_history.append({"role": "user", "content": message, "image": "../assets/user_profile.png"})
    chat_history.append({"role": "assistant", "content": image_html})

    return "", chat_history


def download_log():
    """현재 채팅 기록 JSON 파일 다운로드"""
    if chat.log_file and os.path.exists(chat.log_file):
        return chat.log_file
    return None

def load_chat(file):
    """저장된 채팅 기록을 불러와 UI에 반영"""
    chat.load_log(file.name)
    chat_history = []
    for msg in chat.messages:
        if msg["role"] == "user":
            chat_history.append({"role": "user", "content": msg["content"], "image": "../assets/user_profile.png"})
        elif msg["role"] == "assistant":
            chat_history.append({"role": "assistant", "content": msg["content"], "image": "../assets/bot_profile.png"})
    return chat_history

def clear_chat(chat_history):
    """채팅 기록 초기화"""
    chat.clear_log()
    return []

# Gradio Blocks UI 구성
with gr.Blocks() as demo:
    with gr.Row():
        gr.Markdown("# MoodBin - 당신의 감정을 공유하세요 🌈")

    gr.Markdown("한국고등교육재단 인재림 3기 (황경서, 박소혜, 배서현, 최대현) - SOUL Project의 연구 결과물입니다.")

    chatbot = gr.Chatbot(type='messages')  # 'messages' 타입 사용
    msg = gr.Textbox(label="메시지를 입력하세요", placeholder="무엇이든 물어보세요!")
    load_file = gr.File(label="채팅 불러오기")
    download_output = gr.File(label="채팅 로그 다운로드")

    with gr.Row():
        clear_btn = gr.Button("채팅 비우기", variant="secondary")
        download_btn = gr.Button("채팅 로그 다운로드", variant="success")

    # 이벤트 연결
    msg.submit(respond, [msg, chatbot], [msg, chatbot])
    clear_btn.click(clear_chat, inputs=[chatbot], outputs=chatbot)
    download_btn.click(download_log, inputs=None, outputs=download_output)
    load_file.upload(load_chat, inputs=[load_file], outputs=[chatbot])  # 채팅 로그 불러오기

demo.launch(debug=True, share=True)
