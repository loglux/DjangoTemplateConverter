# Django Template Converter

## Description

`DjangoTemplateConverter` is a tool for converting HTML templates into Django templates. It finds and copies static files (CSS, JS, images) and creates Django templates from HTML sections marked by comments. Comments should start with the keyword `Start` and end with the keyword `End`. An important condition is that section names should be a single word (e.g., `AboutUs Start` instead of `About Us Start`).

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

### Project Features

The project provides the following functionalities:

- **Section Conversion**: Converts multi-word section names to single-word by removing spaces (e.g., `AboutUs Start`).
- **Static Files Copy**: Copies all CSS, JS, and image files to the Django static folder.
- **Template Creation**: Creates separate Django templates for each section and forms a main base template `base.html`.

## License

This project is licensed under the MIT licence.