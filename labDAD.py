import json
import requests
import tkinter as tk
from tkinter import messagebox, filedialog


def fetch_coordinates_for_city(city_name):
    # Define the API URL with the city name
    api_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=10&language=en&format=json"

    # Make the API request
    response = requests.get(api_url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()

        # Filter data for California
        california_data = [item for item in data.get('results', []) if item.get('admin1') == 'California']

        # Extract the latitude and longitude values
        if california_data:
            latitude = california_data[0].get('latitude')
            longitude = california_data[0].get('longitude')
            return {"latitude": latitude, "longitude": longitude}
        else:
            print(f"No data found for {city_name}, California.")
            return None
    else:
        print(f"Failed to fetch data for {city_name}. Status code: {response.status_code}")
        return None


def load_city_coordinates():
    ''' Fetch city coordinates using API call and load in JSON file '''

    # List of cities
    cities = ["Napa", "Sonoma", "Santa Cruz", "Monterey", "Berkeley", "Livermore", "San Francisco", "San Mateo",
              "San Jose", "Los Gatos"]

    # Dictionary to store results
    results = {}

    # Loop through each city
    for city in cities:
        print(f"Fetching coordinates for {city}...")
        coordinates = fetch_coordinates_for_city(city)
        if coordinates:
            results[city] = coordinates
        else:
            results[city] = "No data found for California."

    # Print the results
    print(json.dumps(results, indent=4))

    # Write the results to a JSON file
    with open('city_coordinates.json', 'w') as outfile:
        json.dump(results, outfile, indent=4)


def check_file_exists(file_name):
    try:
        with open(file_name, 'r'):
            return True
    except FileNotFoundError:
        return False


def read_coordinates_from_file(file_path):
    # Open the JSON file and load its content into a dictionary

    with open(file_path, 'r') as file:
        data = json.load(file)
    return data


def get_coordinates(city, data):
    # Fetch the latitude and longitude for the given city
    if city in data:
        latitude = data[city].get('latitude')
        longitude = data[city].get('longitude')
        return latitude, longitude
    else:
        print(f"No data found for {city}.")
        return None, None


def fetch_daily_weather(latitude, longitude):
    api_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={latitude}&longitude={longitude}&"
        f"daily=temperature_2m_max,temperature_2m_min,windspeed_10m_max,uv_index_max&"
        f"timezone=America/Los_Angeles&"
        f"temperature_unit=fahrenheit&"
        f"wind_speed_unit=mph&"
        f"forecast_days=5"
    )
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch weather data. Status code: {response.status_code}")
        return None


def fetch_city_weather(city, data):
    latitude, longitude = get_coordinates(city, data)
    if latitude is not None and longitude is not None:
        print(f"Coordinates for {city}: Latitude={latitude}, Longitude={longitude}")

        print("Fetching daily weather data...")
        weather_data = fetch_daily_weather(latitude, longitude)

        if weather_data:
            # Extracting daily weather information
            daily_data = weather_data.get('daily')
            print(daily_data)
            print('\n')

            if daily_data:
                dates = daily_data.get('time')
                max_temps = daily_data.get('temperature_2m_max')
                min_temps = daily_data.get('temperature_2m_min')
                max_winds = daily_data.get('windspeed_10m_max')
                max_uvs = daily_data.get('uv_index_max')

                # return the above variables for each city and have function called based on city selection

                # if city not in city_weather_data:
                #    city_weather_data[city] = []

                for i in range(len(dates)):
                    date = dates[i]
                    max_temp = max_temps[i]
                    min_temp = min_temps[i]
                    max_wind = max_winds[i]
                    max_uv = max_uvs[i]

                    # city_weather_data[city].append({
                    #         "date": date,
                    #         "max_temperature_f": max_temp,
                    #         "min_temperature_f": min_temp,
                    #         "max_wind_speed_mph": max_wind,
                    #         "max_uv_index": max_uv
                    #     })

                    print(
                        f"Date: {date}, Max Temp: {max_temp}, Min Temp: {min_temp}, Max Wind Speed: {max_wind}, Max UV Index: {max_uv}")
                    return daily_data
            else:
                print("No daily data available.")
        else:
            print("Could not fetch weather data.")




