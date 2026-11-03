import pandas as pd
import requests
from io import BytesIO

# Dati
vehicles = [
    {"plate": "GF244EW", "tare": 14840},
    {"plate": "GS772ME", "tare": 15300},
    {"plate": "GY940MC", "tare": 15400},
    {"plate": "EX919XL", "tare": 15580},
    {"plate": "GJ977BL", "tare": 14700},
    {"plate": "GC166GY", "tare": 15400},
    {"plate": "GY917LV", "tare": 14900},
    {"plate": "EL748RH", "tare": 16000},
    {"plate": "GF243EW", "tare": 15000},
    {"plate": "FT365WG", "tare": 15000},
    {"plate": "GC501GL", "tare": 15700},
    {"plate": "CX326NK", "tare": 14200},
    {"plate": "CD239GS", "tare": 15760},
    {"plate": "GP728HD", "tare": 14800},
    {"plate": "GA510ER", "tare": 15500},
    {"plate": "FN384MX", "tare": 14800},
    {"plate": "GH789KX", "tare": 19800},
    {"plate": "HB945YE", "tare": 19800},
    {"plate": "GW276HW", "tare": 19800},
    {"plate": "FJ026YE", "tare": 15600},
    {"plate": "GE245VX", "tare": 16100},
    {"plate": "GH798KX", "tare": 15900},
    {"plate": "FN228MX", "tare": 16100},
    {"plate": "HC743YA", "tare": 15500},
    {"plate": "GW275HW", "tare": 16500},
    {"plate": "GW566HX", "tare": 14700},
    {"plate": "FW016SA", "tare": 14800},
    {"plate": "EA269YE", "tare": 15000},
    {"plate": "GT966BV", "tare": 14900},
    {"plate": "GE293XR", "tare": 14900},
    {"plate": "ES325AE", "tare": 14600},
    {"plate": "GY930MC", "tare": 14700},
    {"plate": "GC719AT", "tare": 15100},
    {"plate": "FD881RX", "tare": 16100},
    {"plate": "DG845DS", "tare": 15000},
    {"plate": "DE356ZB", "tare": 14500},
    {"plate": "DN532EN", "tare": 16300},
    {"plate": "DJ276SM", "tare": 14500},
    {"plate": "CX465NK", "tare": 17200},
    {"plate": "CK919WX", "tare": 15100},
    {"plate": "GS635ME", "tare": 15000},
    {"plate": "FZ622BV", "tare": 15200},
    {"plate": "FZ623BV", "tare": 14500},
    {"plate": "FZ624BV", "tare": 15500},
    {"plate": "FZ626BV", "tare": 15500},
    {"plate": "GE983KB", "tare": 14500},
    {"plate": "ZA525XB", "tare": 13900},
    {"plate": "GY767LZ", "tare": 14100},
    {"plate": "GJ834DD", "tare": 14500},
    {"plate": "GB707EM", "tare": 14200},
    {"plate": "GT561BW", "tare": 14900},
    {"plate": "FV902MK", "tare": 15800},
    {"plate": "GF055HK", "tare": 14700},
    {"plate": "GD689ED", "tare": 14500},
    {"plate": "GV683YD", "tare": 14700},
    {"plate": "GX573DL", "tare": 14300},
    {"plate": "HB600BK", "tare": 14800},
    {"plate": "GM314JC", "tare": 14700},
    {"plate": "FT383WG", "tare": 14600},
    {"plate": "GM152JC", "tare": 14500},
    {"plate": "FR003KF", "tare": 15000},
    {"plate": "HD038AA", "tare": 14300},
    {"plate": "GL440MR", "tare": 14300},
    {"plate": "HD006AA", "tare": 14500},
    {"plate": "HD004AA", "tare": 14400},
    {"plate": "GD688ED", "tare": 14500},
    {"plate": "GT582NF", "tare": 14500},
    {"plate": "FN410YL", "tare": 19400},
    {"plate": "FW785SA", "tare": 18500},
    {"plate": "FW784SA", "tare": 18600},
    {"plate": "GC062GY", "tare": 18300},
    {"plate": "FW457SA", "tare": 15700},
    {"plate": "HC949ER", "tare": 15400},
    {"plate": "GB510EM", "tare": 15100},
    {"plate": "GH429EC", "tare": 15400},
    {"plate": "GJ749BL", "tare": 15200},
    {"plate": "GL801BA", "tare": 18400},
    {"plate": "GF732YW", "tare": 15800},
    {"plate": "GM302DW", "tare": 15000},
    {"plate": "EM710CV", "tare": 15300},
    {"plate": "GF788YW", "tare": 15160},
    {"plate": "DJ033SM", "tare": 15700},
    {"plate": "FE987FL", "tare": 15050},
    {"plate": "HD722PE", "tare": 14550},
    {"plate": "FH128WS", "tare": 15400},
    {"plate": "FH064WV", "tare": 14800},
    {"plate": "PF228GY", "tare": 15700},
    {"plate": "ES289AE", "tare": 14820},
    {"plate": "GM708SR", "tare": 15800},
    {"plate": "GX971JF", "tare": 15400},
    {"plate": "GD682ND", "tare": 15100},
    {"plate": "GL757YN", "tare": 14400},
    {"plate": "GP959HE", "tare": 15000},
    {"plate": "GZ917HE", "tare": 15000},
    {"plate": "FZ884BV", "tare": 15200},
    {"plate": "GS636ME", "tare": 15100},
    {"plate": "GX461LW", "tare": 16200},
    {"plate": "GM689SR", "tare": 15000},
    {"plate": "HC845EZ", "tare": 18700},
    {"plate": "GV950HX", "tare": 18800},
    {"plate": "GB591EM", "tare": 18700},
    {"plate": "FZ251BV", "tare": 19400},
    {"plate": "FT143MJ", "tare": 19140},
    {"plate": "GE732RK", "tare": 19550},
    {"plate": "GJ161WE", "tare": 19480},
    {"plate": "GL804YN", "tare": 19440},
    {"plate": "GL858YN", "tare": 19400},
    {"plate": "GT992CA", "tare": 19200},
    {"plate": "GT993CA", "tare": 19280},
    {"plate": "GD129ND", "tare": 19370},
    {"plate": "HB134FG", "tare": 19490},
    {"plate": "GJ932BL", "tare": 15300},
    {"plate": "FZ062BV", "tare": 14950},
    {"plate": "GV823HX", "tare": 17290},
    {"plate": "DX247PS", "tare": 17480},
    {"plate": "FD997ZS", "tare": 14700},
    {"plate": "HF404CT", "tare": 14700},
    {"plate": "GS813ME", "tare": 15000},
    {"plate": "FT824MJ", "tare": 15000},
    {"plate": "GV498HS", "tare": 16200},
    {"plate": "GJ714BL", "tare": 14780},
    {"plate": "GJ715BL", "tare": 14270},
    {"plate": "GS791ME", "tare": 14700},
    {"plate": "GZ157HT", "tare": 15000},
    {"plate": "GS854ME", "tare": 14230},
    {"plate": "FK491GW", "tare": 14600},
    {"plate": "FM388KP", "tare": 15400},
    {"plate": "GP685RR", "tare": 14000},
    {"plate": "GN602XG", "tare": 14300},
    {"plate": "HC098GW", "tare": 14100},
    {"plate": "HB657CN", "tare": 14500},
    {"plate": "GX968RH", "tare": 14700},
    {"plate": "GD141ED", "tare": 15000},
    {"plate": "GL950BA", "tare": 15700},
    {"plate": "EN428NH", "tare": 14800},
    {"plate": "CY867JM", "tare": 14700},
    {"plate": "GB816HV", "tare": 14800},
    {"plate": "GV480YA", "tare": 16500},
    {"plate": "GM620SR", "tare": 17600},
    {"plate": "GB696BR", "tare": 15900},
    {"plate": "GB920BR", "tare": 15900},
    {"plate": "FR025RE", "tare": 15900},
    {"plate": "FW386SA", "tare": 15000},
    {"plate": "FN055KY", "tare": 15200},
    {"plate": "GP357BJ", "tare": 14800},
    {"plate": "FN062WF", "tare": 14500},
    {"plate": "GH913RD", "tare": 14300},
    {"plate": "GK477MJ", "tare": 14300},
    {"plate": "GF754HK", "tare": 14300},
    {"plate": "FN534KY", "tare": 15000},
    {"plate": "FN535KY", "tare": 15000},
    {"plate": "GK469MJ", "tare": 14300},
    {"plate": "GT096NL", "tare": 14500},
    {"plate": "GK480MJ", "tare": 14300},
    {"plate": "FH268ZA", "tare": 14300},
    {"plate": "FE875FL", "tare": 14300},
    {"plate": "GT723NG", "tare": 14300},
    {"plate": "GX097DN", "tare": 14300},
    {"plate": "GX099DN", "tare": 14300},
    {"plate": "GG371WF", "tare": 14300},
    {"plate": "CB069XY", "tare": 14300},
    {"plate": "FX541DE", "tare": 14300},
    {"plate": "BM493RN", "tare": 14300},
    {"plate": "HB499TH", "tare": 14700},
    {"plate": "FT234WG", "tare": 14300},
    {"plate": "DY498NZ", "tare": 18200},
    {"plate": "BS242RP", "tare": 16100},
    {"plate": "GF726DK", "tare": 14500},
    {"plate": "DZ460AF", "tare": 16300},
    {"plate": "EZ621SH", "tare": 18000},
    {"plate": "EZ619SH", "tare": 18000},
    {"plate": "EZ620SH", "tare": 18000},
    {"plate": "DM784DA", "tare": 17500},
    {"plate": "FV867JR", "tare": 14000},
    {"plate": "FX870DE", "tare": 17700},
    {"plate": "GC740BV", "tare": 14500},
    {"plate": "GE033XS", "tare": 18500},
    {"plate": "GC959LJ", "tare": 14500},
    {"plate": "GP998VB", "tare": 15700}
]

