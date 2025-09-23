import json
import os
from typing import Dict, Optional
from jinja2 import Environment, FileSystemLoader, meta

def convert_none_to_empty(data):
    """Recursively converts None values to empty strings in dictionaries and lists"""
    if isinstance(data, dict):
        return {k: convert_none_to_empty(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_none_to_empty(item) for item in data]
    elif data is None:
        return ""
    return data

def generate_html_report(reports_dir, report_name_file, v):
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

def json_to_html(json_file_path: str, reports_dir: str, report_name_file: str) -> str:
    """
    Trasforma un file JSON in un report HTML utilizzando un template Jinja2.
    
    Args:
        json_file_path (str): Percorso del file JSON contenente i dati.
        reports_dir (str): Directory contenente i template Jinja2.
        report_name_file (str): Nome del file del template Jinja2.
    
    Returns:
        str: Il report HTML generato.
        
    Raises:
        FileNotFoundError: Se il file JSON o il template non esistono.
        json.JSONDecodeError: Se il file JSON non è valido.
        Exception: Per altri errori durante la trasformazione.
    """
    try:
        # Verifica che il file JSON esista
        if not os.path.exists(json_file_path):
            raise FileNotFoundError(f"Il file JSON '{json_file_path}' non esiste.")
        
        # Verifica che il template esista
        template_path = os.path.join(reports_dir, report_name_file)
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Il template '{report_name_file}' non esiste in '{reports_dir}'.")
        
        # Leggi il file JSON
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Converti i dati JSON in un dizionario compatibile con Jinja2
        # Supponiamo che il JSON contenga direttamente le variabili necessarie
        # (es. {"titolo": "Report Mensile", "utente": {"nome": "Mario", "cognome": "Rossi"}, ...})
        report_variables = flatten_json(json_data)
        
        # Chiama la funzione generate_html_report
        return generate_html_report(reports_dir, report_name_file, report_variables)
    
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Errore nel parsing del file JSON: {str(e)}", e.doc, e.pos)
    except Exception as e:
        raise Exception(f"Errore durante la trasformazione JSON in HTML: {str(e)}")

def flatten_json(data: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """
    Appiattisce un dizionario JSON annidato in un dizionario piatto per compatibilità con Jinja2.
    
    Args:
        data (Dict): Dizionario JSON da appiattire.
        parent_key (str): Chiave genitore per la ricorsione.
        sep (str): Separatore per le chiavi annidate.
    
    Returns:
        Dict: Dizionario piatto con chiavi in formato 'parent.child'.
    """
    items = []
    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_json(value, new_key, sep).items())
        else:
            items.append((new_key, value))
    return dict(items)

# Esempio di utilizzo:
# json_file_path = "path/to/data.json"
# reports_dir = "path/to/templates"
# report_name_file = "report_template.html"
# html_output = json_to_html(json_file_path, reports_dir, report_name_file)
# print(html_output)

json_file_path = "/home/riccardo/Scrivania/projects/LOCAL/in-out-new/in-out/applications/static/report/weight_in.json"

reports_dir = "/home/riccardo/Scrivania/projects/LOCAL/in-out-new/in-out/applications/static/report"

report_name_file = "weight_in.html"

html_output = json_to_html(json_file_path, reports_dir, report_name_file)

print(html_output)