class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.search_results = []

        city_groups = {
            "North Bay": ["Napa", "Sonoma"],
            "The Coast": ["Santa Cruz", "Monterey"],
            "East Bay": ["Berkeley", "Livermore"],
            "Peninsula": ["San Francisco", "San Mateo"],
            "South Bay": ["San Jose", "Los Gatos"]
        }

        file_name = 'city_coordinates.json'
        if not check_file_exists(file_name):
            print(f"The file '{file_name}' does not exist, calling API to create JSON file having coordinates")
            # Calls function to load city coordinates
            load_city_coordinates()

        # Fetch the city coordinates from JSON file
        print('Reading coordinates from the JSON file...')
        self.data = read_coordinates_from_file(file_name)

        # title + width/height of app
        self.title("Travel Weather App")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)


        # labels for the app
        label0 = tk.Label(self, text="Look up weather at your destination", font=("Helvetica", 20))
        label1 = tk.Label(self, text="Select destinations then click Submit", font=("Helvetica", 14))
        label0.grid(row=0, column=0, pady=10)
        label1.grid(row=1, column=0, pady=10)

        # listbox frame
        listbox_frame = tk.Frame(self)
        listbox_frame.grid(row=2, column=0, pady=10)
        listbox_frame.grid_columnconfigure(0, weight=1)
        listbox_frame.grid_rowconfigure(0, weight=1)
        self.listbox = tk.Listbox(listbox_frame, selectmode=tk.MULTIPLE)
        self.listbox.grid(row=0, column=0, sticky="nsew")


        # display the city names
        for region, cities in city_groups.items():
            for city in cities:
                self.listbox.insert(tk.END, f"{region}: {city}")

        submit_button = tk.Button(self, text="Submit", command=self.on_submit)
        submit_button.grid(row=3, column=0, pady=10)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_submit(self):
        """
        Handles the submit button click event. Fetches weather data for selected cities using multithreading.
        """
        selected_indices = self.listbox.curselection()
        selected_cities = []
        for i in selected_indices:
            item_text = self.listbox.get(i).strip()
            if not item_text.endswith(':'):  # Ignore region headers
                city_group, city = item_text.split(": ")
                selected_cities.append((city_group, city))
                city_data = fetch_city_weather(city, self.data)
                DisplayWindow(self, city, city_data)

        self.listbox.selection_clear(0, tk.END)

    def update_search_results(self, city, city_data):
        if not any(result["city"] == city for result in self.search_results):
            self.search_results.append({"city": city, "weather_data": city_data})
            print("Weather data fetched for", city)

    def on_closing(self):
        if self.search_results:
            answer = messagebox.askyesno("Save", "Save your results in a directory of your choice?")
            if answer:
                self.save_search_results()
        self.destroy()

    def save_search_results(self):
        directory = filedialog.askdirectory(initialdir="./", title="Select Directory to Save File")
        if directory:
            filepath = directory + "/weather.txt"
            with open(filepath, "w") as file:
                for result in self.search_results:
                    city = result["city"]
                    weather_data = result["weather_data"]
                    file.write(f"{city}:\n")
                    for row in zip(weather_data['Date'], weather_data['High'],
                                   weather_data['Low'], weather_data['Wind'],
                                   weather_data['UV']):
                        file.write(", ".join(map(str, row)))
                        file.write("\n")
            messagebox.showinfo("File Saved", f"Search results saved to: {filepath}")


class DisplayWindow(tk.Toplevel):
    def __init__(self, master, city, city_data):
        super().__init__(master)

        self.master = master
        self.city = city
        self.search_results = []
        headers = ["Date", "High", "Low", "Wind", "UV"]
        city_data = dict(zip(headers, city_data.values()))


        # title + window setup
        self.title("City Weather")
        self.grid_columnconfigure(0, weight=1)
        for i in range(5):
            self.grid_columnconfigure(i, weight=1)

        # Add the location label at the top center
        location_label = tk.Label(self, text=f"\nWeather for {city}\n", font=("Helvetica", 20))
        location_label.grid(pady=10)

        listbox_frame = tk.Frame(self)
        listbox_frame.grid(padx=10, pady=10)

        # Populate the listbox with some sample items
        for i, key in enumerate(city_data.keys()):
            label = tk.Label(listbox_frame, text=key, font=("Arial", 12, "bold"))
            label.grid(row=0, column=i, padx=5, pady=5)

            listbox = tk.Listbox(listbox_frame, height=len(city_data[key]), width=15)
            listbox.grid(row=1, column=i, padx=5, pady=5)

            # Populate the listbox with data
            for item in city_data[key]:
                listbox.insert(tk.END, item)

        # Update search results in the main window
        self.master.update_search_results(self.city, city_data)


def main():
    pass


if __name__ == "__main__":
    main()
    app = MainWindow()
    app.mainloop()