drivers = []

# RAGIONE SOCIALE


vectors = [
    {"social_reason": "FACCHIN CALCESTRUZZI Srl"},
    {"social_reason": "GRUPPO ADIGE BITUMI"},
    {"social_reason": "SASSO Srl"},
    {"social_reason": "GENERAL WORK"},
    {"social_reason": "BAGGIO Srl"},
    {"social_reason": "BERGAMIN"},
    {"social_reason": "PIZZATO TRASPORTI"},
    {"social_reason": "PR TRASPORTI Srl"},
    {"social_reason": "ROSSI ESCAVAZIONI Srl"},
    {"social_reason": "LOGISTICA SPIGOLON"},
    {"social_reason": "SD TRUCK"},
    {"social_reason": "NORD EST SERVICE"},
    {"social_reason": "DS TRASPORTI"},
    {"social_reason": "GIRARDINI"},
    {"social_reason": "FRATELLI GIRARDINI"},
    {"social_reason": "PIZZATO TRASPORTI Srl"},
    {"social_reason": "BATTISTELLO DENIS"},
    {"social_reason": "CRACCO FILIPPO"},
    {"social_reason": "ARRIGANI DANIELE"},
    {"social_reason": "SCUCCATO MARCO"},
    {"social_reason": "L.M COSTRUZIONI"},
    {"social_reason": "BIASIOLO AUTOTRASPORTI"},
    {"social_reason": "VICENTINA TRASPORTI"},
    {"social_reason": "BERGAMIN Srl"},
    {"social_reason": "SARTORELLO TRASPORTI Srl"},
    {"social_reason": "F.LLI FARESIN"},
    {"social_reason": "EDIL MARAGNOLE"},
    {"social_reason": "PALLADIO STRADE"},
    {"social_reason": "BETON CANDEO Srl"},
    {"social_reason": "DRT"},
    {"social_reason": "BASTIANELLO PAOLO STEFANO & C. Sas"},
    {"social_reason": "BA di BIZZOTTO ANTONIO"},
    {"social_reason": "BM di BIZZOTTO MICHAEL"},
    {"social_reason": "FREDEL Srl"},
    {"social_reason": "LUCCA ANGELO Snc"},
    {"social_reason": "FRIGO SRL"},
    {"social_reason": "MAGRIN GIULIANA"},
    {"social_reason": "ZAMBELLO FRATELLI Snc"},
    {"social_reason": "DORO MANFREDO"},
    {"social_reason": "SABBIA BRENTA Srl"},
    {"social_reason": "BASTIANELLO PAOLO Sas"}
]

