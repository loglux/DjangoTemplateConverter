import os
import re
import shutil
from bs4 import BeautifulSoup, Comment
from urllib.parse import urlparse

class DjangoTemplateConverter:
    def __init__(self, app_name, index_file):
        self.app_name = app_name
        self.index_file = index_file
        self.index_dir = os.path.dirname(index_file)
        self.static_dir = os.path.join(app_name, 'static', app_name)
        self.template_dir = os.path.join(app_name, 'templates', app_name)
        self.setup_directories()
        self.soup = None
        self.sections = {}

    def setup_directories(self):
        os.makedirs(self.static_dir, exist_ok=True)
        os.makedirs(self.template_dir, exist_ok=True)

    def sanitize_filename(self, filename):
        return re.sub(r'[^\w\-_\.\/ ]', '_', filename)

    def read_index_file(self):
        with open(self.index_file, 'r', encoding='utf-8') as file:
            self.soup = BeautifulSoup(file, 'html.parser')

    def find_and_copy_static_files(self):
        static_tags = self.soup.find_all(['link', 'script', 'img'])

        for tag in static_tags:
            if tag.name == 'link' and 'stylesheet' in tag.get('rel', []):
                self.process_static_file(tag, 'href', 'css')
            elif tag.name == 'script':
                self.process_static_file(tag, 'src', 'js')
            elif tag.name == 'img':
                self.process_static_file(tag, 'src', 'img')

    def process_static_file(self, tag, attr, file_type):
        original_path = tag.get(attr)
        if original_path and not urlparse(original_path).scheme:
            local_path = os.path.normpath(os.path.join(self.index_dir, original_path))
            print(f"Original reference: {original_path}")
            print(f"Checking existence of file: {local_path}")

            if os.path.exists(local_path):
                sanitized_name = self.sanitize_filename(original_path)
                new_path = os.path.normpath(os.path.join(self.static_dir, sanitized_name))
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                shutil.copy2(local_path, new_path)
                tag[attr] = f"{{% static '{self.app_name}/{sanitized_name}' %}}"
                print(f"Copied {local_path} to {new_path}")

                # If it's a CSS file, scan for additional URLs inside it
                if file_type == 'css':
                    self.scan_css_for_static_files(local_path, sanitized_name)

    def scan_css_for_static_files(self, css_file_path, css_sanitized_name):
        with open(css_file_path, 'r', encoding='utf-8') as css_file:
            css_content = css_file.read()
            urls = re.findall(r'url\(([^)]+)\)', css_content)
            for url in urls:
                url = url.strip('"').strip("'")
                if not urlparse(url).scheme:  # Skip absolute URLs
                    static_file_path = os.path.normpath(os.path.join(os.path.dirname(css_file_path), url))
                    print(f"Found static file in CSS: {static_file_path}")
                    if os.path.exists(static_file_path):
                        sanitized_name = self.sanitize_filename(os.path.relpath(static_file_path, self.index_dir))
                        new_path = os.path.normpath(os.path.join(self.static_dir, sanitized_name))
                        print(f"Attempting to create directory: {os.path.dirname(new_path)}")
                        os.makedirs(os.path.dirname(new_path), exist_ok=True)
                        shutil.copy2(static_file_path, new_path)
                        print(f"Copied {static_file_path} to {new_path}")

                        # Update the CSS content with the new path
                        new_url = f"{{% static '{self.app_name}/{sanitized_name}' %}}"
                        css_content = css_content.replace(url, new_url)

            # Write the updated CSS content back to the file
            updated_css_path = os.path.normpath(os.path.join(self.static_dir, css_sanitized_name))
            with open(updated_css_path, 'w', encoding='utf-8') as css_file:
                css_file.write(css_content)
                print(f"Updated CSS file written to: {updated_css_path}")

    def analyze_template(self):
        comments = self.soup.find_all(string=lambda text: isinstance(text, Comment))
        print("All comments found in the HTML file:")
        for comment in comments:
            print(f"Comment: {comment}")

        for i, comment in enumerate(comments):
            comment = comment.strip()  # Remove leading and trailing whitespace
            if 'Start' in comment:
                section_name = comment.split(' ')[0].strip()
                if section_name:  # Only consider non-empty section names
                    self.sections[section_name] = {'start': i}
                    print(f"Found section start: {section_name}")
            elif 'End' in comment:
                section_name = comment.split(' ')[0].strip()
                if section_name and section_name in self.sections:
                    self.sections[section_name]['end'] = i
                    print(f"Found section end: {section_name}")

    def extract_section(self, section_name):
        start_comment = f'{section_name} Start'
        end_comment = f'{section_name} End'
        comments = self.soup.find_all(string=lambda text: isinstance(text, Comment))
        start_idx = end_idx = -1
        for i, comment in enumerate(comments):
            if start_comment in comment:
                start_idx = i
            elif end_comment in comment:
                end_idx = i
        if start_idx != -1 and end_idx != -1:
            elements = comments[start_idx].find_all_next(limit=(end_idx - start_idx))
            section_content = ''.join(str(elem) for elem in elements)
            return section_content
        return ""

    def create_template_file(self, filename, content):
        template_path = os.path.join(self.template_dir, filename)
        os.makedirs(os.path.dirname(template_path), exist_ok=True)
        with open(template_path, 'w', encoding='utf-8') as file:
            file.write(content)

    def convert_to_django_templates(self):
        # Extract sections and create individual section templates
        for section_name in self.sections:
            content = self.extract_section(section_name)
            content = f"{{% load static %}}\n{{% block {section_name.lower()} %}}\n{content}\n{{% endblock %}}"
            self.create_template_file(f'{section_name.lower()}.html', content)

        # Create base template
        head_content = self.soup.head.prettify()
        body_scripts = [str(script) for script in self.soup.body.find_all('script')]
        body_script_tags = '\n'.join(body_scripts)

        base_template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <title>{{% block title %}}Your Site Title{{% endblock %}}</title>
            {{% load static %}}
            {head_content}
        </head>
        <body>
            {{% include 'navbar.html' %}}
            {{% block content %}}{{% endblock %}}
            {{% include 'footer.html' %}}
            {body_script_tags}
        </body>
        </html>
        """
        self.create_template_file('base.html', base_template)

        # Create index template
        index_content = "{% extends 'base.html' %}\n{% block content %}\n"
        for section_name in self.sections:
            if section_name.lower() not in ['navbar', 'footer']:
                index_content += f"    {{% include '{section_name.lower()}.html' %}}\n"
        index_content += "{% endblock %}\n"
        self.create_template_file('index.html', index_content)

    def run(self):
        self.read_index_file()
        self.find_and_copy_static_files()
        self.analyze_template()
        print(f"Template analysis complete. Sections found: {self.sections}")

        self.convert_to_django_templates()

# Пример использования класса
if __name__ == '__main__':
    app_name = 'portfolio'
    index_file = ('CryptoCoin-1.0.0/index.html')
    converter = DjangoTemplateConverter(app_name, index_file)
    converter.run()
