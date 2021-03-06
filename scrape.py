import lxml.html
import requests
import string, datetime, os, csv, time, random, sys

# Set time in between requests
SLEEP_TIME = 7200 # 2 hours
SLEEP_TIME_BUFFER = 900 # 15 mins

URL = 'https://www.grousemountain.com/current_conditions'

# information for output csv
schema = ['date', 'time', 'temp_celsius', 'high', 'low', 'weather', 'status', 'report_type', 'today_forecast', 'tomorrow_forecast', 'snow_12hr', 'snow_24hr', 'snow_48hr', 'snow_overnight', 'snow_7days', 'snow_total', 'snow_snowmaking', 'snow_peak', 'snow_plateau']
csv_name = 'grouse_weather_report.csv'

# Parses html into list
def parse_text(text):
    return list(filter(lambda x: len(x) > 0, text.split('\n')))

# Parses temperature from string
def get_temp(text, temp_type):
    print(text)
    # Flurries. High:-4 Low: -6
    temp = ''
    if temp_type in text:
        if temp_type + ': ' in text:
            split = text.split(temp_type + ': ')
        else:
            split = text.split(temp_type + ':')
        split = split[1].split(' ')
        temp = split[0]
    return temp

def main(*args):
    # Scrape data from website
    while True:
        # No point parsing data before 5AM
        d = datetime.datetime.now()

        if len(args) > 1:
            d = d - datetime.timedelta(hours=8)
        if d.hour < 6 or d.hour > 23:
            print('Sleeping at {} ... Trying again in 40 mins.'.format(str(d)))
            time.sleep(2000)
            continue

        response = requests.get(URL)
        tree = lxml.html.fromstring(response.text)
        #tree = lxml.html.parse('sample.html').getroot() # for testing

        # Check if season is winter
        season = tree.find_class("menu-item--active")[0].xpath('./form/input/@value')[0]
        if season.lower() != 'winter':
            print('Winter is no more.')
            return
        date, current_time = str(d).split(' ')

        # Current temp/conditions
        conditions = tree.xpath('//div[@class="current-weather__content"]')[0].text_content()
        parsed_conditions = parse_text(conditions)
        celsius = parsed_conditions[0][:-2]
        weather = parsed_conditions[-1]
        current_status = tree.xpath('//div[@class="current_status"]')[0].text_content()
        parsed_status = parse_text(current_status)
        status = '{} {}'.format(*parsed_status[:2])
        report_type = '{} {}'.format(*parsed_status[2:4])

        # Weather forecaset
        forecast = tree.xpath('//div[@class="forecast"]')[0].text_content()
        parsed_forecast = parse_text(forecast)
        today, tomorrow = parsed_forecast[1], parsed_forecast[3]
        high_today = get_temp(today, 'High')
        low_today = get_temp(today, 'Low')

        # Short term snow totals
        snow_today = tree.find_class("conditions-snow-report__stats-day")[0].text_content()
        parsed_snow_today = parse_text(snow_today)
        snow_12hr = parsed_snow_today[1].strip(string.ascii_letters)
        snow_24hr = parsed_snow_today[7].strip(string.ascii_letters)
        snow_48hr = parsed_snow_today[10].strip(string.ascii_letters)
        snow_overnight = parsed_snow_today[4].strip(string.ascii_letters)

        # Long term snow totals
        snow_summary = tree.find_class('conditions-snow-report__stats-season')[0].text_content()
        parsed_snow_summary = parse_text(snow_summary)
        snow_7days = parsed_snow_summary[1].strip(string.ascii_letters)
        snow_total = parsed_snow_summary[4].strip(string.ascii_letters)
        snow_snowmaking = parsed_snow_summary[7].strip(string.ascii_letters)
        snow_peak = parsed_snow_summary[10].strip(string.ascii_letters)
        snow_plateau = parsed_snow_summary[13].strip(string.ascii_letters)

        # Write to CSV
        row = [date, current_time, celsius, high_today, low_today, weather, status, report_type, today, tomorrow, snow_12hr, snow_24hr, snow_48hr, snow_overnight, snow_7days, snow_total, snow_snowmaking, snow_peak, snow_plateau]
        print(row)

        file_exists = os.path.exists(csv_name)
        mode = 'a' if file_exists else 'w'
        with open(csv_name, mode) as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(schema)
            writer.writerow(row)

        delay = SLEEP_TIME + (random.random() * SLEEP_TIME_BUFFER)
        print('Sleeping for {}'.format(str(datetime.timedelta(seconds=delay))))
        time.sleep(delay)

if __name__ == '__main__':
    main(*sys.argv)
