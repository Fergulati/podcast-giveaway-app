from app import create_app

app = create_app()

if __name__ == '__main__':
    socketio = getattr(app, 'socketio', None)
    if socketio is not None:
        socketio.run(app, debug=True)
    else:
        app.run(debug=True)
