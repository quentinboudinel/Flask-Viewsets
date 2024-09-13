# Flask-Viewsets

`Flask-Viewsets` is a Python package that provides a `ViewSet` class, inheriting from Flask's `View`, inspired by [Django REST Framework](https://github.com/encode/django-rest-framework)'s `ViewSet`. This package aims to streamline the development of RESTful APIs in Flask by offering a simple and flexible class-based view structure for mapping HTTP methods to defined actions on a per route basis.

## Features

- Provides an easy-to-use class-based view to manage HTTP methods.
- Supports all HTTP methods (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`, ...).
- Extensible and customizable for various use cases.

## Installation

You can install `Flask-Viewsets` using pip:

```bash
pip install Flask-Viewsets
```

## Usage

To use the ViewSet class, import it in your Flask application, define a viewset class by inheriting ViewSet, and implement the desired HTTP methods. Here’s a simple example:

```python
# views.py
from flask_viewsets import ViewSet

class ExampleViewSet(ViewSet):
    def hello(self):
        return "Hello, world!"

    def echo(self, message: str):
        return message
```

```python
# app.py
from flask import Flask

from . import views

app = Flask(__name__)
app.add_url_rule('/hello', view_func=views.ExampleViewSet.as_view({
    "get": "hello"
}))
app.add_url_rule('/echo/<string:message>', view_func=views.ExampleViewSet.as_view({
    "get": "echo"
}))

if __name__ == "__main__":
    app.run(debug=True)
```

## Requirements

- Python ^3.12
- Flask ^3.0.3

## Contributing

Contributions are welcome! Please feel free to submit a pull request, file an issue, or suggest improvements.

## License

This project is licensed under the GNU Affero General Public License. See the LICENSE.md file for details.

Enjoy using Flask-Viewsets? Give it a star and help make Flask development easier!
