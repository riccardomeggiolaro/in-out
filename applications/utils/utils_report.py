from jinja2 import Environment, FileSystemLoader, meta
import os
from applications.router.weigher.types import ReportVariables
import libs.lb_config as lb_config
from modules.md_database.interfaces.subject import SubjectDataDTO
from modules.md_database.interfaces.vector import VectorDataDTO
from modules.md_database.interfaces.driver import DriverDataDTO
from modules.md_database.interfaces.vehicle import VehicleDataDTO
from modules.md_database.interfaces.material import MaterialDataDTO
from modules.md_database.interfaces.operator import OperatorDataDTO
import json

def get_data_variables(in_out):
    report_in = lb_config.g_config["app_api"]["report_in"]
    report_out = lb_config.g_config["app_api"]["report_out"]
    report = report_out if in_out.idWeight2 else report_in
    name_file = ""
    variables = ReportVariables(**{})
    variables.typeSubject = in_out.access.typeSubject.value
    variables.subject = in_out.access.subject if in_out.access.subject else SubjectDataDTO(**{})
    variables.vector = in_out.access.vector if in_out.access.vector else VectorDataDTO(**{})
    variables.driver = in_out.access.driver if in_out.access.driver else DriverDataDTO(**{})
    variables.vehicle = in_out.access.vehicle if in_out.access.vehicle else VehicleDataDTO(**{})
    variables.material = in_out.material if in_out.material else MaterialDataDTO(**{})    
    variables.operator = in_out.weight1.operator if in_out.weight1 and in_out.weight1.operator else in_out.weight2.operator or OperatorDataDTO(**{})
    variables.note = in_out.access.note
    variables.document_reference = in_out.access.document_reference
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

def delete_none_value(data):
    """Recursively removes keys with None values in dictionaries and lists."""
    if isinstance(data, dict):
        # Filter out keys with None values
        return {k: delete_none_value(v) for k, v in data.items() if v is not None}
    elif isinstance(data, list):
        # Remove None values from lists
        return [delete_none_value(item) for item in data if item is not None]
    return data

def get_report_file(report_dir, report_name_file):
    content = os.path.join(report_dir, report_name_file)
    if os.path.exists(content):
        with open(content, 'r', encoding='utf-8') as file:
            return file.read()
    return None

def generate_html_report(reports_dir, report_name_file, v: ReportVariables = None):
    try:
        # Setup path to reports
        env = Environment(loader=FileSystemLoader(reports_dir))
        
        file_path = os.path.join(reports_dir, report_name_file)
        
        # Controlla se è un file JSON o HTML
        if report_name_file.endswith('.json'):
            # Caso JSON: leggi il file e estrai l'HTML dalla chiave "html"
            with open(file_path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)
                html_content = json_data.get('html', '')
            
            # Crea il template dalla stringa HTML
            report = env.from_string(html_content)
            parsed_content = env.parse(html_content)
            
        else:
            # Caso HTML: carica direttamente il template
            report = env.get_template(report_name_file)
            source = env.loader.get_source(env, report_name_file)[0]
            parsed_content = env.parse(source)
        
        # Trova le variabili non dichiarate nel template
        variables = meta.find_undeclared_variables(parsed_content)

        # Create template data dictionary
        report_data = {var: v[var] if v and var in v else None for var in variables}
        
        # Rimuove tutte le variabili con valore None
        report_data = delete_none_value(report_data)

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