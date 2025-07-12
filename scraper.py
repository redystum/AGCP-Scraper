from datetime import datetime
import requests
from bs4 import BeautifulSoup
import json

URL = "https://publico.agcp.ipleiria.pt/paginas/ScheduleRptSalasSemanalPublico.aspx"

rooms = {
    "0": [
        "A.S0.5",
        "A.S0.6",
        "A.S0.8",
        "A.S0.9"
    ], 
    "1": [
        "A.S1.1",
        "A.S1.10",
        "A.S1.12",
        "A.S1.13",
        "A.S1.14",
        "A.S1.6",
        "A.S1.7",
        "A.S1.8",
        "A.S1.9"
    ],
    "2": [
        "A.S2.03",
        "A.S2.04",
        "A.S2.05",
        "A.S2.08",
        "A.S2.09",
        "A.S2.10",
        "A.S2.11",
        "A.S2.12",
        "A.S2.13",
        "A.S2.14",
        "A.S2.15"
    ]
}


def fetch_initial_page():
    try:
        response = requests.get(URL)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching initial page: {e}")
        return None


def extract_hidden_fields(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    viewstate = soup.find('input', {'name': '__VIEWSTATE'})['value']
    viewstategenerator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})['value']
    eventvalidation = soup.find('input', {'name': '__EVENTVALIDATION'})['value']

    return viewstate, viewstategenerator, eventvalidation


def submit_form(classroom_option, viewstate, viewstategenerator, eventvalidation):
    formdata = {
        '__EVENTTARGET': 'ctl00$PlaceHolderMain$ddlSalas',
        '__EVENTARGUMENT': '',
        '__VIEWSTATE': viewstate,
        '__VIEWSTATEGENERATOR': viewstategenerator,
        '__EVENTVALIDATION': eventvalidation,
        'ctl00$PlaceHolderMain$ddlSalas': classroom_option
    }

    try:
        response = requests.post(URL, data=formdata)
        response.raise_for_status()  # Raise an error for bad responses
        return response.text
    except requests.RequestException as e:
        print(f"Error submitting form: {e}")
        return None


def get_room_schedule(classroom):
    initial_page_html = fetch_initial_page()
    if not initial_page_html:
        return None

    viewstate, viewstategenerator, eventvalidation = extract_hidden_fields(initial_page_html)

    soup = BeautifulSoup(initial_page_html, 'html.parser')
    classroom_option = soup.select_one(
        'select[name="ctl00$PlaceHolderMain$ddlSalas"] option:-soup-contains("{}")'.format(classroom))

    if not classroom_option:
        print("Classroom A.S2.10 not found in options.")
        return None

    classroom_value = classroom_option['value']

    calendar_page_html = submit_form(classroom_value, viewstate, viewstategenerator, eventvalidation)

    if calendar_page_html:
        print("Form submitted successfully. Calendar page HTML fetched.")

        # get the line that start with c.events =
        soup = BeautifulSoup(calendar_page_html, 'html.parser')
        script_tag = soup.find('script', string=lambda t: t and 'c.events =' in t)
        if script_tag:
            script_content = script_tag.string
            start_index = script_content.find('c.events =') + len('c.events =')
            end_index = script_content.find('c.eventsAllDay', start_index)
            events_data = script_content[start_index:end_index].strip()[:-1]  # Remove trailing semicolon
            print("Events data extracted successfully.")
            return events_data
        else:
            print("No events data found in the calendar page.")
            return None

    else:
        print("Failed to fetch calendar page after form submission.")
        return None


def scrap(day: str, start: str, end: str, floors: list):
    empty = []
    start_time = datetime.strptime(f"{day} {start}", "%d-%m-%Y %H:%M")
    end_time = datetime.strptime(f"{day} {end}", "%d-%m-%Y %H:%M")
    available_rooms = []
    for floor in floors:
        if floor in rooms:
            available_rooms.extend(rooms[floor])
    if not available_rooms:
        print("No rooms available for the specified floors.")
        return []
    
    print(f"Checking rooms on floors: {floors}")
    for room in available_rooms:
        events_data = get_room_schedule(room)
        if not events_data:
            print("No events data available for the specified classroom.")
            continue

        data = json.loads(events_data)

        is_empty = True
        for event in data:
            event_start = datetime.strptime(event['Start'], "%B %d, %Y %H:%M:%S %z").replace(tzinfo=None)
            event_end = datetime.strptime(event['End'], "%B %d, %Y %H:%M:%S %z").replace(tzinfo=None)

            if start_time.date() != event_start.date():
                continue

            if event_start < end_time and event_end > start_time:
                is_empty = False
                print(f"Room {room} is occupied from {event_start} to {event_end}.")
                break

        if is_empty:
            empty.append(room)
            print(f"Room {room} is empty from {start_time} to {end_time}.")

    return empty


if __name__ == "__main__":
    empty = scrap(
        day="08-07-2025",
        start="16:00",
        end="18:30",
        floors=["2"]
    )

    print("Empty rooms:", empty)
