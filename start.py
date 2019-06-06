from settings import app
from back import b
from features import f
from user import u
from movie import m
from flask import render_template


@app.route('/')
@app.route('/main')
def e():
    return render_template('movieIndex.html')


if __name__ == '__main__':
    app.register_blueprint(b, url_prefix='/b')
    app.register_blueprint(f, url_prefix='/f')
    app.register_blueprint(u, url_prefix='/u')
    app.register_blueprint(m, url_prefix='/m')
    app.run(debug=True, host='0.0.0.0')
