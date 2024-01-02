from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)


import model
import logic


MAX_TITLE_LENGTH = 30
MAX_TEXT_LENGTH = 200


class ApiException(Exception):
    pass

events = {} 
event_id_counter = 1

def generate_event_id():
    global event_id_counter
    event_id = event_id_counter
    event_id_counter += 1
    return event_id


def _from_raw(raw_event: str) -> model.Event:
    parts = raw_event.split('|')
    if len(parts) == 3:
        event = model.Event()
        event.id = generate_event_id()
        try:
            event.date = datetime.strptime(parts[0], '%Y-%m-%d').date()
        except ValueError:
            raise ApiException('Invalid date format. Please use the format YYYY-MM-DD.')
        event.title = str(parts[1])
        event.text = str(parts[2])
        return event
    else:
        raise ApiException(f"Invalid RAW event data{raw_event}")


def _to_raw(event: model.Event) -> str:
    return f"{event.date}|{event.title}|{event.text}"

API_ROOT = "/api/v1/calendar/"
EVENT_API_ROOT = API_ROOT + "/event"


@app.route(EVENT_API_ROOT + "/", methods=["POST"])
def create():
    try:
        data = str(request.get_data(as_text=True))
        event = _from_raw(data)

        if len(event.title) > MAX_TITLE_LENGTH or len(event.text) > MAX_TEXT_LENGTH:
            raise ApiException(
                f'Maximum title length is {MAX_TITLE_LENGTH} characters, maximum text length is {MAX_TEXT_LENGTH} characters.')

        if event.date in events:
            raise ApiException('An event already exists for this date.')

        events[event.id] = {'date': event.date, 'title': event.title, 'text': event.text}
        return jsonify({'message': 'Event created successfully.'}), 201

    except ApiException as e:
        return jsonify({'error': str(e)}), 400


@app.route(EVENT_API_ROOT + "/", methods=["GET"])
def list_events():
    return jsonify(events)


@app.route(EVENT_API_ROOT + "/<_date>/", methods=["GET"])
def read_event(_date: str):
    try:
        event_date = datetime.strptime(_date, '%Y-%m-%d').date()
        event = events.get(event_date)
        if event:
            return jsonify(event)
        else:
            return jsonify({'error': 'Event not found.'}), 404

    except ValueError:
        return jsonify({'error': 'Invalid date format.'}), 400


@app.route(EVENT_API_ROOT + "/<_date>/", methods=["PUT"])
def update_event(_date: str):
    try:
        event_date = datetime.strptime(_date, '%Y-%m-%d').date()
        event = events.get(event_date)
        if event:
            data = str(request.get_data(as_text=True))
            new_event = _from_raw(data)

            if len(new_event.title) > MAX_TITLE_LENGTH or len(new_event.text) > MAX_TEXT_LENGTH:
                raise ApiException(
                    f'Maximum title length is {MAX_TITLE_LENGTH} characters, maximum text length is {MAX_TEXT_LENGTH} characters.')

            event['title'] = new_event.title
            event['text'] = new_event.text
            return jsonify({'message': 'Event updated successfully.'})

        else:
            return jsonify({'error': 'Event not found.'}), 404

    except (ApiException, ValueError) as e:
        return jsonify({'error': str(e)}), 400


@app.route(EVENT_API_ROOT + "/<_date>/", methods=["DELETE"])
def delete_event(_date: str):
    try:
        event_date = datetime.strptime(_date, '%Y-%m-%d').date()
        if event_date in events:
            del events[event_date]
            return jsonify({'message': 'Event deleted successfully.'})
        else:
            return jsonify({'error': 'Event not found.'}), 404

    except ValueError:
        return jsonify({'error': 'Invalid date format.'}), 400


if __name__ == '__main__':
    app.run(debug=True)
