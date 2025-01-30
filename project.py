from flask import Flask, render_template, request
import os
import requests
import pycountry

app = Flask(__name__)

# Store API key securely using environment variables
OPENWEATHER_API_KEY = "c70a74b54910e4f3d2675b56006ab319"
NEWS_API_KEY = "53968f264bd14de41ae489ff0ae9450e"
IP_API_URL = "https://api64.ipify.org?format=json"
GEO_API_URL = "http://ip-api.com/json/"
NEWS_API_URL = "https://gnews.io/api/v4/top-headlines"

@app.route("/")
def homepage():
    city, country_code, country_name, articles = "Unknown", "", "Unknown", []

    try:
        # Step 1: Get user's public IP address
        ip_response = requests.get(IP_API_URL)
        ip_data = ip_response.json()
        user_ip = ip_data.get("ip", "")
        print(f"User IP: {user_ip}")  # Debug log

        # Step 2: Get user's location data
        geo_response = requests.get(f"{GEO_API_URL}{user_ip}")
        geo_data = geo_response.json()
        print(f"Geolocation Data: {geo_data}")  # Debug log

        city = geo_data.get("city", "Unknown")
        country_code = geo_data.get("countryCode", "")

        # Convert country code to full country name
        if country_code:
            country_obj = pycountry.countries.get(alpha_2=country_code)
            country_name = country_obj.name if country_obj else "Unknown"

            # Step 3: Fetch local news based on country
            news_response = requests.get(NEWS_API_URL, params={
                "country": country_code.lower(),  # GNews uses lowercase country codes
                "token": NEWS_API_KEY,
                "max": 3  # Limit to 3 articles
            })
            news_data = news_response.json()
            print(f"News API Response: {news_data}")  # Debug log
            articles = news_data.get("articles", [])[:3]  # Limit to 3 articles

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")

    return render_template("home.html", country=country_name, articles=articles)

@app.route('/cat')
def cat():
    # Fetch data from the Cat Facts API
    cat_facts_url = "https://catfact.ninja/fact"
    response = requests.get(cat_facts_url)

    if response.status_code == 200:
        cat_fact = response.json()["fact"]
    else:
        cat_fact = "Could not fetch cat facts at the moment. Please try again later."

    return render_template('cat.html', cat_fact=cat_fact)

# Openweather API
@app.route('/weather', methods=['GET', 'POST'])
def weather():
    weather_data = None
    error = None

    if request.method == 'POST':
        city = request.form.get('city')

        if city:
            weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"

            try:
                response = requests.get(weather_url)
                if response.status_code == 200:
                    weather_data = response.json()
                else:
                    error = "City not found. Please try again."
            except requests.exceptions.RequestException:
                error = "Weather service is currently unavailable. Please try again later."
        else:
            error = "Please enter a city name."

    return render_template('result.html', weather_data=weather_data, error=error)

# Zenquotes
@app.route('/quotes', methods=['GET', 'POST'])
def quotes():
    quote_data = None
    error = None

    if request.method == 'POST' or request.method == 'GET':  # Allow refresh
        url = "https://zenquotes.io/api/random"

        try:
            response = requests.get(url)
            if response.status_code == 200:
                quote_json = response.json()
                quote_data = {
                    "content": quote_json[0]["q"],  # Quote text
                    "author": quote_json[0]["a"]  # Author name
                }
            else:
                error = "Failed to fetch a quote. Please try again."
        except requests.exceptions.RequestException:
            error = "Quote service is currently unavailable. Please try again later."

    return render_template('quotes.html', quote_data=quote_data, error=error)

# GitHub API route
@app.route('/github', methods=['GET', 'POST'])
def github_profile():
    user_data = None
    error = None

    # Check if form is submitted
    if request.method == 'POST':
        username = request.form.get('username')

        if username:
            # GitHub API call
            url = f"https://api.github.com/users/{username}/repos"
            headers = {
                'Authorization': 'token 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'}

            try:
                response = requests.get(url, headers=headers)

                if response.status_code == 200:  # Successful response
                    user_data = response.json()
                    if not user_data:
                        error = "This user doesn't have any repositories."
                elif response.status_code == 404:  # User not found
                    error = "This user can't be found."
                else:  # Other error codes
                    error = "Unable to fetch details. Please try again later."
            except requests.exceptions.RequestException:
                error = "There was a problem connecting to GitHub. Please try again later."
        else:
            error = "Please provide a username."

    return render_template('github.html', user_data=user_data, error=error)

#Jokes API
@app.route('/joke', methods=['GET', 'POST'])
def joke():
    joke_data = None
    error = None

    if request.method == 'POST':
        # Fetch a random joke from JokeAPI
        category = request.form.get('category', 'Any')  # Default is 'Any' if no category is selected
        url = f"https://v2.jokeapi.dev/joke/{category}?type=single"

        try:
            response = requests.get(url)
            if response.status_code == 200:
                joke_data = response.json()
            else:
                error = "Failed to fetch a joke. Please try again."
        except requests.exceptions.RequestException as e:
            error = "Joke service is currently unavailable. Please try again later."

    return render_template('joke.html', joke_data=joke_data, error=error)

#Currency Exchange Rate
@app.route('/currency', methods=['GET', 'POST'])
def currency_rate():
    exchange_data = None
    error = None

    if request.method == 'POST':
        base_currency = request.form['base_currency']  # e.g., USD
        target_currency = request.form['target_currency']  # e.g., EUR
        amount = float(request.form['amount'])  # Amount of base currency
        url = f"https://v6.exchangerate-api.com/v6/134c221bed30d8402bb59b76/latest/{base_currency}"

        try:
            response = requests.get(url)
            if response.status_code == 200:
                rates = response.json()
                if target_currency in rates["conversion_rates"]:
                    target_rate = rates["conversion_rates"][target_currency]
                    calculated_amount = round(amount * target_rate, 2)  # Calculate the exchanged amount
                    exchange_data = {
                        "base": base_currency,
                        "target": target_currency,
                        "rate": target_rate,
                        "amount": amount,
                        "calculated_amount": calculated_amount
                    }
                else:
                    error = f"Currency '{target_currency}' not found in exchange rates!"
            else:
                error = "Failed to fetch exchange rates. Please check your API key or try again later."
        except requests.exceptions.RequestException as e:
            error = "Currency exchange service is currently unavailable. Please try again later."

    return render_template('currency.html', exchange_data=exchange_data, error=error)

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == "__main__":
    # Change port to avoid conflicts
    app.run(debug=True, port=5001)  # Use port 5001 instead of the default 5000




