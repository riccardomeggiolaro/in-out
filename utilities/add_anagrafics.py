import pandas as pd
import requests
from io import BytesIO

# Prenotazioni permanenti (da Database_Targhe_corretto_1.xlsx, fogli 27/10/26 e 28/10/26)
# Ogni riga: cliente, vettore, materiale, targa, tara (kg)
reservations = [
    {"subject": "FACCHIN CALCESTRUZZI Srl", "vector": "FACCHIN CALCESTRUZZI Srl", "material": "Ghiaia in Natura DoP", "plate": "GF244EW", "tare": 14840},
    {"subject": "FACCHIN CALCESTRUZZI Srl", "vector": "FACCHIN CALCESTRUZZI Srl", "material": "Ghiaia in Natura DoP", "plate": "GS772ME", "tare": 15300},
    {"subject": "FACCHIN CALCESTRUZZI Srl", "vector": "FACCHIN CALCESTRUZZI Srl", "material": "Ghiaia in Natura DoP", "plate": "GY940MC", "tare": 15400},
    {"subject": "FACCHIN CALCESTRUZZI Srl", "vector": "FACCHIN CALCESTRUZZI Srl", "material": "Ghiaia in Natura DoP", "plate": "EX919XL", "tare": 15580},
    {"subject": "FACCHIN CALCESTRUZZI Srl", "vector": "FACCHIN CALCESTRUZZI Srl", "material": "Ghiaia in Natura DoP", "plate": "GJ977BL", "tare": 14700},
    {"subject": "FACCHIN CALCESTRUZZI Srl", "vector": "FACCHIN CALCESTRUZZI Srl", "material": "Ghiaia in Natura DoP", "plate": "GC166GY", "tare": 15400},
    {"subject": "FACCHIN CALCESTRUZZI Srl", "vector": "FACCHIN CALCESTRUZZI Srl", "material": "Ghiaia in Natura DoP", "plate": "GY917LV", "tare": 14900},
    {"subject": "FACCHIN CALCESTRUZZI Srl", "vector": "FACCHIN CALCESTRUZZI Srl", "material": "Ghiaia in Natura DoP", "plate": "EL748RH", "tare": 16000},
    {"subject": "FACCHIN CALCESTRUZZI Srl", "vector": "FACCHIN CALCESTRUZZI Srl", "material": "Ghiaia in Natura DoP", "plate": "GF243EW", "tare": 15000},
    {"subject": "FACCHIN CALCESTRUZZI Srl", "vector": "FACCHIN CALCESTRUZZI Srl", "material": "Ghiaia in Natura DoP", "plate": "FT365WG", "tare": 15000},
    {"subject": "FACCHIN CALCESTRUZZI Srl", "vector": "FACCHIN CALCESTRUZZI Srl", "material": "Ghiaia in Natura DoP", "plate": "GC501GL", "tare": 15700},
    {"subject": "FACCHIN CALCESTRUZZI Srl", "vector": "FACCHIN CALCESTRUZZI Srl", "material": "Ghiaia in Natura DoP", "plate": "CX326NK", "tare": 14200},
    {"subject": "FACCHIN CALCESTRUZZI Srl", "vector": "FACCHIN CALCESTRUZZI Srl", "material": "Ghiaia in Natura DoP", "plate": "CD239GS", "tare": 15760},
    {"subject": "FACCHIN CALCESTRUZZI Srl", "vector": "FACCHIN CALCESTRUZZI Srl", "material": "Ghiaia in Natura DoP", "plate": "HD968PN", "tare": 15300},
    {"subject": "GRUPPO ADIGE BITUMI", "vector": "GRUPPO ADIGE BITUMI", "material": "Ghiaia in Natura DoP", "plate": "GP728HD", "tare": 14800},
    {"subject": "GRUPPO ADIGE BITUMI", "vector": "GRUPPO ADIGE BITUMI", "material": "Ghiaia in Natura DoP", "plate": "GA510ER", "tare": 15500},
    {"subject": "GRUPPO ADIGE BITUMI", "vector": "GRUPPO ADIGE BITUMI", "material": "Ghiaia in Natura DoP", "plate": "FN384MX", "tare": 14800},
    {"subject": "GRUPPO ADIGE BITUMI", "vector": "GRUPPO ADIGE BITUMI", "material": "Ghiaia in Natura DoP", "plate": "GH789KX", "tare": 19800},
    {"subject": "GRUPPO ADIGE BITUMI", "vector": "GRUPPO ADIGE BITUMI", "material": "Ghiaia in Natura DoP", "plate": "HB945YE", "tare": 19800},
    {"subject": "GRUPPO ADIGE BITUMI", "vector": "GRUPPO ADIGE BITUMI", "material": "Ghiaia in Natura DoP", "plate": "GW276HW", "tare": 19800},
    {"subject": "GRUPPO ADIGE BITUMI", "vector": "GRUPPO ADIGE BITUMI", "material": "Ghiaia in Natura DoP", "plate": "FJ926YE", "tare": 15600},
    {"subject": "GRUPPO ADIGE BITUMI", "vector": "GRUPPO ADIGE BITUMI", "material": "Ghiaia in Natura DoP", "plate": "GE245VX", "tare": 16100},
    {"subject": "GRUPPO ADIGE BITUMI", "vector": "GRUPPO ADIGE BITUMI", "material": "Ghiaia in Natura DoP", "plate": "GH798KX", "tare": 15900},
    {"subject": "GRUPPO ADIGE BITUMI", "vector": "GRUPPO ADIGE BITUMI", "material": "Ghiaia in Natura DoP", "plate": "FN228MX", "tare": 16100},
    {"subject": "GRUPPO ADIGE BITUMI", "vector": "GRUPPO ADIGE BITUMI", "material": "Ghiaia in Natura DoP", "plate": "HC743YA", "tare": 15500},
    {"subject": "GRUPPO ADIGE BITUMI", "vector": "GRUPPO ADIGE BITUMI", "material": "Ghiaia in Natura DoP", "plate": "GW275HW", "tare": 16500},
    {"subject": "GRUPPO ADIGE BITUMI", "vector": "GRUPPO ADIGE BITUMI", "material": "Ghiaia in Natura DoP", "plate": "GW566HX", "tare": 14700},
    {"subject": "GRUPPO ADIGE BITUMI", "vector": "SASSO Srl", "material": "Ghiaia in Natura DoP", "plate": "FW016SA", "tare": 14800},
    {"subject": "GRUPPO ADIGE BITUMI", "vector": "SASSO Srl", "material": "Ghiaia in Natura DoP", "plate": "EA269YE", "tare": 15000},
    {"subject": "GRUPPO ADIGE BITUMI", "vector": "GENERAL WORK", "material": "Ghiaia in Natura DoP", "plate": "GT966BV", "tare": 14900},
    {"subject": "GRUPPO ADIGE BITUMI", "vector": "GENERAL WORK", "material": "Ghiaia in Natura DoP", "plate": "GE293XR", "tare": 14900},
    {"subject": "GRUPPO ADIGE BITUMI", "vector": "GENERAL WORK", "material": "Ghiaia in Natura DoP", "plate": "ES325AE", "tare": 14600},
    {"subject": "GRUPPO ADIGE BITUMI", "vector": "GENERAL WORK", "material": "Ghiaia in Natura DoP", "plate": "GY930MC", "tare": 14700},
    {"subject": "GRUPPO ADIGE BITUMI", "vector": "GENERAL WORK", "material": "Ghiaia in Natura DoP", "plate": "GC719AT", "tare": 15100},
    {"subject": "GRUPPO ADIGE BITUMI", "vector": "BAGGIO Srl", "material": "Ghiaia in Natura DoP", "plate": "FD881RX", "tare": 16100},
    {"subject": "GRUPPO ADIGE BITUMI", "vector": "BAGGIO Srl", "material": "Ghiaia in Natura DoP", "plate": "DG845DS", "tare": 15000},
    {"subject": "GRUPPO ADIGE BITUMI", "vector": "BAGGIO Srl", "material": "Ghiaia in Natura DoP", "plate": "DE356ZB", "tare": 14500},
    {"subject": "GRUPPO ADIGE BITUMI", "vector": "BAGGIO Srl", "material": "Ghiaia in Natura DoP", "plate": "DN532EN", "tare": 16300},
    {"subject": "GRUPPO ADIGE BITUMI", "vector": "BAGGIO Srl", "material": "Ghiaia in Natura DoP", "plate": "CK919WX", "tare": 15100},
    {"subject": "GRUPPO ADIGE BITUMI", "vector": "BERGAMIN Srl", "material": "Ghiaia in Natura DoP", "plate": "GS635ME", "tare": 15000},
    {"subject": "SUPERBETON SpA", "vector": "PIZZATO TRASPORTI Srl", "material": "Ghiaia in Natura DoP", "plate": "FZ624BV", "tare": 15500},
    {"subject": "SUPERBETON SpA", "vector": "PIZZATO TRASPORTI Srl", "material": "Ghiaia in Natura DoP", "plate": "FZ626BV", "tare": 15500},
    {"subject": "SUPERBETON SpA", "vector": "PR TRASPORTI Srl", "material": "Ghiaia in Natura DoP", "plate": "GE983KB", "tare": 14500},
    {"subject": "SUPERBETON SpA", "vector": "PR TRASPORTI Srl", "material": "Ghiaia in Natura DoP", "plate": "ZA525XB", "tare": 13900},
    {"subject": "SUPERBETON SpA", "vector": "PR TRASPORTI Srl", "material": "Ghiaia in Natura DoP", "plate": "GY767LZ", "tare": 14100},
    {"subject": "SUPERBETON SpA", "vector": "PR TRASPORTI Srl", "material": "Ghiaia in Natura DoP", "plate": "GJ834DD", "tare": 14500},
    {"subject": "SUPERBETON SpA", "vector": "ROSSI ESCAVAZIONI Srl", "material": "Ghiaia in Natura DoP", "plate": "GB707EM", "tare": 14200},
    {"subject": "SUPERBETON SpA", "vector": "ROSSI ESCAVAZIONI Srl", "material": "Ghiaia in Natura DoP", "plate": "GT561BW", "tare": 14900},
    {"subject": "SUPERBETON SpA", "vector": "ROSSI ESCAVAZIONI Srl", "material": "Ghiaia in Natura DoP", "plate": "FV902MK", "tare": 15800},
    {"subject": "SUPERBETON SpA", "vector": "LOGISTICA SPIGOLON", "material": "Ghiaia in Natura DoP", "plate": "GF055HK", "tare": 14700},
    {"subject": "SUPERBETON SpA", "vector": "SD TRUCK", "material": "Ghiaia in Natura DoP", "plate": "GD689ED", "tare": 14500},
    {"subject": "SUPERBETON SpA", "vector": "SD TRUCK", "material": "Ghiaia in Natura DoP", "plate": "GV683YD", "tare": 14700},
    {"subject": "SUPERBETON SpA", "vector": "SD TRUCK", "material": "Ghiaia in Natura DoP", "plate": "GX573DL", "tare": 14300},
    {"subject": "SUPERBETON SpA", "vector": "NORD EST SERVICE", "material": "Ghiaia in Natura DoP", "plate": "HB600BK", "tare": 14800},
    {"subject": "SUPERBETON SpA", "vector": "LOGISTICA SPIGOLON", "material": "Ghiaia in Natura DoP", "plate": "GM314JC", "tare": 14700},
    {"subject": "SUPERBETON SpA", "vector": "LOGISTICA SPIGOLON", "material": "Ghiaia in Natura DoP", "plate": "FT383WG", "tare": 14600},
    {"subject": "SUPERBETON SpA", "vector": "SD TRUCK", "material": "Ghiaia in Natura DoP", "plate": "GM152JC", "tare": 14500},
    {"subject": "SUPERBETON SpA", "vector": "LOGISTICA SPIGOLON", "material": "Ghiaia in Natura DoP", "plate": "FR603KF", "tare": 15000},
    {"subject": "SUPERBETON SpA", "vector": "DS TRASPORTI", "material": "Ghiaia in Natura DoP", "plate": "HD038AA", "tare": 14300},
    {"subject": "SUPERBETON SpA", "vector": "DS TRASPORTI", "material": "Ghiaia in Natura DoP", "plate": "GL440MR", "tare": 14300},
    {"subject": "SUPERBETON SpA", "vector": "DS TRASPORTI", "material": "Ghiaia in Natura DoP", "plate": "HD006AA", "tare": 14500},
    {"subject": "SUPERBETON SpA", "vector": "DS TRASPORTI", "material": "Ghiaia in Natura DoP", "plate": "HD004AA", "tare": 14400},
    {"subject": "SUPERBETON SpA", "vector": "DS TRASPORTI", "material": "Ghiaia in Natura DoP", "plate": "GD688ED", "tare": 14500},
    {"subject": "SUPERBETON SpA", "vector": "DS TRASPORTI", "material": "Ghiaia in Natura DoP", "plate": "GT582NF", "tare": 14500},
    {"subject": "SUPERBETON SpA", "vector": "DORO MANFREDO", "material": "Ghiaia in Natura DoP", "plate": "EZ621SH", "tare": 18000},
    {"subject": "SUPERBETON SpA", "vector": "DORO MANFREDO", "material": "Ghiaia in Natura DoP", "plate": "EZ619SH", "tare": 18000},
    {"subject": "SUPERBETON SpA", "vector": "DORO MANFREDO", "material": "Ghiaia in Natura DoP", "plate": "EZ620SH", "tare": 18000},
    {"subject": "SUPERBETON SpA", "vector": "DORO MANFREDO", "material": "Ghiaia in Natura DoP", "plate": "DM784DA", "tare": 17500},
    {"subject": "GIRARDINI SpA", "vector": "GIRARDINI", "material": "Ghiaia in Natura DoP", "plate": "FN410YL", "tare": 19400},
    {"subject": "GIRARDINI SpA", "vector": "GIRARDINI", "material": "Ghiaia in Natura DoP", "plate": "FW785SA", "tare": 18500},
    {"subject": "GIRARDINI SpA", "vector": "GIRARDINI", "material": "Ghiaia in Natura DoP", "plate": "FW784SA", "tare": 18600},
    {"subject": "GIRARDINI SpA", "vector": "GIRARDINI", "material": "Ghiaia in Natura DoP", "plate": "GC062GY", "tare": 18300},
    {"subject": "GIRARDINI SpA", "vector": "GIRARDINI", "material": "Ghiaia in Natura DoP", "plate": "FW457SA", "tare": 15700},
    {"subject": "GIRARDINI SpA", "vector": "GIRARDINI", "material": "Ghiaia in Natura DoP", "plate": "HC949ER", "tare": 15400},
    {"subject": "GIRARDINI SpA", "vector": "GIRARDINI", "material": "Ghiaia in Natura DoP", "plate": "GB510EM", "tare": 15100},
    {"subject": "GIRARDINI SpA", "vector": "GIRARDINI", "material": "Ghiaia in Natura DoP", "plate": "GH429EC", "tare": 15400},
    {"subject": "GIRARDINI SpA", "vector": "GIRARDINI", "material": "Ghiaia in Natura DoP", "plate": "GJ749BL", "tare": 15200},
    {"subject": "GIRARDINI SpA", "vector": "FRATELLI GIRARDINI", "material": "Ghiaia in Natura DoP", "plate": "GL801BA", "tare": 18400},
    {"subject": "GIRARDINI SpA", "vector": "FRATELLI GIRARDINI", "material": "Ghiaia in Natura DoP", "plate": "GF732YW", "tare": 15800},
    {"subject": "GIRARDINI SpA", "vector": "PIZZATO TRASPORTI Srl", "material": "Ghiaia in Natura DoP", "plate": "FZ622BV", "tare": 15200},
    {"subject": "GIRARDINI SpA", "vector": "PIZZATO TRASPORTI Srl", "material": "Ghiaia in Natura DoP", "plate": "FZ623BV", "tare": 14500},
    {"subject": "GIRARDINI SpA", "vector": "BATTISTELLO DENIS", "material": "Ghiaia in Natura DoP", "plate": "GM302DW", "tare": 15000},
    {"subject": "GIRARDINI SpA", "vector": "CRACCO FILIPPO", "material": "Ghiaia in Natura DoP", "plate": "EM710CV", "tare": 15300},
    {"subject": "GIRARDINI SpA", "vector": "ARRIGANI DANIELE", "material": "Ghiaia in Natura DoP", "plate": "GF788YW", "tare": 15160},
    {"subject": "GIRARDINI SpA", "vector": "SCUCCATO MARCO", "material": "Ghiaia in Natura DoP", "plate": "DJ033SM", "tare": 15700},
    {"subject": "GIRARDINI SpA", "vector": "L.M COSTRUZIONI", "material": "Ghiaia in Natura DoP", "plate": "FE987FL", "tare": 15050},
    {"subject": "GIRARDINI SpA", "vector": "L.M COSTRUZIONI", "material": "Ghiaia in Natura DoP", "plate": "HD722PE", "tare": 14550},
    {"subject": "GIRARDINI SpA", "vector": "L.M COSTRUZIONI", "material": "Ghiaia in Natura DoP", "plate": "FH128WS", "tare": 15400},
    {"subject": "GIRARDINI SpA", "vector": "L.M COSTRUZIONI", "material": "Ghiaia in Natura DoP", "plate": "FH064WV", "tare": 14800},
    {"subject": "GIRARDINI SpA", "vector": "L.M COSTRUZIONI", "material": "Ghiaia in Natura DoP", "plate": "PF228GY", "tare": 15700},
    {"subject": "GIRARDINI SpA", "vector": "L.M COSTRUZIONI", "material": "Ghiaia in Natura DoP", "plate": "ES289AE", "tare": 14820},
    {"subject": "GIRARDINI SpA", "vector": "BIASIOLO AUTOTRASPORTI", "material": "Ghiaia in Natura DoP", "plate": "GM708SR", "tare": 15800},
    {"subject": "GIRARDINI SpA", "vector": "BIASIOLO AUTOTRASPORTI", "material": "Ghiaia in Natura DoP", "plate": "GX971JF", "tare": 15400},
    {"subject": "GIRARDINI SpA", "vector": "VICENTINA TRASPORTI", "material": "Ghiaia in Natura DoP", "plate": "GD682ND", "tare": 15100},
    {"subject": "GIRARDINI SpA", "vector": "VICENTINA TRASPORTI", "material": "Ghiaia in Natura DoP", "plate": "GL757YN", "tare": 14400},
    {"subject": "GIRARDINI SpA", "vector": "BAGGIO Srl", "material": "Ghiaia in Natura DoP", "plate": "DJ276SM", "tare": 14470},
    {"subject": "GIRARDINI SpA", "vector": "BAGGIO Srl", "material": "Ghiaia in Natura DoP", "plate": "CX465NK", "tare": 17160},
    {"subject": "GIRARDINI SpA", "vector": "BERGAMIN Srl", "material": "Ghiaia in Natura DoP", "plate": "GP959HE", "tare": 15000},
    {"subject": "GIRARDINI SpA", "vector": "BERGAMIN Srl", "material": "Ghiaia in Natura DoP", "plate": "GZ917HE", "tare": 15000},
    {"subject": "GIRARDINI SpA", "vector": "BERGAMIN Srl", "material": "Ghiaia in Natura DoP", "plate": "FZ884BV", "tare": 15200},
    {"subject": "GIRARDINI SpA", "vector": "BERGAMIN Srl", "material": "Ghiaia in Natura DoP", "plate": "GS636ME", "tare": 15100},
    {"subject": "GIRARDINI SpA", "vector": "BERGAMIN Srl", "material": "Ghiaia in Natura DoP", "plate": "GX461LW", "tare": 16200},
    {"subject": "GIRARDINI SpA", "vector": "BERGAMIN Srl", "material": "Ghiaia in Natura DoP", "plate": "GM689SR", "tare": 15000},
    {"subject": "GIRARDINI SpA", "vector": "BERGAMIN Srl", "material": "Ghiaia in Natura DoP", "plate": "HC845EZ", "tare": 18700},
    {"subject": "GIRARDINI SpA", "vector": "BERGAMIN Srl", "material": "Ghiaia in Natura DoP", "plate": "GV950HX", "tare": 18800},
    {"subject": "GIRARDINI SpA", "vector": "BERGAMIN Srl", "material": "Ghiaia in Natura DoP", "plate": "GB591EM", "tare": 18700},
    {"subject": "GIRARDINI SpA", "vector": "SARTORELLO TRASPORTI Srl", "material": "Ghiaia in Natura DoP", "plate": "FZ251BV", "tare": 19400},
    {"subject": "GIRARDINI SpA", "vector": "SARTORELLO TRASPORTI Srl", "material": "Ghiaia in Natura DoP", "plate": "FT143MJ", "tare": 19140},
    {"subject": "GIRARDINI SpA", "vector": "SARTORELLO TRASPORTI Srl", "material": "Ghiaia in Natura DoP", "plate": "GE732RK", "tare": 19550},
    {"subject": "GIRARDINI SpA", "vector": "SARTORELLO TRASPORTI Srl", "material": "Ghiaia in Natura DoP", "plate": "GJ161WE", "tare": 19480},
    {"subject": "GIRARDINI SpA", "vector": "SARTORELLO TRASPORTI Srl", "material": "Ghiaia in Natura DoP", "plate": "GL804YN", "tare": 19440},
    {"subject": "GIRARDINI SpA", "vector": "SARTORELLO TRASPORTI Srl", "material": "Ghiaia in Natura DoP", "plate": "GL858YN", "tare": 19400},
    {"subject": "GIRARDINI SpA", "vector": "SARTORELLO TRASPORTI Srl", "material": "Ghiaia in Natura DoP", "plate": "GT992CA", "tare": 19200},
    {"subject": "GIRARDINI SpA", "vector": "SARTORELLO TRASPORTI Srl", "material": "Ghiaia in Natura DoP", "plate": "GT993CA", "tare": 19280},
    {"subject": "GIRARDINI SpA", "vector": "SARTORELLO TRASPORTI Srl", "material": "Ghiaia in Natura DoP", "plate": "GD129ND", "tare": 19370},
    {"subject": "GIRARDINI SpA", "vector": "SARTORELLO TRASPORTI Srl", "material": "Ghiaia in Natura DoP", "plate": "HB134FG", "tare": 19490},
    {"subject": "GIRARDINI SpA", "vector": "SARTORELLO TRASPORTI Srl", "material": "Ghiaia in Natura DoP", "plate": "GJ932BL", "tare": 15300},
    {"subject": "GIRARDINI SpA", "vector": "SARTORELLO TRASPORTI Srl", "material": "Ghiaia in Natura DoP", "plate": "FZ062BV", "tare": 14950},
    {"subject": "GIRARDINI SpA", "vector": "SARTORELLO TRASPORTI Srl", "material": "Ghiaia in Natura DoP", "plate": "GV823HX", "tare": 17290},
    {"subject": "GIRARDINI SpA", "vector": "SARTORELLO TRASPORTI Srl", "material": "Ghiaia in Natura DoP", "plate": "DX247PS", "tare": 17480},
    {"subject": "GIRARDINI SpA", "vector": "F.LLI FARESIN", "material": "Ghiaia in Natura DoP", "plate": "FD997ZS", "tare": 14700},
    {"subject": "GIRARDINI SpA", "vector": "F.LLI FARESIN", "material": "Ghiaia in Natura DoP", "plate": "HF404CT", "tare": 14700},
    {"subject": "GIRARDINI SpA", "vector": "F.LLI FARESIN", "material": "Ghiaia in Natura DoP", "plate": "GS813ME", "tare": 15000},
    {"subject": "GIRARDINI SpA", "vector": "F.LLI FARESIN", "material": "Ghiaia in Natura DoP", "plate": "FT824MJ", "tare": 15000},
    {"subject": "GIRARDINI SpA", "vector": "F.LLI FARESIN", "material": "Ghiaia in Natura DoP", "plate": "GV498HS", "tare": 16200},
    {"subject": "GIRARDINI SpA", "vector": "F.LLI FARESIN", "material": "Ghiaia in Natura DoP", "plate": "GJ714BL", "tare": 14780},
    {"subject": "GIRARDINI SpA", "vector": "F.LLI FARESIN", "material": "Ghiaia in Natura DoP", "plate": "GJ715BL", "tare": 14270},
    {"subject": "GIRARDINI SpA", "vector": "F.LLI FARESIN", "material": "Ghiaia in Natura DoP", "plate": "GS791ME", "tare": 14700},
    {"subject": "GIRARDINI SpA", "vector": "F.LLI FARESIN", "material": "Ghiaia in Natura DoP", "plate": "GZ157HT", "tare": 15000},
    {"subject": "GIRARDINI SpA", "vector": "F.LLI FARESIN", "material": "Ghiaia in Natura DoP", "plate": "GS854ME", "tare": 14230},
    {"subject": "GIRARDINI SpA", "vector": "EDIL MARAGNOLE", "material": "Ghiaia in Natura DoP", "plate": "FK491GW", "tare": 14600},
    {"subject": "GIRARDINI SpA", "vector": "PALLADIO STRADE", "material": "Ghiaia in Natura DoP", "plate": "FM388KP", "tare": 15400},
    {"subject": "BETON CANDEO Srl", "vector": "BETON CANDEO Srl", "material": "Ghiaia in Natura DoP", "plate": "GP685RR", "tare": 14000},
    {"subject": "BETON CANDEO Srl", "vector": "BETON CANDEO Srl", "material": "Ghiaia in Natura DoP", "plate": "GN602XG", "tare": 14300},
    {"subject": "BETON CANDEO Srl", "vector": "BETON CANDEO Srl", "material": "Ghiaia in Natura DoP", "plate": "HC098GW", "tare": 14100},
    {"subject": "BETON CANDEO Srl", "vector": "BETON CANDEO Srl", "material": "Ghiaia in Natura DoP", "plate": "HB657CN", "tare": 14500},
    {"subject": "BETON CANDEO Srl", "vector": "BETON CANDEO Srl", "material": "Ghiaia in Natura DoP", "plate": "GX968RH", "tare": 14700},
    {"subject": "BETON CANDEO Srl", "vector": "DRT", "material": "Ghiaia in Natura DoP", "plate": "GD141ED", "tare": 15000},
    {"subject": "BETON CANDEO Srl", "vector": "BASTIANELLO PAOLO STEFANO & C. Sas", "material": "Ghiaia in Natura DoP", "plate": "GL950BA", "tare": 15700},
    {"subject": "BETON CANDEO Srl", "vector": "BA di BIZZOTTO ANTONIO", "material": "Ghiaia in Natura DoP", "plate": "EN428NH", "tare": 14800},
    {"subject": "BETON CANDEO Srl", "vector": "BA di BIZZOTTO ANTONIO", "material": "Ghiaia in Natura DoP", "plate": "CY867JM", "tare": 14700},
    {"subject": "BETON CANDEO Srl", "vector": "BA di BIZZOTTO ANTONIO", "material": "Ghiaia in Natura DoP", "plate": "GB816HV", "tare": 14800},
    {"subject": "BETON CANDEO Srl", "vector": "BM di BIZZOTTO MICHAEL", "material": "Ghiaia in Natura DoP", "plate": "GV480YA", "tare": 16500},
    {"subject": "BETON CANDEO Srl", "vector": "FREDEL Srl", "material": "Ghiaia in Natura DoP", "plate": "GM620SR", "tare": 17600},
    {"subject": "BETON CANDEO Srl", "vector": "LUCCA ANGELO Snc", "material": "Ghiaia in Natura DoP", "plate": "GB696BR", "tare": 15900},
    {"subject": "BETON CANDEO Srl", "vector": "LUCCA ANGELO Snc", "material": "Ghiaia in Natura DoP", "plate": "GB920BR", "tare": 15900},
    {"subject": "BETON CANDEO Srl", "vector": "LUCCA ANGELO Snc", "material": "Ghiaia in Natura DoP", "plate": "FR025RE", "tare": 15900},
    {"subject": "BETON CANDEO Srl", "vector": "FRIGO SRL", "material": "Ghiaia in Natura DoP", "plate": "FW386SA", "tare": 15000},
    {"subject": "BETON CANDEO Srl", "vector": "FRIGO SRL", "material": "Ghiaia in Natura DoP", "plate": "FN655KY", "tare": 15200},
    {"subject": "BETON CANDEO Srl", "vector": "FRIGO SRL", "material": "Ghiaia in Natura DoP", "plate": "GP357BJ", "tare": 14800},
    {"subject": "BETON CANDEO Srl", "vector": "FRIGO SRL", "material": "Ghiaia in Natura DoP", "plate": "FN962WF", "tare": 14500},
    {"subject": "BETON CANDEO Srl", "vector": "MAGRIN GIULIANA", "material": "Ghiaia in Natura DoP", "plate": "GH913RD", "tare": 14300},
    {"subject": "BETON CANDEO Srl", "vector": "MAGRIN GIULIANA", "material": "Ghiaia in Natura DoP", "plate": "GK477MJ", "tare": 14300},
    {"subject": "BETON CANDEO Srl", "vector": "MAGRIN GIULIANA", "material": "Ghiaia in Natura DoP", "plate": "GF754HK", "tare": 14300},
    {"subject": "BETON CANDEO Srl", "vector": "MAGRIN GIULIANA", "material": "Ghiaia in Natura DoP", "plate": "FN534KY", "tare": 15000},
    {"subject": "BETON CANDEO Srl", "vector": "MAGRIN GIULIANA", "material": "Ghiaia in Natura DoP", "plate": "FN535KY", "tare": 15000},
    {"subject": "BETON CANDEO Srl", "vector": "MAGRIN GIULIANA", "material": "Ghiaia in Natura DoP", "plate": "GK469MJ", "tare": 14300},
    {"subject": "BETON CANDEO Srl", "vector": "MAGRIN GIULIANA", "material": "Ghiaia in Natura DoP", "plate": "GT096NL", "tare": 14500},
    {"subject": "BETON CANDEO Srl", "vector": "MAGRIN GIULIANA", "material": "Ghiaia in Natura DoP", "plate": "GK480MJ", "tare": 14300},
    {"subject": "BETON CANDEO Srl", "vector": "MAGRIN GIULIANA", "material": "Ghiaia in Natura DoP", "plate": "FH268ZA", "tare": 14300},
    {"subject": "BETON CANDEO Srl", "vector": "MAGRIN GIULIANA", "material": "Ghiaia in Natura DoP", "plate": "FE875FL", "tare": 14300},
    {"subject": "BETON CANDEO Srl", "vector": "MAGRIN GIULIANA", "material": "Ghiaia in Natura DoP", "plate": "GT723NG", "tare": 14300},
    {"subject": "BETON CANDEO Srl", "vector": "MAGRIN GIULIANA", "material": "Ghiaia in Natura DoP", "plate": "GX097DN", "tare": 14300},
    {"subject": "BETON CANDEO Srl", "vector": "MAGRIN GIULIANA", "material": "Ghiaia in Natura DoP", "plate": "GX099DN", "tare": 14300},
    {"subject": "BETON CANDEO Srl", "vector": "MAGRIN GIULIANA", "material": "Ghiaia in Natura DoP", "plate": "GG371WF", "tare": 14300},
    {"subject": "BETON CANDEO Srl", "vector": "MAGRIN GIULIANA", "material": "Ghiaia in Natura DoP", "plate": "CB069XY", "tare": 14300},
    {"subject": "BETON CANDEO Srl", "vector": "MAGRIN GIULIANA", "material": "Ghiaia in Natura DoP", "plate": "FX541DE", "tare": 14300},
    {"subject": "BETON CANDEO Srl", "vector": "MAGRIN GIULIANA", "material": "Ghiaia in Natura DoP", "plate": "BM493RN", "tare": 14300},
    {"subject": "BETON CANDEO Srl", "vector": "MAGRIN GIULIANA", "material": "Ghiaia in Natura DoP", "plate": "HB499TH", "tare": 14700},
    {"subject": "BETON CANDEO Srl", "vector": "MAGRIN GIULIANA", "material": "Ghiaia in Natura DoP", "plate": "FT234WG", "tare": 14300},
    {"subject": "BETON CANDEO Srl", "vector": "MAGRIN GIULIANA", "material": "Ghiaia in Natura DoP", "plate": "DY498NZ", "tare": 18200},
    {"subject": "BETON CANDEO Srl", "vector": "ZAMBELLO FRATELLI Snc", "material": "Ghiaia in Natura DoP", "plate": "BS242RP", "tare": 16100},
    {"subject": "BETON CANDEO Srl", "vector": "ZAMBELLO FRATELLI Snc", "material": "Ghiaia in Natura DoP", "plate": "GF726DK", "tare": 14500},
    {"subject": "BETON CANDEO Srl", "vector": "ZAMBELLO FRATELLI Snc", "material": "Ghiaia in Natura DoP", "plate": "DZ460AF", "tare": 16300},
    {"subject": "SABBIA BRENTA Srl", "vector": "SABBIA BRENTA Srl", "material": "Ghiaia in Natura DoP", "plate": "FV867JR", "tare": 14000},
    {"subject": "SABBIA BRENTA Srl", "vector": "SABBIA BRENTA Srl", "material": "Ghiaia in Natura DoP", "plate": "FX870DE", "tare": 17700},
    {"subject": "SABBIA BRENTA Srl", "vector": "SABBIA BRENTA Srl", "material": "Ghiaia in Natura DoP", "plate": "GC740BV", "tare": 14500},
    {"subject": "SABBIA BRENTA Srl", "vector": "SABBIA BRENTA Srl", "material": "Ghiaia in Natura DoP", "plate": "GE033XS", "tare": 18500},
    {"subject": "SABBIA BRENTA Srl", "vector": "SABBIA BRENTA Srl", "material": "Ghiaia in Natura DoP", "plate": "GC959LJ", "tare": 14500},
    {"subject": "SABBIA BRENTA Srl", "vector": "BASTIANELLO PAOLO Sas", "material": "Ghiaia in Natura DoP", "plate": "GP998VB", "tare": 15700}
]


