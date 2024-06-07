# Name: Wingyi Ng, Shamita Goyal
# lab number: lab 4
# module: process

import requests
import json
import tkinter as tk
from tkinter import messagebox, filedialog
import os
import time
import multiprocessing as mp

def fetchGeo(city):
    '''use multiprocessing to fetch Geo data'''
    website = "https://geocoding-api.open-meteo.com/v1/search?name={}&count=5&language=en&format=json"
    api = website.format(city.replace(" ", "+"))
    page = requests.get(api)
    resultDict = page.json()
    for v in resultDict.values():
        try:
            for d in v:
                if "admin1" in d and d["admin1"] == 'California':
                    return city, [d['latitude'], d['longitude']]
        except TypeError:
            continue

def fetchWeather(geocode, q):
    '''use queue to fetch the Weather Data'''
    k, v = geocode
    if v:
        latitude, longitude = v
        WeatherApi = ("https://api.open-meteo.com/v1/forecast?latitude={}&longitude={}" + 
                      "&daily=temperature_2m_max,temperature_2m_min,uv_index_max,wind_speed_10m_max" +
                      "&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=America%2FLos_Angeles" + 
                      "&past_hours=24&forecast_days=5&forecast_hours=24")
        final = WeatherApi.format(latitude, longitude)
        page = requests.get(final)
        resultDict = page.json()
        q.put((k, resultDict))

def getInfo(filename):
    '''Create a JSON file with all the latitude and longitude of the 10 cities'''
    citiesD = {"North Bay": ('Napa', 'Sonoma'), 'The Coast':("Santa Cruz", "Monterey"), 'East Bay': ("Berkeley", "Livermore"), 
               'Peninsula': ("San Francisco", "San Mateo"), 'South Bay': ('San Jose', 'Los Gatos')}
    cities = [city for region in citiesD.values() for city in region]
    #start = time.time()
    with mp.Pool(processes=10) as pool:
        geocodes = pool.map(fetchGeo, cities)
        
    #print("elapsed time: ", time.time() - start) #n5 0.70s 
    data = {k: v for k, v in geocodes if v}
    
    with open(filename, 'w') as fh:
        json.dump(data, fh, indent=3)

class MainWindow(tk.Tk):
    '''Create the main window'''
    def __init__(self, filename='info.json'):
        super().__init__()
        self.title("Travel Weather App")
        title = "Look up weather at your destination"
        tk.Label(self, text=title, fg="tomato", font=("Helvetica", 25)).grid(padx=5, pady=5)
        purpose = "Select destinations then click submit"
        tk.Label(self, text=purpose, fg="tomato", font=("Helvetica", 18)).grid(padx=5, pady=5)

        self.aList = ['North Bay: Napa', 'North Bay: Sonoma', 'The Coast: Santa Cruz', "The Coast: Monterey",
                      'East Bay: Berkeley', "East Bay: Livermore", 'Peninsula: San Francisco', "Peninsula: San Mateo",
                      'South Bay: San Jose', 'South Bay: Los Gatos']
        self.LB = tk.Listbox(self, height=10, width=30, selectmode="multiple", font=("Helvetica", 18))
        self.LB.insert(tk.END, *self.aList)
        self.LB.grid(padx=5, pady=5)

        tk.Button(text="submit", font=("Helvetica", 23), command=self.submit).grid(padx=15, pady=15)

        if not os.path.exists(filename):
            getInfo(filename)
        with open(filename, 'r') as f:
            self.geocodes = json.load(f)
        
        self.protocol("WM_DELETE_WINDOW", self.close)

    def submit(self):
        '''api request for the cities selected'''
        cities = [self.aList[i].split(": ")[1] for i in self.LB.curselection()]
        geocodes = [(city, self.geocodes.get(city)) for city in cities if city in self.geocodes]

        #start = time.time()
        q = mp.Queue()
        processes = [mp.Process(target=fetchWeather, args=(geocode, q)) for geocode in geocodes]
        
        for p in processes:
            p.start()
        
        results = [q.get() for i in processes]
        for p in processes:
            p.join()

        for city, resultDict in results:
            if resultDict:
                DisplayWindow(self, city, resultDict)

        #print(f"Total elapsed time: {time.time()-start:.2f}s") #n6 # 0.77s
        self.LB.selection_clear(0, tk.END)

    def close(self):
        if DisplayWindow.weatherData:
            if messagebox.askokcancel("Save", "Save your results in a directory of your choice?"):
                self.output()
        self.destroy()
    
    def output(self):
        directory = filedialog.askdirectory(initialdir=".")
        if directory:
            filepath = os.path.join(directory, "weather.txt")
            with open(filepath, 'w') as file:
                for city, data in DisplayWindow.weatherData.items():
                    file.write(f"{city}:\n")
                    dates = list(data.keys())
                    file.write(", ".join(dates) + "\n")
                    
                    high = [data[date][0] for date in dates]
                    file.write(", ".join(map(str, high)) + "\n")
                    
                    low = [data[date][1] for date in dates]
                    file.write(", ".join(map(str, low)) + "\n")
                    
                    wind = [data[date][2] for date in dates]
                    file.write(", ".join(map(str, wind)) + "\n")

                    uv = [data[date][3] for date in dates]
                    file.write(", ".join(map(str, uv)) + "\n")

            messagebox.showinfo("Save", f"File weather.txt has been saved in {filepath}")

class DisplayWindow(tk.Toplevel):
    '''Window to display weather data for a city.'''
    weatherData = {}
    def __init__(self, master, city, resultDict):
        super().__init__(master)
        self.title("City Weather")
        tk.Label(self, text=f"Weather for {city}", font=("Helvetica", 25)).grid(row=0, columnspan=5, pady=10)
        
        headers = ["Date", "High", "Low", "Wind", "UV"]
        for idx, header in enumerate(headers):
            tk.Label(self, text=header, font=("Helvetica", 18)).grid(row=1, column=idx)
        
        date = resultDict["daily"]["time"]
        high = resultDict["daily"]["temperature_2m_max"]
        low = resultDict["daily"]["temperature_2m_min"]
        wind = resultDict["daily"]["wind_speed_10m_max"]
        UV = resultDict["daily"]["uv_index_max"]

        LBs = []
        widths = [10, 5, 5, 5, 5]
        for idx in range(5):
            LB = tk.Listbox(self, height=5, width=widths[idx], font=("Helvetica", 18))
            LB.grid(row=2, column=idx, padx=7, pady=7)
            LBs.append(LB)

        OutData = {}
        for i in range(len(date)):
            LBs[0].insert(tk.END, date[i])
            LBs[1].insert(tk.END, high[i])
            LBs[2].insert(tk.END, low[i])
            LBs[3].insert(tk.END, wind[i])
            LBs[4].insert(tk.END, UV[i])

            dateOut = date[i]
            highOut = high[i]
            lowOut = low[i]
            windOut = wind[i]
            UVOut = UV[i]
            OutData[dateOut] = [highOut, lowOut, windOut, UVOut]

        DisplayWindow.weatherData[city] = OutData

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()

'''
                    serial          multithreading      multiprocessing
geocoding data      5.63                  1.56               0.70
weather data    5.83 (10 cities)   1.4 (10 cities)    0.78 (10 cities)

'''

'''
 to make the API requests (series, multithreading, multiprocessing) in order from slowest to fastest
 the order would be series then multithreading then multiprocessing
 because serial requests are one request at a time, which mean one api request after another
 and with multithreading, each thread handles an api request, while one thread is waiting, others can make requests 
 the fastest should be multiprocessing with a better cpu, each process can assign an api request
 '''
