from django.shortcuts import render
import pyowm
from pyowm.utils import timestamps
from datetime import timedelta
import requests
import json
import googlemaps

# Create your views here.

# API Key 입력 부분
API_Key = 'a3a57abdc75d6bd277763f8062aa14cd'
owm = pyowm.OWM(API_Key)

# 날씨 정보 알려주는 메서드 객체 생성
mgr=owm.weather_manager()

def index(request):
    return render(request, 'weather/index.html')

def current(request):
    return render(request, 'weather/current.html')

def display(request):
    try:
        city_name = request.POST['city']
        obs = mgr.weather_at_place(city_name)
        weather = obs.weather
        weather_dict = {
            'Clear': '맑음',
            'Clouds': '흐림',
            'Rain': '비',
            'Thunderstorm': '폭풍우',
            'Snow': '눈',
            'Mist': '안개'
        }
        # 기온
        temperature = weather.temperature('celsius')

        # 바람 관련
        wind = weather.wind(unit='beaufort')
        wind_speed = wind['speed']
        wind_deg = wind['deg']

        # 풍속 (보퍼트 풍력 계급)
        if 0 <= wind_speed <= 4:
            wind_speed = '약한 바람'

        elif wind_speed <= 6:
            wind_speed = '조금 강한 바람'

        elif wind_speed <= 8:
            wind_speed = '강한 바람'

        elif wind_speed <= 12:
            wind_speed = '매우 강한 바람'

        # 풍향
        if (0<= wind_deg <= 10) or (340 < wind_deg <= 360):
            wind_deg = '북'
        elif 10 < wind_deg <= 30:
            wind_deg ='북북동'
        elif 30 < wind_deg <= 50:
            wind_deg = '북동'
        elif 50 < wind_deg <= 70:
            wind_deg = '동북동'
        elif 70 < wind_deg <= 100:
            wind_deg = '동'
        elif 100 < wind_deg <= 120:
            wind_deg = '동남동'
        elif 120 < wind_deg <= 140:
            wind_deg = '남동'
        elif 140 < wind_deg <= 160:
            wind_deg = '남남동'
        elif 160 < wind_deg <= 190:
            wind_deg = '남'
        elif 190 < wind_deg <= 210:
            wind_deg = '남남서'
        elif 210 < wind_deg <= 230:
            wind_deg = '남서'
        elif 230 < wind_deg <= 250:
            wind_deg = '서남서'
        elif 250 < wind_deg <= 280:
            wind_deg = '서'
        elif 280 < wind_deg <= 300:
            wind_deg = '서북서'
        elif 300 < wind_deg <= 320:
            wind_deg = '북서'
        elif 320 < wind_deg <= 340:
            wind_deg = '북북서'

        # 일출, 일몰 시간
        sunrise = weather.sunrise_time(timeformat='date')
        sunrise += timedelta(hours=9)
        sunset = weather.sunset_time(timeformat='date')
        sunset += timedelta(hours=9)

        # 내일의 날씨
        three_h_forecast = mgr.forecast_at_place(city_name, '3h')
        tomorrow = timestamps.tomorrow()
        tomorrow += timedelta(hours=9)
        tomorrow_weather = three_h_forecast.get_weather_at(tomorrow)

        # 내일 비가 옴?
        tomorrow_is_rain = '아뇽'
        rain_list=[]
        rain_flag=1
        for i in range(0,24):
            time = i
            tomorrow_time = timestamps.tomorrow(time,0)
            tomorrow_specific_weather = three_h_forecast.get_weather_at(tomorrow_time).status
            if tomorrow_specific_weather == 'Rain':
                rain_list.append(time)
                rain_flag = 0

        if len(rain_list)!=0 and rain_flag==0:
            if len(rain_list)==1:
                tomorrow_is_rain = '넹 %d시에 옵니당' %rain_list[0]
            elif 2<=len(rain_list):
                tomorrow_is_rain = '넹 %d시부터 %d시까지 옵니당' %(rain_list[0],rain_list[-1])

        # 내일 눈이 옴?
        tomorrow_is_snow = '아뇽'
        snow_list = []
        snow_flag=1
        for i in range(0,24):
            time = i
            tomorrow_time = timestamps.tomorrow(time,0)
            tomorrow_specific_weather = three_h_forecast.get_weather_at(tomorrow_time).status
            if tomorrow_specific_weather == 'Snow':
                snow_list.append(time)
                snow_flag=0

        if len(snow_list)!=0 and snow_flag==0:
            if len(snow_list)==1:
                tomorrow_is_snow = '넹 %d시에 옵니당' %snow_list[0]
            elif 2<=len(snow_list):
                tomorrow_is_snow = '넹 %d시부터 %d시까지 옵니당' %(snow_list[0],snow_list[-1])


        gmaps = googlemaps.Client(key='AIzaSyCmM3vFXEdl5yuuWqJApoxPF0H67jWqHAY')
        geocode_result = gmaps.geocode((city_name))
        lat = geocode_result[0]['geometry']['location']['lat']
        lng = geocode_result[0]['geometry']['location']['lng']
        air_url = 'http://api.openweathermap.org/data/2.5/' \
              'air_pollution/forecast?lat=%f&lon=%f&appid=' % (lat, lng)
        mykey = 'a3a57abdc75d6bd277763f8062aa14cd'
        air_url += mykey
        r = requests.get(air_url)
        data = json.loads(r.text)
        pm10 = data['list'][0]['components']['pm10']
        aqi = data['list'][0]['main']['aqi']

        if 0<=pm10<=30:
            pm10 = '좋음'
        elif 30<pm10<=80:
            pm10 = '보통'
        elif 80<pm10<=150:
            pm10 = '나쁨'
        elif 150<pm10:
            pm10 = '매우 나쁨'

        if aqi == 1:
            aqi = '매우 좋음'
        elif aqi == 2:
            aqi = '좋음'
        elif aqi == 3:
            aqi = '보통'
        elif aqi == 4:
            aqi = '나쁨'
        elif aqi == 5:
            aqi = '매우 나쁨'

        ctx = {
            'weather' : weather_dict[weather.status],
            'temperature' : temperature['temp'],
            'wind_speed' : wind_speed,
            'wind_deg' : wind_deg,
            'tomorrow_weather' : weather_dict[tomorrow_weather.status],
            'tomorrow_is_rain' : tomorrow_is_rain,
            'tomorrow_is_snow' : tomorrow_is_snow,
            'pm10' : pm10,
            'aqi' : aqi,
            'cityname' : city_name,

        }
    except:
        return render(request, 'weather/citynameerror.html')

    return render(request, 'weather/displayweather.html',ctx)