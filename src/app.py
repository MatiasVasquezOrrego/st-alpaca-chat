import streamlit as st
from streamlit_chat import message as st_message

def generate_alpaca_message(user_input: str):
    return "alpaca response"

def generate_chat():
    user_message = st.session_state.input_text
    alpaca_message = generate_alpaca_message(user_input=user_message)

    st.session_state.history.append(
        {'message': user_message, 'is_user': True}
    )

    st.session_state.history.append(
        {'message': alpaca_message, 'is_user': False}
    )

st.title("Alpaca Chat")

if "history" not in st.session_state:
    history = [
        {
            "message": "Hello my friend",
            "is_user": False
        }
    ]
    st.session_state.history = history

st.text_input("", key="input_text", on_change=generate_chat)

for i, chat in enumerate(st.session_state.history):
    st_message(**chat, key=str(i))