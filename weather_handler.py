import requests
import os

# ✅ Load Weather API Key
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# ✅ Fetch real-time weather data for a specific city
def get_weather(city=None):
    if not city:
        return "**Please provide a city name for the weather report.**"

    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={city}&days=7&aqi=no&alerts=no"
    
    try:
        print(f"🔍 Fetching weather for: {city}")  # ✅ Debugging step
        print(f"🌐 API Request URL: {url}")  # ✅ Debugging step
        
        response = requests.get(url)
        data = response.json()

        # ✅ Debug: Print API response
        print("🔎 API Response:", data)  

        # ✅ Check if response contains weather data
        if "error" in data:
            print(f"❌ API Error: {data['error'].get('message', 'Unknown error')}")
            return f"**I couldn't retrieve the weather for {city}. Error: {data['error'].get('message', 'Unknown error')}**"

        if "current" not in data or "forecast" not in data:
            return f"**I couldn't retrieve the weather for {city}. Please try another location.**"

        # ✅ Extract current weather details
        current_temp = data["current"].get("temp_f", "N/A")
        condition = data["current"].get("condition", {}).get("text", "Unknown")
        wind_speed = data["current"].get("wind_mph", "N/A")
        precipitation = data["current"].get("precip_in", "N/A")
        icon_url = "https:" + data["current"]["condition"]["icon"]

        # ✅ Format the 7-day forecast
        forecast_data = data["forecast"]["forecastday"]
        forecast = "".join(
            f"<li>📅 <b>{day['date']}</b> - <img src='https:{day['day']['condition']['icon']}' width='20'> {day['day'].get('avgtemp_f', 'N/A')}°F, {day['day']['condition']['text']}</li>"
            for day in forecast_data
        )

        # ✅ Final formatted response
        weather_response = (
            f"<b>📍 Location:</b> {data['location']['name']}, {data['location']['region']}, {data['location']['country']}<br><br>"
            f"<b>🌡 Temperature:</b> {current_temp}°F<br>"
            f"<b>⛅ Condition:</b> {condition} <img src='{icon_url}' width='25'><br>"
            f"<b>💨 Wind Speed:</b> {wind_speed} mph<br>"
            f"<b>🌧 Precipitation:</b> {precipitation} in<br><br>"
            f"<b>📅 7-Day Forecast:</b><br><ul>{forecast}</ul>"
        )

        return weather_response

    except Exception as e:
        print(f"❌ Error fetching weather data: {e}")
        return f"**I couldn't fetch the weather for {city}. Please try again later.**"
