import modules.custom.panel_siren.functions.panel as panel
import modules.custom.panel_siren.functions.siren as siren

def send_panel_message():
    panel.send_message(ip="100.100.100.100", port=5200, message="AB123CD")
    
def send_siren_message():
    siren.send_message(ip="100.100.100.101", port=80, endpoint=f"http://100.100.100.101/rpc/Switch.Set?id=0&on=true", username="admin", password="16888")