subjects = [
    {"social_reason": "FACCHIN CALCESTRUZZI Srl"},
    {"social_reason": "GRUPPO ADIGE BITUMI"},
    {"social_reason": "SUPERBETON SpA"},
    {"social_reason": "GIRARDINI SpA"},
    {"social_reason": "BETON CANDEO Srl"},
    {"social_reason": "SABBIA BRENTA Srl"}
]

materials = [
    {"description": "Ghiaia in Natura DoP"}
]

card_registry = [
  { "number": "A001", "code": "3C00CBC1A0" },
  { "number": "A002", "code": "3C00CBFD75" },
  { "number": "A003", "code": "3C00CBF455" },
  { "number": "A004", "code": "3C00B57B9A" },
  { "number": "A005", "code": "3C00CB92D2" },
  { "number": "A006", "code": "3C00CB52656" },
  { "number": "A007", "code": "3C00B71835" },
  { "number": "A008", "code": "3C00B5402B" },
  { "number": "A009", "code": "3C00CB78BA" },
  { "number": "A010", "code": "3C00B70E4C" },
  { "number": "A011", "code": "3C00B638A8" },
  { "number": "A012", "code": "3C00CA2603" },
  { "number": "A013", "code": "3C00CBE10D" },
  { "number": "A014", "code": "3C00C871BC" },
  { "number": "A015", "code": "3C00CAD737" },
  { "number": "A016", "code": "3C00B58FEC" },
  { "number": "A017", "code": "3C00CA5F12" },
  { "number": "A018", "code": "3C00CA04F8" },
  { "number": "A019", "code": "3C00CA03EB" },
  { "number": "A020", "code": "3C00CABD69" },
  { "number": "A021", "code": "3C00B5A760" },
  { "number": "A022", "code": "3C00CBAD19" },
  { "number": "A023", "code": "3C00CB43DF" },
  { "number": "A024", "code": "3C00B5D437" },
  { "number": "A025", "code": "3C00CA4B2A" },
  { "number": "A026", "code": "3C00CC2C04" },
  { "number": "A027", "code": "3C00B6C548" },
  { "number": "A028", "code": "3C00B6729B" },
  { "number": "A029", "code": "3C00CC41B3" },
  { "number": "A030", "code": "3C00C9D1DA" },
  { "number": "A031", "code": "3C00B65BAD" },
  { "number": "A032", "code": "3C00B431C3" },
  { "number": "A033", "code": "3C00B5D941" },
  { "number": "A034", "code": "3C00B54100" },
  { "number": "A035", "code": "3C00CBD3A8" },
  { "number": "A036", "code": "01154A7C55" },
  { "number": "A037", "code": "01154A6DBC" },
  { "number": "A038", "code": "01154A6777" },
  { "number": "A039", "code": "01154A91F9" },
  { "number": "A040", "code": "01154A84C3" },
  { "number": "A041", "code": "01154A8793" },
  { "number": "A042", "code": "01154A865E" },
  { "number": "A043", "code": "01154A5B57" },
  { "number": "A044", "code": "01154A8F83" },
  { "number": "A045", "code": "01154A5BFA" },
  { "number": "A046", "code": "01154A834C" },
  { "number": "A047", "code": "01154A901B" },
  { "number": "A048", "code": "01154A800D" },
  { "number": "A049", "code": "01154A5CCB" },
  { "number": "A050", "code": "01154A7906" }
]

