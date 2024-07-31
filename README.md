# Django Template Converter

## Description

`DjangoTemplateConverter` is a tool for converting HTML templates into Django templates. It finds and copies static files (CSS, JS, images) and creates Django templates from HTML sections marked by comments. Comments should start with the keyword `Start` and end with the keyword `End`. An important condition is that section names should be a single word (e.g., `AboutUs Start` instead of `About Us Start`).

## Features

- **Static Files Copy**: Copies all CSS, JS, and image files to the Django static folder.
- **Template Creation**: Creates separate Django templates for each section and forms a main base template `base.html`.
- **Navbar Link Update**: Updates links in the navbar to use Django's `{% url %}` template tag.
- **URLs Configuration**: Automatically generates a `urls.py` file based on the sections identified in the HTML.
- **Views Creation**: Creates a `views.py` file with a view function for each section.

## Installation and Usage

### Dependencies

Make sure you have the following dependencies installed:
- Python 3.10+
- BeautifulSoup4
- urllib3

### Installation

1. Clone the repository:

   ```sh
   git clone https://github.com/loglux/DjangoTemplateConverter.git
   ```

2. Navigate to the project directory:

   ```sh
   cd DjangoTemplateConverter
   ```

3. Install the dependencies:

   ```sh
   pip install BeuatifulSoup4
   ```

### Usage

1. Create an HTML file with sections marked by comments. For example:
   ```html
   <!-- Header Start -->
   <div>Header Content</div>
   <!-- Header End -->
   <!-- Footer Start -->
   <div>Footer Content</div>
   <!-- Footer End -->
   ```
It is recommended to combine the header and navbar into the same template called navbar, enclosing the necessary parts of the header and navbar within the same comments:
```html
<!-- Navbar Start -->
<div>Header Content</div>
<div>Navbar Content</div>
<!-- Navbar End -->
```

2. Run the script `django_template.py` by specifying the Django app name and the path to your HTML file:
   ```sh
   python django_template.py
   ```

### Example Usage

Example usage of the class:
```python
if __name__ == '__main__':
    app_name = 'portfolio'
    index_file = 'CryptoCoin-1.0.0/index.html'
    converter = TemplateConverter(app_name, index_file)
    converter.run()
```

## License

This project is licensed under the MIT licence.