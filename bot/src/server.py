import json
import os
from flask import request
from src import app
import requests
import time

ACCESS_TOKEN = os.environ.get('FACEBOOK_PAGE_TOKEN')
VERIFY_TOKEN = os.environ.get('FACEBOOK_VERIFY_TOKEN')
FORISMATIC_API_ENDPOINT = 'https://api.forismatic.com/api/1.0/'
GRAPH_API_URL = 'https://graph.facebook.com/v2.6/me/messages?access_token=' + ACCESS_TOKEN
WELCOME_MSGS = [
    'Hey! Welcome to Instant Quote. I will provide you awesome quotes that will motivate and inspire you for the day ahead 😀',
    'Please type "Quote" to get an awesome quote!',
    'One last thing! If you need help, type "HELP" 😅'
]

@app.route('/')
def home():
    return "Welcome to Instant Quote", 200


@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        if request.args.get('hub.verify_token') == VERIFY_TOKEN:
            return request.args.get('hub.challenge')
        return "Wrong verify token"
    elif request.method == 'POST':
        event = json.loads(request.data)
        for entry in event['entry']:
            for messaging_obj in entry['messaging']:
                message = messaging_obj['message']['text']
                sender_id = messaging_obj['sender']['id']
                mark_message_as_seen(sender_id)
                display_typing(sender_id)
                if message in ['Hey', 'hey', 'HEY', 'Hi', 'hi', 'HI', 'Hello', 'hello', 'HELLO']: # Check if the user greets hello
                    for response in WELCOME_MSGS:
                        send_message(response, sender_id)
                        if response is not WELCOME_MSGS[-1]: # If it's not the last welcome message, set typing indication on
                            display_typing(sender_id)
                elif message in ['Quote', 'Quotes', 'quote', 'quotes', 'QUOTE', 'QUOTES']:
                    quote = get_quote()
                    send_message(quote, sender_id)
                elif message in ['Help', 'help', 'HELP']:
                    send_message(WELCOME_MSGS[1], sender_id) # Send information only about the necessary command
                elif message in ['Bye', 'bye', 'BYE']:
                    send_message('Have a nice day and inspire others 😉\nBye 😊', sender_id)
        return 'Instant Quote Bot is now running...', 200


def mark_message_as_seen(sender_id):
    headers = {
        'Content-Type': 'application/json'
    }
    payload = {
        'recipient': {
            'id': sender_id
        },
        'sender_action': 'mark_seen'
    }
    requests.post(GRAPH_API_URL, headers=headers, data=json.dumps(payload))


def display_typing(sender_id, is_typing=True):
    sender_action = 'typing_on' if is_typing else 'typing_off'
    headers = {
        'Content-Type': 'application/json'
    }
    payload = {
        'recipient': {
            'id': sender_id
        },
        'sender_action': sender_action
    }
    requests.post(GRAPH_API_URL, headers=headers, data=json.dumps(payload))


def get_quote():
    params = {
        'method': 'getQuote',
        'format': 'json',
        'lang': 'en'
    }
    response = requests.post(FORISMATIC_API_ENDPOINT, params=params)
    response_json = json.loads(response.text)
    return '{}\n- {}'.format(response_json['quoteText'],response_json['quoteAuthor'])


def send_message(response, sender_id):
    time.sleep(1) # Give one second delay to avoid instant replies
    display_typing(sender_id, is_typing=False)
    headers = {
        'Content-Type': 'application/json'
    }
    payload = {
        'messaging_type': 'RESPONSE',
        'recipient': {
            'id': sender_id
        },
        'message': {
            'text': response
        }
    }
    requests.post(GRAPH_API_URL, headers=headers, data=json.dumps(payload))
