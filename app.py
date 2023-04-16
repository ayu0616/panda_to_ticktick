from flask import Flask

from main import main as main_func

app = Flask(__name__)


@app.route("/")
def index():
    main_func()
    return "Finished!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
