from flask import Flask, jsonify
import yfinance as yf
import requests
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

app = Flask(__name__)

# Constants
STOCK_INDICES = {"^NSEI": "Nifty 50", "^BSESN": "Sensex", "^IXIC": "NASDAQ"}
AQI_API_URL = "http://api.waqi.info/feed/chennai/"
WEATHER_API_URL = "http://api.weatherapi.com/v1/current.json?"


# Fetch stock market data
def get_stock_data():
    stock_summary = {}
    for symbol, name in STOCK_INDICES.items():
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period="1d")
            close_price = round(data["Close"].iloc[-1], 2) if not data.empty else None
            news = stock.news[:3] if hasattr(stock, "news") else []

            news_summary = [
                {
                    "title": item.get("content", {}).get("title", "No title"),
                    "summary": item.get("content", {}).get("summary", "No summary"),
                }
                for item in news
            ]

            stock_summary[name] = {
                "Closing Price": close_price,
                "Related News": news_summary,
            }
        except Exception as e:
            stock_summary[name] = {"error": f"Failed to fetch stock data: {e}"}

    return stock_summary


# Fetch AQI data
def get_aqi():
    token = os.getenv("AQI_API_KEY")  # Store in .env
    if not token:
        return {"error": "API key missing"}

    try:
        response = requests.get(AQI_API_URL, params={"token": token})
        response.raise_for_status()
        data = response.json()
        return (
            {"AQI": data["data"]["aqi"]}
            if data.get("status") == "ok"
            else {"error": data.get("status")}
        )
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch AQI: {e}"}


# Fetch weather data
def get_weather():
    api_key = os.getenv("WEATHER_API_KEY")  # Store in .env
    if not api_key:
        return {"error": "Weather API key missing"}

    try:
        params = {"q": "Chennai", "key": api_key}
        response = requests.get(WEATHER_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return {
            "temperature": data["current"]["temp_c"],
            "feels like": data["current"]["feelslike_c"],
            "description": data["current"]["condition"]["text"],
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch weather: {e}"}


@app.route("/")
def home():
    stock_data = get_stock_data()
    aqi_data = get_aqi()
    weather_data = get_weather()

    return jsonify(
        {"Market Summary": stock_data, "AQI": aqi_data, "Weather": weather_data}
    )


if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 5000)),
        debug=os.getenv("FLASK_DEBUG", "False") == "True",
    )