def unique(values):
    return list(dict.fromkeys(values))


# Anagrafiche ricavate dalle prenotazioni
vehicles = [{"plate": r["plate"], "tare": r["tare"]} for r in reservations]
drivers = []
vectors = [{"social_reason": v} for v in unique(r["vector"] for r in reservations)]
subjects = [{"social_reason": s} for s in unique(r["subject"] for r in reservations)]
materials = [{"description": m} for m in unique(r["material"] for r in reservations)]

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
HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}

# Base URL
base_url = "http://localhost/api/anagrafic"


# Funzione per creare e inviare file xlsx
def create_and_upload_xlsx(data, filename, endpoint):
    buffer = BytesIO()
    df = pd.DataFrame(data)
    df.to_excel(buffer, index=False, engine='openpyxl')
    buffer.seek(0)

    files = {'file': (filename, buffer, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}

    try:
        response = requests.post(endpoint, files=files, headers=HEADERS)
        print(f"{filename} → {endpoint}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        print("-" * 60)
        return response
    except Exception as e:
        print(f"Errore con {filename}: {e}")
        print("-" * 60)
        return None


def get_ids(anagrafic, key):
    """Ritorna una mappa valore → id per l'anagrafica indicata."""
    response = requests.get(f"{base_url}/{anagrafic}/list", headers=HEADERS)
    response.raise_for_status()
    return {
        str(item[key]).strip().upper(): item["id"]
        for item in response.json()["data"]
        if item.get(key)
    }


def get_vehicles_with_permanent_access():
    response = requests.get(f"{base_url}/access/list", params={"permanent": "true"}, headers=HEADERS)
    response.raise_for_status()
    ids = set()
    for access in response.json().get("data", []):
        id_vehicle = access.get("idVehicle") or (access.get("vehicle") or {}).get("id")
        if id_vehicle:
            ids.add(id_vehicle)
    return ids


def create_reservations():
    subject_ids = get_ids("subject", "social_reason")
    vector_ids = get_ids("vector", "social_reason")
    vehicle_ids = get_ids("vehicle", "plate")
    material_ids = get_ids("material", "description")
    already_reserved = get_vehicles_with_permanent_access()

    created, skipped, errors = 0, 0, 0
    for r in reservations:
        try:
            id_vehicle = vehicle_ids[r["plate"].upper()]
            if id_vehicle in already_reserved:
                print(f"{r['plate']}: prenotazione permanente già presente, salto")
                skipped += 1
                continue
            body = {
                "typeSubject": "CUSTOMER",
                "subject": {"id": subject_ids[r["subject"].upper()]},
                "vector": {"id": vector_ids[r["vector"].upper()]},
                "vehicle": {"id": id_vehicle},
                "material": {"id": material_ids[r["material"].upper()]},
                "number_in_out": None,  # None = prenotazione permanente
                "type": "RESERVATION",
                "mode": "STANDARD",
            }
        except KeyError as e:
            print(f"{r['plate']}: anagrafica non trovata {e}")
            errors += 1
            continue

        response = requests.post(f"{base_url}/access", json=body, headers=HEADERS)
        if response.ok:
            created += 1
            print(f"{r['plate']}: prenotazione creata")
        else:
            errors += 1
            print(f"{r['plate']}: errore {response.status_code} {response.text}")

    print("-" * 60)
    print(f"Prenotazioni create: {created} | già presenti: {skipped} | errori: {errors}")


# Carica tutti i file
print("Inizio caricamento file xlsx...\n")

create_and_upload_xlsx(vehicles, "vehicle", f"{base_url}/vehicle/upload-file")
create_and_upload_xlsx(drivers, "driver", f"{base_url}/driver/upload-file")
create_and_upload_xlsx(vectors, "vector", f"{base_url}/vector/upload-file")
create_and_upload_xlsx(subjects, "subject", f"{base_url}/subject/upload-file")
create_and_upload_xlsx(materials, "material", f"{base_url}/material/upload-file")
create_and_upload_xlsx(card_registry, "card-registry", f"{base_url}/card-registry/upload-file")

print("\nCaricamento anagrafiche completato!\n")

print("Creazione prenotazioni permanenti...\n")
create_reservations()
