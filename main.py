import flask
from datetime import datetime

app = flask.Flask(__name__)
@app.route('/')
def index():
    # return the index page
    return flask.render_template('index.html')

@app.route('/empty_classrooms', methods=['POST'])
def empty_classrooms():
    data = flask.request.json

    # Extract data from request
    day = data.get('day')
    start_time = data.get('startTime')
    end_time = data.get('endTime')
    floors = data.get('floors', [])

    print(f"Received request for empty classrooms:")
    print(f"  Date: {day}")
    print(f"  Time: {start_time} to {end_time}")
    print(f"  Floors: {floors}")

    print(f"Received data: day={day}, start_time={start_time}, end_time={end_time}, floors={floors}")

    # Format day as dd-mm-yyyy for scraper
    formatted_date = datetime.strptime(day, '%Y-%m-%d').strftime('%d-%m-%Y')

    # Call scraper function
    from scraper import scrap
    empty_rooms = scrap(
        day=formatted_date,
        start=start_time,
        end=end_time,
        floors=floors
    )

    # Format room information
    result = []
    for room_name in empty_rooms:
        building = room_name.split('.')[0]
        floor = int(room_name.split('.')[1][1:2])
        result.append({
            'name': room_name,
            'building': building,
            'floor': floor
        })

    return flask.jsonify(result)



if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)