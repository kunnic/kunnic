import time
import json
from lxml import etree

# Dữ liệu tĩnh thay thế cho các truy vấn API GitHub
KUNNIC_PAYLOAD = """
{
  "title": "kunnic.com",
  "subtitle": "Personal Website",
  "sections": [
    {
      "id": "about",
      "title": "About Me",
      "icon": "user",
      "iconColor": "text-blue-600",
      "content": {
        "greeting": "Hello! I'm Duc Huy NGUYEN, also known as Kunnic.",
        "description": "As a final-year Computer Science student with a special interest in the world of video games and music, I, Kunnic, created this website for both myself and for those I love."
      }
    },
    {
      "id": "os",
      "title": "OS Edition",
      "icon": "windows",
      "iconColor": "text-blue-600",
      "content": {
        "edition": "kunnic OS - 2025 Creative Edition build 1.0.0",
        "copyright": "Copyright © 2004 The Kunnic Corporation. All rights reserved."
      }
    },
    {
      "id": "system",
      "title": "System Information",
      "icon": "computer",
      "iconColor": "text-green-600",
      "content": {
        "cpu": {
          "name": "kunnic's Voyager Gen I",
          "specs": [
            { "name": "Creative", "speed": "3.14GHz", "color": "blue" },
            { "name": "Analysis", "speed": "10.17GHz", "color": "green" },
            { "name": "Discipline", "speed": "2.71GHz", "color": "orange" },
            { "name": "Thinking", "speed": "10.28GHz", "color": "purple" }
          ]
        },
        "memory": {
          "total": "32GB Creative RAM",
          "breakdown": [
            { "name": "Gaming", "size": "16GB", "color": "blue" },
            { "name": "Composing", "size": "8GB", "color": "green" },
            { "name": "Youtube Shorts", "size": "2GB", "color": "red" },
            { "name": "Coding", "size": "2GB", "color": "orange" },
            { "name": "for Zou JiaJia ❤️", "size": "1.5GB", "color": "pink" },
            { "name": "Philosophy", "size": "0.5GB", "color": "gray" }
          ]
        },
        "cache": [
          { "level": "L1", "name": "Ultra-Fast Gaming Respond Cache", "color": "red" },
          { "level": "L2", "name": "Medium Music Theory Processing Cache", "color": "yellow" },
          { "level": "L3", "name": "Deep Philosophy Buffer", "color": "gray" }
        ],
        "apu": {
          "name": "Integrated Hi-Fi Audio Processor for Classical Music",
          "color": "indigo"
        },
        "storage": [
          { "name": "1TB Passion SSD", "color": "green" },
          { "name": "∞ Dream Cloud", "color": "purple" }
        ],
        "architecture": {
          "type": "64-bit Dreamer-based OS",
          "version": "kunnicOS v2025.1 (Creative Edition)"
        }
      }
    },
    {
      "id": "computer-info",
      "title": "Computer Name, Domain, and Workgroup Settings",
      "icon": "network",
      "iconColor": "text-indigo-600",
      "content": {
        "computerName": "KUNNIC",
        "fullComputerName": "kunnic.social.network",
        "description": "A work in progress. Handle with care.",
        "workgroup": "KUNNIC_OUTPOST_DISCORD"
      }
    },
    {
      "id": "activation",
      "title": "Activation",
      "icon": "shield",
      "iconColor": "text-green-600",
      "content": {
        "status": "Fully activated by Passion and Curiosity.",
        "isActivated": true
      }
    },
    {
      "id": "contact",
      "title": "Get in Touch",
      "icon": "contact",
      "iconColor": "text-blue-600",
      "content": {
        "description": "Feel free to reach out for collaborations, questions, or just to say hi!",
        "links": [
          {
            "type": "email",
            "label": "Email Me",
            "url": "mailto:kunnic@gmail.com",
            "color": "bg-blue-500 hover:bg-blue-600"
          },
          {
            "type": "linkedin",
            "label": "LinkedIn",
            "url": "https://www.linkedin.com/in/kunnic",
            "color": "bg-blue-600 hover:bg-blue-700"
          },
          {
            "type": "github",
            "label": "GitHub",
            "url": "https://github.com/kunnic",
            "color": "bg-gray-800 hover:bg-gray-900"
          }
        ],
        "footer": "Made with ❤️ using React & Django"
      }
    }
  ]
}
"""

def data_parser(json_payload):
    """
    Returns a loaded dictionary from the raw JSON payload
    """
    return json.loads(json_payload)


def section_getter(data, section_id):
    """
    Returns the content of a specific section from the loaded JSON data.
    Acts similarly to the GraphQL getters in the original script.
    """
    for section in data['sections']:
        if section['id'] == section_id:
            return section['content']
    raise Exception(f"Section {section_id} not found in the payload.")


