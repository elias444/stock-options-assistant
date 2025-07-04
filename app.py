import streamlit as st
import openai
import requests
import datetime
import yfinance as yf
import pandas_ta as ta

# --- CONFIGURE THESE ---
OPENAI_API_KEY = "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"
ALPACA_API_KEY = "PKYK3RYMN72SRI7O5RKP"
ALPACA_SECRET_KEY = "9kqQa3BmitaC5c5U3523KGggQcFbY3rA1oIgIkVX"

# --- SETUP ---
openai.api_key = OPENAI_API_KEY

# --- HELPER FUNCTIONS ---
def get_stock_price(ticker):
    try:
        data = yf.Ticker(ticker)
        price = data.history(period="1d").iloc[-1]['Close']
        return price
    except Exception as e:
        st.error(f"Price error: {e}")
        return None

def get_technical_indicators(ticker):
    try:
        df = yf.download(ticker, period="1mo", interval="1d")
        df.ta.rsi(length=14, append=True)
        df.ta.macd(append=True)
        rsi = df['RSI_14'].dropna().iloc[-1]
        macd = df['MACD_12_26_9'].dropna().iloc[-1]
        signal = df['MACDs_12_26_9'].dropna().iloc[-1]
        return f"RSI: {rsi:.2f}, MACD: {macd:.2f}, Signal: {signal:.2f}"
    except Exception as e:
        return f"Could not calculate indicators: {e}"

def get_alpaca_options_chain(ticker):
    url = f"https://data.alpaca.markets/v1beta1/options/chains/{ticker}"
    headers = {
        "APCA-API-KEY-ID": ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("option_chain", [])[:10]
    else:
        return f"Options API error: {response.status_code}"

def chat_with_assistant(message_history):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=message_history
    )
    return response.choices[0].message.content

# --- STREAMLIT APP ---
st.title("💬 Chat with Your AI Options Assistant")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "system", "content": "You are a helpful, expert options trading assistant. Format responses using markdown (bold headers, bullet points, italics for notes)."},
    ]

user_input = st.chat_input("Ask me about a stock, strategy, or market view...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    words = user_input.upper().split()
    ticker = next((word for word in words if word.isalpha() and len(word) <= 5), None)

    price = get_stock_price(ticker) if ticker else None
    indicators = get_technical_indicators(ticker) if ticker else ""
    options_data = get_alpaca_options_chain(ticker) if ticker else ""

    if price:
        summary = f"**Price**: ${price:.2f}\n\n**Indicators**: {indicators}\n\n**Options Sample**: {str(options_data)[:500]}"
        st.session_state.chat_history.append({"role": "system", "content": summary})

    response = chat_with_assistant(st.session_state.chat_history)
    st.session_state.chat_history.append({"role": "assistant", "content": response})

for msg in st.session_state.chat_history[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

st.markdown("---")
st.caption("Built with 💡 by ChatGPT + Alpaca + OpenAI + yFinance")