# Token di autenticazione
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwidXNlcm5hbWUiOiJiYXJvbnBlc2kiLCJwYXNzd29yZCI6IiQyYiQxMiRQQUhFNGtoNmxuWG8zdzlTRjl0ajdPamVjbzkxdmdXNzVDcFM5QzBuM0JPNHNoYVdHR08ubSIsImxldmVsIjo0LCJkZXNjcmlwdGlvbiI6ImJhcm9ub3Blc2kiLCJkYXRlX2NyZWF0ZWQiOiIyMDI1LTEwLTMxVDEwOjIyOjEwLjIyODgyNiIsImV4cCI6NDkxNTUwNjk1OH0.EsGLRj73mXHK5hJ-FUyKyy51VKKMvIwODXMi5H4Kpos"

# Funzione per creare e inviare file xlsx
def create_and_upload_xlsx(data, filename, endpoint):
    buffer = BytesIO()
    df = pd.DataFrame(data)
    df.to_excel(buffer, index=False, engine='openpyxl')
    buffer.seek(0)

    files = {'file': (filename, buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    headers = {'Authorization': f'Bearer {AUTH_TOKEN}'}

    try:
        response = requests.post(endpoint, files=files, headers=headers)
        print(f"{filename} → {endpoint}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        print("-" * 60)
        return response
    except Exception as e:
        print(f"Errore con {filename}: {e}")
        print("-" * 60)
        return None

# Base URL
base_url = "http://localhost/api/anagrafic"

# Carica tutti i file
print("Inizio caricamento file xlsx...\n")

create_and_upload_xlsx(vehicles, "vehicle", f"{base_url}/vehicle/upload-file")
create_and_upload_xlsx(drivers, "driver", f"{base_url}/driver/upload-file")
create_and_upload_xlsx(vectors, "vector", f"{base_url}/vector/upload-file")
create_and_upload_xlsx(subjects, "subject", f"{base_url}/subject/upload-file")
create_and_upload_xlsx(materials, "material", f"{base_url}/material/upload-file")
create_and_upload_xlsx(card_registry, "card-registry", f"{base_url}/card-registry/upload-file")

print("\nCaricamento completato!")