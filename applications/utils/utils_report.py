from jinja2 import Environment, FileSystemLoader, meta
import libs.lb_config as lb_config

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

        template_data = {var: v[var] if v and var in v else None for var in variables}

        # Return the raw template without data
        return template.render(**template_data)
        
    except Exception as e:
        raise e