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
        self.menu_items = set()  # To keep menu items

    def setup_directories(self):
        os.makedirs(self.static_dir, exist_ok=True)
        os.makedirs(self.template_dir, exist_ok=True)

    def sanitize_filename(self, filename):
        # Replace invalid characters but preserve directory structure
        return re.sub(r'[^\w\-_\.\/\\]', '_', filename)

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

            # Regex to match URLs in various CSS properties, excluding gradient functions
            css_content = re.sub(
                r'url\(\s*["\']?(?!.*?(?:linear-gradient|radial-gradient|repeating-linear-gradient).*?)\s*(.*?)\s*["\']?\s*\)',
                lambda match: self.replace_with_static(match, css_file_path),
                css_content
            )
            updated_css_path = os.path.normpath(os.path.join(self.static_dir, css_sanitized_name))
            with open(updated_css_path, 'w', encoding='utf-8') as css_file:
                css_file.write(css_content)
                print(f"Updated CSS file written to: {updated_css_path}")

    def replace_with_static(self, match, css_file_path):
        url = match.group(1).strip()

        if url.startswith(('http://', 'https://', 'data:', '#')):
            # Ignore absolute URLs, data URIs, and fragment identifiers
            return match.group(0)

        # Split URL into file path and parameters
        url_parts = url.split('?', 1)
        file_path = url_parts[0]
        url_params = '?' + url_parts[1] if len(url_parts) > 1 else ''

        static_image_path = os.path.normpath(os.path.join(os.path.dirname(css_file_path), file_path))
        print(f"Found image URL in CSS: {static_image_path}")

        if os.path.exists(static_image_path):
            sanitized_name = self.sanitize_filename(os.path.relpath(static_image_path, self.index_dir))
            new_path = os.path.normpath(os.path.join(self.static_dir, sanitized_name))
            print("Debugging New path: " + new_path)
            print("Debugging static image path: " + static_image_path)
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            shutil.copy2(static_image_path, new_path)
            print(f"Copied {static_image_path} to {new_path}")
            relative_path = new_path.replace(self.static_dir, '/static/' + self.app_name).replace("\\", "/")
            # Return URL with parameters preserved
            return f'url("{relative_path}{url_params}")'
        else:
            print(f"Warning: {static_image_path} does not exist.")
            return match.group(0)

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
        start_idx = -1
        for i, comment in enumerate(comments):
            if start_comment in comment:
                start_idx = i
                break
        if start_idx != -1:
            comment = comments[start_idx]
            section_content = ''
            while comment:
                comment = comment.next_sibling
                if comment and isinstance(comment, Comment) and end_comment in comment:
                    break
                if comment and not isinstance(comment, Comment):
                    section_content += str(comment)
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

        # Create head template
        head_content = self.soup.head.prettify()
        head_template = f"""{{% load static %}}\n{head_content}"""
        self.create_template_file('head.html', head_template)

        # Create body scripts template
        body_scripts = [str(script) for script in self.soup.body.find_all('script')]
        body_script_tags = '\n'.join(body_scripts)
        body_scripts_template = f"""{{% load static %}}\n{body_script_tags}"""
        self.create_template_file('body_scripts.html', body_scripts_template)

        # Create base template
        base_template = \
"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>{% block title %}Your Site Title{% endblock %}</title>
    {% include 'head.html' %}
</head>
<body>
    {% include 'navbar.html' %}
    {% block content %}{% endblock %}
    {% include 'footer.html' %}
    {% include 'body_scripts.html' %}
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

    def update_navbar_links(self):
        """
        Updates links in the navbar.html file.
        """
        # Path to the navbar.html file
        navbar_file_path = os.path.join(self.template_dir, 'navbar.html')
        # Check if the file exists
        if not os.path.exists(navbar_file_path):
            print(f"File {navbar_file_path} does not exist.")
            return
        try:
            # Read the content of the file
            with open(navbar_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            # Update the links
            updated_content = self.update_navbar_links_in_content(content)
            # Write the updated content back to the file
            # Utilising the create_template_file method
            self.create_template_file('navbar.html', updated_content)
            print(f"Updated navbar links in {navbar_file_path}")
        except IOError as e:
            print(f"An error occurred while processing the file: {e}")

    def update_navbar_links_in_content(self, content):
        """
        Update links in the passed content.
        Save the original link (like index.html, about.html, etc) in the self.menu_items list.
        """
        def replace_href(match):
            href = match.group(1).strip()
            if href.endswith('.html'):
                name = href.rsplit('.', 1)[0]  # Remove ".html" from the link
                new_href = f'href="{{% url \'{name}\' %}}"'
                print(f"Replacing: href=\"{href}\" with {new_href}")
                self.menu_items.add(href)  # Save the original links to self.menu_items
                return new_href
            return match.group(0)
        # Update only links that end with .html
        updated_content = re.sub(r'href="([^"]+\.html)"', replace_href, content)
        return updated_content

    def create_urls_file(self):
        urls_content = \
f"""from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
"""
        for menu_item_name in self.menu_items:
            if menu_item_name != 'index.html':
                urls_content += f"    path('{menu_item_name.lower().replace('.html', '')}/', views.{menu_item_name.lower().replace('.html', '')}, name='{menu_item_name.lower().replace('.html', '')}'),\n"

        urls_content += "]\n"
        urls_file = os.path.join(self.app_name, 'urls.py')
        with open(urls_file, 'w', encoding='utf-8') as file:
            file.write(urls_content)
        print(f"URLs configuration written to: {urls_file}")

    def create_views_file(self):
        views_content = \
f"""from django.shortcuts import render

#def index(request):
#    return render(request, '{self.app_name}/index.html')
"""
        for menu_item_name in self.menu_items:
            views_content += f"""
def {menu_item_name.lower().replace('.html', '')}(request):
    return render(request, '{menu_item_name.lower()}')
"""
        views_file = os.path.join(self.app_name, 'views.py')
        with open(views_file, 'w', encoding='utf-8') as file:
            file.write(views_content)
        print(f"Views configuration written to: {views_file}")

    def run(self):
        self.read_index_file()
        self.find_and_copy_static_files()
        self.analyze_template()
        print(f"Template analysis complete. Sections found: {self.sections}")
        self.convert_to_django_templates()
        self.update_navbar_links()
        self.create_urls_file()
        self.create_views_file()
        print(self.menu_items)

# Usage
if __name__ == '__main__':
    app_name = 'portfolio'
    index_file = 'Kelly/index.html'
    converter = DjangoTemplateConverter(app_name, index_file)
    converter.run()
