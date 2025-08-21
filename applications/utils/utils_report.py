from jinja2 import Environment, FileSystemLoader, meta
import os
from applications.router.weigher.types import ReportVariables
import libs.lb_config as lb_config
from modules.md_database.interfaces.subject import SubjectDataDTO
from modules.md_database.interfaces.vector import VectorDataDTO
from modules.md_database.interfaces.driver import DriverDataDTO
from modules.md_database.interfaces.vehicle import VehicleDataDTO
from modules.md_database.interfaces.material import MaterialDataDTO

def get_data_variables(in_out):
    report_in = lb_config.g_config["app_api"]["report_in"]
    report_out = lb_config.g_config["app_api"]["report_out"]
    report = report_out if in_out.idWeight2 else report_in
    name_file = ""
    variables = ReportVariables(**{})
    variables.typeSubject = in_out.reservation.typeSubject.value
    variables.subject = in_out.reservation.subject if in_out.reservation.subject else SubjectDataDTO(**{})
    variables.vector = in_out.reservation.vector if in_out.reservation.vector else VectorDataDTO(**{})
    variables.driver = in_out.reservation.driver if in_out.reservation.driver else DriverDataDTO(**{})
    variables.vehicle = in_out.reservation.vehicle if in_out.reservation.vehicle else VehicleDataDTO(**{})
    variables.material = in_out.material if in_out.material else MaterialDataDTO(**{})    
    variables.note = in_out.reservation.note
    variables.document_reference = in_out.reservation.document_reference
    if in_out.idWeight1:
        name_file = f"{in_out.weight1.weigher}_{in_out.weight1.pid}"
        variables.weight1.date = in_out.weight1.date.strftime("%d/%m/%Y %H:%M")
        variables.weight1.pid = in_out.weight1.pid
        variables.weight1.weight = in_out.weight1.weight
    if in_out.idWeight2:
        if in_out.weight2.tare > 0:
            name_file = f"{in_out.weight2.weigher}_{in_out.weight2.pid}"
            variables.weight1.weight = in_out.weight2.tare
            variables.weight1.type = "PT" if in_out.weight2.is_preset_tare else "Tara"
        else:
            name_file = f"{in_out.weight2.weigher}_{in_out.weight1.pid}_{in_out.weight2.pid}"
        variables.weight2.date = in_out.weight2.date.strftime("%d/%m/%Y %H:%M") if in_out.idWeight2 else ""
        variables.weight2.pid = in_out.weight2.pid if in_out.idWeight2 else ""
        variables.weight2.weight = in_out.weight2.weight if in_out.idWeight2 else ""
    variables.net_weight = in_out.net_weight
    name_file += ".pdf"
    return name_file, variables, report

def convert_none_to_empty(data):
    """Recursively converts None values to empty strings in dictionaries and lists"""
    if isinstance(data, dict):
        return {k: convert_none_to_empty(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_none_to_empty(item) for item in data]
    elif data is None:
        return ""
    return data

def generate_html_report(reports_dir, report_name_file, v: ReportVariables =None):
    try:
        # Setup path to reports
        env = Environment(loader=FileSystemLoader(reports_dir))
        
        # Get the template
        report = env.get_template(report_name_file)

        source = env.loader.get_source(env, report_name_file)[0]
        parsed_content = env.parse(source)
        variables = meta.find_undeclared_variables(parsed_content)

        # Create template data dictionary
        report_data = {var: v[var] if v and var in v else None for var in variables}
        
        # Convert all None values to empty strings recursively
        report_data = convert_none_to_empty(report_data)

        # Return the rendered report
        return report.render(**report_data)
        
    except Exception as e:
        raise e

def generate_csv_report(variables: ReportVariables):
    data = [
        variables.typeSubject,
        variables.subject.id if variables.subject.id else '',
        variables.subject.social_reason if variables.subject.social_reason else '',
        variables.subject.telephone if variables.subject.telephone else '',
        variables.subject.cfpiva if variables.subject.cfpiva else '',
        variables.vector.id if variables.vector.id else '',
        variables.vector.social_reason if variables.vector.social_reason else '',
        variables.vector.telephone if variables.vector.telephone else '',
        variables.vector.cfpiva if variables.vector.cfpiva else '',
        variables.driver.id if variables.driver.id else '',
        variables.driver.social_reason if variables.driver.social_reason else '',
        variables.driver.telephone if variables.driver.telephone else '',
        variables.vehicle.id if variables.vehicle.id else '',
        variables.vehicle.plate if variables.vehicle.plate else '',
        variables.vehicle.description if variables.vehicle.description else '',
        variables.material.id if variables.material.id else '',
        variables.material.description if variables.material.description else '',
        variables.note,
        variables.document_reference,
        variables.weight1.date if variables.weight1.date else '',
        variables.weight1.pid if variables.weight1.pid else '',
        variables.weight1.weight if variables.weight1.weight else '',
        variables.weight2.date if variables.weight2.date else '',
        variables.weight2.pid if variables.weight2.pid else '',
        variables.weight2.weight if variables.weight2.weight else '',
        variables.net_weight if variables.net_weight else ''
    ]
    csv_line = ";".join([str(v) for v in data])
    return csv_line

def save_file_dir(dir, name_file, content):
    os.makedirs(dir, exist_ok=True)
    path = os.path.join(dir, name_file)
    # Se content è bytes, salva in modalità binaria, altrimenti salva come testo
    if isinstance(content, bytes):
        with open(path, "wb") as f:
            f.write(content)
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(content))
    return path

def find_file_in_directory(directory, filename):
    # Cammina attraverso la directory
    for root, dirs, files in os.walk(directory):
        if filename in files:
            file_path = os.path.join(root, filename)
            # Apre il file in modalità lettura binaria e ritorna i bytes
            with open(file_path, 'rb') as f:
                return f.read()  # Restituisce i byte del file
    return None