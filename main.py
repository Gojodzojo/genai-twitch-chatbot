from flask import Flask, request

app = Flask(__name__)


@app.route('/message-bot', methods=['GET'])
def message_bot():
    message = request.headers.get('message')
    user = request.headers.get('user')
    return f'🤖 Użytkownik {user} napisał: "{message}". Wiadomość ma {len(message)} znaków'


if __name__ == '__main__':
    app.run(debug=True)
