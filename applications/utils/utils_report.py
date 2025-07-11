from jinja2 import Environment, FileSystemLoader, meta
import libs.lb_config as lb_config
import os

def convert_none_to_empty(data):
    """Recursively converts None values to empty strings in dictionaries and lists"""
    if isinstance(data, dict):
        return {k: convert_none_to_empty(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_none_to_empty(item) for item in data]
    elif data is None:
        return ""
    return data

def generate_report(report_name_file, v=None):
    try:
        # Setup path to templates
        templates_dir = lb_config.g_config["app_api"]["path_reports"]
        env = Environment(loader=FileSystemLoader(templates_dir))
        
        # Get the template
        template = env.get_template(report_name_file)

        source = env.loader.get_source(env, report_name_file)[0]
        parsed_content = env.parse(source)
        variables = meta.find_undeclared_variables(parsed_content)

        # Create template data dictionary
        template_data = {var: v[var] if v and var in v else None for var in variables}
        
        # Convert all None values to empty strings recursively
        template_data = convert_none_to_empty(template_data)

        # Return the rendered template
        return template.render(**template_data)
        
    except Exception as e:
        raise e

def save_file_dir(dir, name_file, bytes_file):
    os.makedirs(dir, exist_ok=True)
    pdf_path = os.path.join(dir, name_file)
    with open(pdf_path, "wb") as f:
        f.write(bytes_file)
    return pdf_path

def find_file_in_directory(directory, filename):
    # Cammina attraverso la directory
    for root, dirs, files in os.walk(directory):
        if filename in files:
            file_path = os.path.join(root, filename)
            # Apre il file in modalità lettura binaria e ritorna i bytes
            with open(file_path, 'rb') as f:
                return f.read()  # Restituisce i byte del file
    return None