def find_and_replace(root, element_id, new_text):
    """
    Finds the element in the SVG file and replaces its text with a new value
    """
    element = root.find(f".//*[@id='{element_id}']")
    if element is not None:
        element.text = str(new_text)


def justify_format(root, element_id, new_text, length=0):
    """
    Updates and formats the text of the element, and modifes the amount of dots in the previous element to justify the new text on the svg
    """
    new_text = str(new_text)
    find_and_replace(root, element_id, new_text)
    just_len = max(0, length - len(new_text))
    if just_len <= 2:
        dot_map = {0: '', 1: ' ', 2: '. '}
        dot_string = dot_map[just_len]
    else:
        dot_string = ' ' + ('.' * just_len) + ' '
    find_and_replace(root, f"{element_id}_dots", dot_string)


def svg_overwrite(filename, about_data, os_data, system_data, comp_data, act_data, contact_data):
    """
    Parse SVG files and update elements with Kunnic's system and personal profile data
    """
    tree = etree.parse(filename)
    root = tree.getroot()
    
    # Mapping Data to SVG IDs
    justify_format(root, 'about_greeting', about_data['greeting'])
    justify_format(root, 'os_edition', os_data['edition'])
    justify_format(root, 'cpu_name', system_data['cpu']['name'])
    justify_format(root, 'memory_total', system_data['memory']['total'])
    justify_format(root, 'apu_name', system_data['apu']['name'])
    justify_format(root, 'architecture', system_data['architecture']['type'])
    justify_format(root, 'computer_name', comp_data['computerName'])
    justify_format(root, 'activation_status', act_data['status'])
    
    # Example for parsing arrays in JSON
    github_url = next((link['url'] for link in contact_data['links'] if link['type'] == 'github'), '')
    justify_format(root, 'github_contact', github_url)

    tree.write(filename, encoding='utf-8', xml_declaration=True)


def perf_counter(funct, *args):
    """
    Calculates the time it takes for a function to run
    Returns the function result and the time differential
    """
    start = time.perf_counter()
    funct_return = funct(*args)
    return funct_return, time.perf_counter() - start


def formatter(query_type, difference, funct_return=False, whitespace=0):
    """
    Prints a formatted time differential
    Returns formatted result if whitespace is specified, otherwise returns raw result
    """
    print('{:<23}'.format('   ' + query_type + ':'), sep='', end='')
    print('{:>12}'.format('%.4f' % difference + ' s ')) if difference > 1 else print('{:>12}'.format('%.4f' % (difference * 1000) + ' ms'))
    if whitespace:
        return f"{'{:,}'.format(funct_return): <{whitespace}}"
    return funct_return


if __name__ == '__main__':
    """
    Duc Huy NGUYEN (Kunnic), 2024-2025
    """
    print('Calculation times:')
    
    # Parse payload
    parsed_data, parse_time = perf_counter(data_parser, KUNNIC_PAYLOAD)
    formatter('payload parse', parse_time)

    # Fetch sections mimicking API calls
    about_data, about_time = perf_counter(section_getter, parsed_data, 'about')
    formatter('about getter', about_time)
    
    os_data, os_time = perf_counter(section_getter, parsed_data, 'os')
    formatter('os info getter', os_time)

    system_data, system_time = perf_counter(section_getter, parsed_data, 'system')
    formatter('system info getter', system_time)

    comp_data, comp_time = perf_counter(section_getter, parsed_data, 'computer-info')
    formatter('computer info getter', comp_time)

    act_data, act_time = perf_counter(section_getter, parsed_data, 'activation')
    formatter('activation getter', act_time)
    
    contact_data, contact_time = perf_counter(section_getter, parsed_data, 'contact')
    formatter('contact getter', contact_time)

    # Overwrite SVG
    try:
        svg_overwrite('dark_mode.svg', about_data, os_data, system_data, comp_data, act_data, contact_data)
        svg_overwrite('light_mode.svg', about_data, os_data, system_data, comp_data, act_data, contact_data)
    except FileNotFoundError:
        print("\n[!] Error: dark_mode.svg or light_mode.svg not found. Create template SVG files first.")

    total_time = parse_time + about_time + os_time + system_time + comp_time + act_time + contact_time

    # move cursor to override 'Calculation times:' with 'Total function time:' and the total function time, then move cursor back
    print('\033[F\033[F\033[F\033[F\033[F\033[F\033[F\033[F\033[F',
          '{:<21}'.format('Total function time:'), '{:>11}'.format('%.4f' % total_time),
          ' s \033[E\033[E\033[E\033[E\033[E\033[E\033[E\033[E\033[E', sep='')