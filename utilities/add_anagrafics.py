import json
import pandas as pd
import requests
from io import BytesIO
from websockets.sync.client import connect as ws_connect

# Prenotazioni permanenti (da pesatura.xlsx, foglio Preferiti)
# Ogni riga: ID_Preferiti (numero tessera), tessera (codice letto dal lettore) e codice cliente.
# La targa del mezzo coincide con il codice della tessera.
reservations = [
    {"id": "351", "card": "7A00618303", "subject": "00321"},
    {"id": "352", "card": "7A00613A4C", "subject": "00322"},
    {"id": "353", "card": "7A00618753", "subject": "00323"},
    {"id": "354", "card": "7A00615379", "subject": "00324"},
    {"id": "355", "card": "7A00616242", "subject": "00325"},
    {"id": "356", "card": "7A006153F6", "subject": "00326"},
    {"id": "357", "card": "7A00613FAB", "subject": "00327"},
    {"id": "358", "card": "7A0061972F", "subject": "00328"},
    {"id": "359", "card": "7A006173AA", "subject": "00329"},
    {"id": "360", "card": "7A0061792C", "subject": "00330"},
    {"id": "361", "card": "7A0061822A", "subject": "00331"},
    {"id": "362", "card": "7A006173E2", "subject": "00332"},
    {"id": "363", "card": "7A0061412B", "subject": "00333"},
    {"id": "364", "card": "7A00617FDB", "subject": "00334"},
    {"id": "365", "card": "7A00619324", "subject": "00335"},
    {"id": "366", "card": "7A00615725", "subject": "00336"},
    {"id": "367", "card": "7A00619CBC", "subject": "00337"},
    {"id": "368", "card": "7A00619B42", "subject": "00338"},
    {"id": "369", "card": "7A0061A289", "subject": "00339"},
    {"id": "370", "card": "7A0061810E", "subject": "00340"},
    {"id": "371", "card": "7A00619720", "subject": "00341"},
    {"id": "372", "card": "7A0061995D", "subject": "00342"},
    {"id": "373", "card": "7A00614054", "subject": "00343"},
    {"id": "374", "card": "7A00615173", "subject": "00344"},
    {"id": "375", "card": "7A00614C9B", "subject": "00345"},
    {"id": "376", "card": "7A00617102", "subject": "00346"},
    {"id": "377", "card": "7A00614CC9", "subject": "00347"},
    {"id": "378", "card": "7A006156D7", "subject": "00348"},
    {"id": "379", "card": "7A00615242", "subject": "00349"},
    {"id": "380", "card": "7A00615794", "subject": "00350"},
    {"id": "381", "card": "7A006171A9", "subject": "00351"},
    {"id": "382", "card": "6F0065642A", "subject": "00352"},
    {"id": "383", "card": "6F006597B4", "subject": "00353"},
    {"id": "384", "card": "6F0065BB4B", "subject": "00354"},
    {"id": "385", "card": "6F0065ADC6", "subject": "00355"},
    {"id": "386", "card": "6F00656381", "subject": "00356"},
    {"id": "387", "card": "6F006563F5", "subject": "00357"},
    {"id": "388", "card": "6F00659DD6", "subject": "00358"},
    {"id": "389", "card": "6F00658525", "subject": "00359"},
    {"id": "390", "card": "6F00659115", "subject": "00360"},
    {"id": "391", "card": "6F00657791", "subject": "00361"},
    {"id": "392", "card": "6F0065C7F3", "subject": "00362"},
    {"id": "393", "card": "7500104495", "subject": "00363"},
    {"id": "394", "card": "75001040CF", "subject": "00364"},
    {"id": "395", "card": "7500104242", "subject": "00365"},
    {"id": "396", "card": "75000FE7FD", "subject": "00366"},
    {"id": "397", "card": "6F00659837", "subject": "00367"},
    {"id": "398", "card": "6F00657A58", "subject": "00368"},
    {"id": "399", "card": "6F00656D91", "subject": "00369"},
    {"id": "400", "card": "6F0065876A", "subject": "00370"},
    {"id": "401", "card": "6F00655F33", "subject": "00371"},
    {"id": "402", "card": "6F006588E1", "subject": "00372"},
    {"id": "403", "card": "6F00658E21", "subject": "00373"},
    {"id": "404", "card": "6F0065BE25", "subject": "00374"},
    {"id": "405", "card": "6F00659517", "subject": "00375"},
    {"id": "406", "card": "6F0065B609", "subject": "00376"},
    {"id": "407", "card": "6F00658344", "subject": "00377"},
    {"id": "408", "card": "6F00657889", "subject": "00378"},
    {"id": "409", "card": "6F0065AEA5", "subject": "00379"},
    {"id": "410", "card": "6F0065658A", "subject": "00380"},
    {"id": "411", "card": "6F0065A059", "subject": "00381"},
    {"id": "412", "card": "6F00655CBE", "subject": "00382"},
    {"id": "413", "card": "6F00657109", "subject": "00383"},
    {"id": "414", "card": "6F0065844F", "subject": "00384"},
    {"id": "415", "card": "6F0065AFCA", "subject": "00385"},
    {"id": "16", "card": "7A00613E55", "subject": "00001"},
    {"id": "17", "card": "6D001F3BE4", "subject": "00002"},
    {"id": "18", "card": "6D001F07DC", "subject": "00003"},
    {"id": "19", "card": "6D00067383", "subject": "00004"},
    {"id": "20", "card": "7A00615849", "subject": "00005"},
    {"id": "21", "card": "7A0061A367", "subject": "00006"},
    {"id": "22", "card": "7A00618F51", "subject": "00007"},
    {"id": "23", "card": "7A006183C3", "subject": "00008"},
    {"id": "24", "card": "7A00617387", "subject": "00009"},
    {"id": "25", "card": "7A00618A07", "subject": "00010"},
    {"id": "26", "card": "7A00615D75", "subject": "00011"},
    {"id": "27", "card": "7A006181D0", "subject": "00012"},
    {"id": "28", "card": "7A0061770F", "subject": "00013"},
    {"id": "29", "card": "7A00616641", "subject": "00014"},
    {"id": "30", "card": "7A0061A1E8", "subject": "00015"},
    {"id": "31", "card": "7A00614368", "subject": "00016"},
    {"id": "32", "card": "7A00614388", "subject": "00017"},
    {"id": "33", "card": "7A00613884", "subject": "00018"},
    {"id": "34", "card": "7A006164E7", "subject": "00019"},
    {"id": "35", "card": "7A0061576A", "subject": "00020"},
    {"id": "36", "card": "7A00619343", "subject": "00021"},
    {"id": "37", "card": "7A0061825A", "subject": "00022"},
    {"id": "38", "card": "7A0061899D", "subject": "00023"},
    {"id": "39", "card": "7A00615858", "subject": "00024"},
    {"id": "40", "card": "7A006160F3", "subject": "00025"},
    {"id": "41", "card": "7A00618246", "subject": "00026"},
    {"id": "42", "card": "7A00615D40", "subject": "00027"},
    {"id": "43", "card": "7A00614631", "subject": "00028"},
    {"id": "44", "card": "7A00618A73", "subject": "00029"},
    {"id": "45", "card": "7A00614927", "subject": "00030"},
    {"id": "46", "card": "7A0061534E", "subject": "00031"},
    {"id": "47", "card": "7A00619DF5", "subject": "00032"},
    {"id": "48", "card": "7A006183F0", "subject": "00033"},
    {"id": "49", "card": "7A00615CA6", "subject": "00034"},
    {"id": "50", "card": "7A00614123", "subject": "00035"},
    {"id": "51", "card": "7A006199F2", "subject": "00036"},
    {"id": "52", "card": "01130F097D", "subject": "00037"},
    {"id": "53", "card": "7A006150B1", "subject": "00038"},
    {"id": "54", "card": "7A0061386F", "subject": "00039"},
    {"id": "55", "card": "7A00616FE2", "subject": "00040"},
    {"id": "56", "card": "7A006166A5", "subject": "00041"},
    {"id": "57", "card": "7A006156E9", "subject": "00042"},
    {"id": "58", "card": "7A00619E84", "subject": "00043"},
    {"id": "59", "card": "7A006195B5", "subject": "00044"},
    {"id": "60", "card": "7A0061A276", "subject": "00045"},
    {"id": "61", "card": "7A00617A6C", "subject": "00046"},
    {"id": "62", "card": "7A00614214", "subject": "00047"},
    {"id": "63", "card": "7A00618574", "subject": "00048"},
    {"id": "64", "card": "7A006193B0", "subject": "00049"},
    {"id": "65", "card": "7A006149FC", "subject": "00050"},
    {"id": "66", "card": "7A006182DE", "subject": "00051"},
    {"id": "67", "card": "7A00617DE6", "subject": "00052"},
    {"id": "68", "card": "7A006198BC", "subject": "00053"},
    {"id": "69", "card": "7A006176D1", "subject": "00054"},
    {"id": "70", "card": "7A00616C8A", "subject": "00055"},
    {"id": "71", "card": "7A0061954D", "subject": "00056"},
    {"id": "72", "card": "7A00614616", "subject": "00057"},
    {"id": "73", "card": "7A006184DA", "subject": "00058"},
    {"id": "74", "card": "7A00614F5B", "subject": "00059"},
    {"id": "75", "card": "7A0061501F", "subject": "00060"},
    {"id": "76", "card": "7A00615707", "subject": "00061"},
    {"id": "77", "card": "7A00618E06", "subject": "00062"},
    {"id": "78", "card": "7A00615556", "subject": "00063"},
    {"id": "79", "card": "7A00615F08", "subject": "00064"},
    {"id": "80", "card": "7A006142DB", "subject": "00065"},
    {"id": "81", "card": "7A00614D3D", "subject": "00066"},
    {"id": "82", "card": "7A00613C52", "subject": "00067"},
    {"id": "83", "card": "7A006178CF", "subject": "00068"},
    {"id": "84", "card": "7A006163E5", "subject": "00069"},
    {"id": "85", "card": "7A006192C9", "subject": "00070"},
    {"id": "86", "card": "7A0061694F", "subject": "00071"},
    {"id": "87", "card": "7A00616319", "subject": "00072"},
    {"id": "88", "card": "7A00614F59", "subject": "00073"},
    {"id": "89", "card": "7A00618DE0", "subject": "00074"},
    {"id": "90", "card": "7A00617ED3", "subject": "00075"},
    {"id": "91", "card": "7A00617863", "subject": "00076"},
    {"id": "92", "card": "7A00618BA3", "subject": "00077"},
    {"id": "93", "card": "7A0078E293", "subject": "00078"},
    {"id": "94", "card": "7A0078FB0D", "subject": "00079"},
    {"id": "95", "card": "7A0079337B", "subject": "00080"},
    {"id": "96", "card": "7A00790747", "subject": "00081"},
    {"id": "97", "card": "7A0078D9AA", "subject": "00082"},
    {"id": "98", "card": "7A0078C90D", "subject": "00083"},
    {"id": "99", "card": "7A00791E39", "subject": "00084"},
    {"id": "100", "card": "7A0079330B", "subject": "00085"},
    {"id": "101", "card": "7A0078E783", "subject": "00086"},
    {"id": "102", "card": "7A0078F767", "subject": "00087"},
    {"id": "103", "card": "7A00792969", "subject": "00088"},
    {"id": "104", "card": "7A00790674", "subject": "00089"},
    {"id": "105", "card": "7A00792EAB", "subject": "00090"},
    {"id": "106", "card": "7A0078DE54", "subject": "00091"},
    {"id": "107", "card": "7A0079073D", "subject": "00092"},
    {"id": "108", "card": "7A0078FB68", "subject": "00093"},
    {"id": "109", "card": "7A0078EB26", "subject": "00094"},
    {"id": "110", "card": "7A00790133", "subject": "00095"},
    {"id": "111", "card": "7A007910A6", "subject": "00096"},
    {"id": "112", "card": "7A0078DBFB", "subject": "00097"},
    {"id": "113", "card": "7A0079311D", "subject": "00098"},
    {"id": "114", "card": "7A0078F6EE", "subject": "00099"},
    {"id": "115", "card": "7A0078E20D", "subject": "00100"},
    {"id": "116", "card": "7A00790B62", "subject": "00101"},
    {"id": "117", "card": "7A00790DCE", "subject": "00102"},
    {"id": "118", "card": "7A0078EA8E", "subject": "00103"},
    {"id": "119", "card": "7A0078E9A7", "subject": "00104"},
    {"id": "120", "card": "7A00790ADD", "subject": "00105"},
    {"id": "121", "card": "7A00792AD3", "subject": "00106"},
    {"id": "122", "card": "7A007926C2", "subject": "00107"},
    {"id": "123", "card": "7A0078FA68", "subject": "00108"},
    {"id": "124", "card": "7A0078FE49", "subject": "00109"},
    {"id": "125", "card": "7A006199E5", "subject": "00110"},
    {"id": "126", "card": "7A00618D9C", "subject": "00111"},
    {"id": "127", "card": "7A00617D3F", "subject": "00112"},
    {"id": "128", "card": "7A00613A21", "subject": "00113"},
    {"id": "129", "card": "7A00615ED6", "subject": "00114"},
    {"id": "130", "card": "7A00619DA4", "subject": "00115"},
    {"id": "131", "card": "7A00616C54", "subject": "00116"},
    {"id": "132", "card": "7A00614763", "subject": "00117"},
    {"id": "133", "card": "7A006197BE", "subject": "00118"},
    {"id": "134", "card": "7A006143F0", "subject": "00119"},
    {"id": "135", "card": "7A0061677E", "subject": "00120"},
    {"id": "136", "card": "7A00618106", "subject": "00121"},
    {"id": "137", "card": "7A00616537", "subject": "00122"},
    {"id": "138", "card": "7A00618C25", "subject": "00123"},
    {"id": "139", "card": "7A00618486", "subject": "00124"},
    {"id": "140", "card": "7A00614FF3", "subject": "00125"},
    {"id": "141", "card": "7A00616E41", "subject": "00126"},
    {"id": "142", "card": "7A006162C9", "subject": "00127"},
    {"id": "143", "card": "7A00619791", "subject": "00128"},
    {"id": "144", "card": "7A00615F3D", "subject": "00129"},
    {"id": "145", "card": "7A006161DE", "subject": "00130"},
    {"id": "146", "card": "7A00617B50", "subject": "00131"},
    {"id": "147", "card": "7A00617E8B", "subject": "00132"},
    {"id": "148", "card": "7A006189ED", "subject": "00133"},
    {"id": "149", "card": "7A00617F78", "subject": "00134"},
    {"id": "150", "card": "7A00619A1E", "subject": "00135"},
    {"id": "151", "card": "7A00617B88", "subject": "00136"},
    {"id": "152", "card": "7A006141EC", "subject": "00137"},
    {"id": "153", "card": "7A00613E1E", "subject": "00138"},
    {"id": "154", "card": "7A00618E14", "subject": "00139"},
    {"id": "155", "card": "7A006176DE", "subject": "00140"},
    {"id": "156", "card": "7A0061661B", "subject": "00141"},
    {"id": "157", "card": "7A00617933", "subject": "00142"},
    {"id": "158", "card": "7A00616856", "subject": "00143"},
    {"id": "159", "card": "7A00619F54", "subject": "00144"},
    {"id": "160", "card": "7A00613D10", "subject": "00145"},
    {"id": "161", "card": "7A00617502", "subject": "00146"},
    {"id": "162", "card": "7A0079165C", "subject": "00147"},
    {"id": "163", "card": "7A00619AEC", "subject": "00148"},
    {"id": "164", "card": "7A00617206", "subject": "00149"},
    {"id": "165", "card": "7A00792A13", "subject": "00150"},
    {"id": "166", "card": "7A00616716", "subject": "00151"},
    {"id": "167", "card": "7A00614708", "subject": "00152"},
    {"id": "168", "card": "7A0078CB3B", "subject": "00153"},
    {"id": "169", "card": "7A0078F7B0", "subject": "00154"},
    {"id": "170", "card": "7A00619B5F", "subject": "00155"},
    {"id": "171", "card": "7A00614DCD", "subject": "00156"},
    {"id": "172", "card": "7A0061A157", "subject": "00157"},
    {"id": "173", "card": "7A00614FFC", "subject": "00158"},
    {"id": "174", "card": "7A0061829A", "subject": "00159"},
    {"id": "175", "card": "7A00613A34", "subject": "00160"},
    {"id": "176", "card": "7A00615705", "subject": "00161"},
    {"id": "177", "card": "7A0061A31B", "subject": "00162"},
    {"id": "178", "card": "7A006189FA", "subject": "00163"},
    {"id": "179", "card": "7A006199EF", "subject": "00164"},
    {"id": "180", "card": "7A00618EBE", "subject": "00165"},
    {"id": "181", "card": "7A00616F55", "subject": "00166"},
    {"id": "182", "card": "7A0061658D", "subject": "00167"},
    {"id": "183", "card": "7A006176DF", "subject": "00168"},
    {"id": "184", "card": "7A0061804A", "subject": "00169"},
    {"id": "185", "card": "7A006180B3", "subject": "00170"},
    {"id": "186", "card": "7A00617CEC", "subject": "00171"},
    {"id": "187", "card": "7A00616A40", "subject": "00172"},
    {"id": "188", "card": "7A00614B75", "subject": "00173"},
    {"id": "189", "card": "7A006170A2", "subject": "00174"},
    {"id": "190", "card": "7A00613C3B", "subject": "00175"},
    {"id": "191", "card": "7A0061390A", "subject": "00176"},
    {"id": "192", "card": "7A006169DC", "subject": "00177"},
    {"id": "193", "card": "7A00618D8A", "subject": "00178"},
    {"id": "194", "card": "7A006172F8", "subject": "00179"},
    {"id": "195", "card": "7A0061A27F", "subject": "00180"},
    {"id": "196", "card": "7A0061731B", "subject": "00181"},
    {"id": "197", "card": "7A00618A31", "subject": "00182"},
    {"id": "198", "card": "7A0061768A", "subject": "00183"},
    {"id": "199", "card": "7A00619C7E", "subject": "00184"},
    {"id": "200", "card": "7A00619683", "subject": "00185"},
    {"id": "201", "card": "7A0061A228", "subject": "00186"},
    {"id": "202", "card": "7A00617EFE", "subject": "00187"},
    {"id": "203", "card": "7A00616B2A", "subject": "00188"},
    {"id": "204", "card": "7A00613AC5", "subject": "00189"},
    {"id": "205", "card": "7A00617E0C", "subject": "00190"},
    {"id": "206", "card": "7A006184B1", "subject": "00191"},
    {"id": "207", "card": "7A00618C12", "subject": "00192"},
    {"id": "208", "card": "7A00613D00", "subject": "00193"},
    {"id": "209", "card": "7A00613805", "subject": "00194"},
    {"id": "210", "card": "7A00618190", "subject": "00195"},
    {"id": "211", "card": "7A006190AF", "subject": "00196"},
    {"id": "212", "card": "7A006190F7", "subject": "00197"},
    {"id": "213", "card": "7A00616041", "subject": "00198"},
    {"id": "214", "card": "7A0077A3A0", "subject": "00199"},
    {"id": "215", "card": "7A00619907", "subject": "00200"},
    {"id": "231", "card": "7A00618969", "subject": "00201"},
    {"id": "232", "card": "7A005A09C2", "subject": "00202"},
    {"id": "233", "card": "7A00617457", "subject": "00203"},
    {"id": "234", "card": "7A00616B3C", "subject": "00204"},
    {"id": "235", "card": "7A00614F98", "subject": "00205"},
    {"id": "236", "card": "7A00614AE3", "subject": "00206"},
    {"id": "237", "card": "7A00617F99", "subject": "00207"},
    {"id": "238", "card": "7A006149A7", "subject": "00208"},
    {"id": "239", "card": "7A006187C9", "subject": "00209"},
    {"id": "240", "card": "7A006174BD", "subject": "00210"},
    {"id": "241", "card": "7A00615259", "subject": "00211"},
    {"id": "242", "card": "7A006146C3", "subject": "00212"},
    {"id": "243", "card": "7A00613BF3", "subject": "00213"},
    {"id": "244", "card": "7A00619CE6", "subject": "00214"},
    {"id": "245", "card": "7A006171CC", "subject": "00215"},
    {"id": "246", "card": "7A00618DFE", "subject": "00216"},
    {"id": "247", "card": "7A00615A07", "subject": "00217"},
    {"id": "248", "card": "7A00618D3E", "subject": "00218"},
    {"id": "249", "card": "7A00617BDE", "subject": "00219"},
    {"id": "250", "card": "7A00618CE3", "subject": "00220"},
    {"id": "251", "card": "7A006165D3", "subject": "00221"},
    {"id": "252", "card": "7A006159AE", "subject": "00222"},
    {"id": "253", "card": "7A00617B26", "subject": "00223"},
    {"id": "254", "card": "7A006197C6", "subject": "00224"},
    {"id": "255", "card": "7A00618BD2", "subject": "00225"},
    {"id": "256", "card": "7A0061643F", "subject": "00226"},
    {"id": "257", "card": "7A0061591E", "subject": "00227"},
    {"id": "258", "card": "7A00615091", "subject": "00228"},
    {"id": "259", "card": "7A00619612", "subject": "00229"},
    {"id": "260", "card": "7A00618F68", "subject": "00230"},
    {"id": "261", "card": "7A00618151", "subject": "00231"},
    {"id": "262", "card": "7A006199A1", "subject": "00232"},
    {"id": "263", "card": "7A00616241", "subject": "00233"},
    {"id": "264", "card": "7A0061496A", "subject": "00234"},
    {"id": "265", "card": "7A00619A61", "subject": "00235"},
    {"id": "266", "card": "7A006177D0", "subject": "00236"},
    {"id": "267", "card": "7A0077D44F", "subject": "00237"},
    {"id": "268", "card": "7A0077849B", "subject": "00238"},
    {"id": "269", "card": "7A0077B625", "subject": "00239"},
    {"id": "270", "card": "7A00778D6B", "subject": "00240"},
    {"id": "271", "card": "7A0077CAF7", "subject": "00241"},
    {"id": "281", "card": "7A006141AF", "subject": "00251"},
    {"id": "282", "card": "7A00613882", "subject": "00252"},
    {"id": "283", "card": "7A00614224", "subject": "00253"},
    {"id": "284", "card": "7A00613F36", "subject": "00254"},
    {"id": "285", "card": "7A00619C08", "subject": "00255"},
    {"id": "286", "card": "7A00614FDA", "subject": "00256"},
    {"id": "287", "card": "7A00619462", "subject": "00257"},
    {"id": "288", "card": "7A00613D6A", "subject": "00258"},
    {"id": "289", "card": "7A006195A7", "subject": "00259"},
    {"id": "290", "card": "7A00617904", "subject": "00260"},
    {"id": "291", "card": "7A00614193", "subject": "00261"},
    {"id": "292", "card": "7A0061952B", "subject": "00262"},
    {"id": "293", "card": "7A00615FDA", "subject": "00263"},
    {"id": "294", "card": "7A00618AF7", "subject": "00264"},
    {"id": "295", "card": "7A0061697D", "subject": "00265"},
    {"id": "272", "card": "7A00614B64", "subject": "00242"},
    {"id": "273", "card": "7A0077CDF5", "subject": "00243"},
    {"id": "274", "card": "7A00617E5F", "subject": "00244"},
    {"id": "275", "card": "7A0061A57A", "subject": "00245"},
    {"id": "276", "card": "7A00619F34", "subject": "00246"},
    {"id": "277", "card": "7A006156A1", "subject": "00247"},
    {"id": "278", "card": "7A00619B63", "subject": "00248"},
    {"id": "279", "card": "7A006173FE", "subject": "00249"},
    {"id": "280", "card": "7A00617C71", "subject": "00250"},
    {"id": "296", "card": "7A00616300", "subject": "00266"},
    {"id": "297", "card": "7A006185CF", "subject": "00267"},
    {"id": "298", "card": "7A006166C5", "subject": "00268"},
    {"id": "299", "card": "7A00619C9D", "subject": "00269"},
    {"id": "300", "card": "7A00617A56", "subject": "00270"},
    {"id": "301", "card": "7A00614002", "subject": "00271"},
    {"id": "302", "card": "7A00619CDE", "subject": "00272"},
    {"id": "303", "card": "7A0061826B", "subject": "00273"},
    {"id": "304", "card": "7A006198AC", "subject": "00274"},
    {"id": "305", "card": "7A00614691", "subject": "00275"},
    {"id": "306", "card": "7A006160DD", "subject": "00276"},
    {"id": "307", "card": "7A00616704", "subject": "00277"},
    {"id": "308", "card": "7A006168B7", "subject": "00278"},
    {"id": "309", "card": "7A00617168", "subject": "00279"},
    {"id": "310", "card": "7A0061481A", "subject": "00280"},
    {"id": "311", "card": "7A006195EA", "subject": "00281"},
    {"id": "312", "card": "7A00617BF4", "subject": "00282"},
    {"id": "313", "card": "7A00614BAA", "subject": "00283"},
    {"id": "314", "card": "7A006173B5", "subject": "00284"},
    {"id": "315", "card": "7A006187C5", "subject": "00285"},
    {"id": "316", "card": "7A00617E03", "subject": "00286"},
    {"id": "317", "card": "7A0061818B", "subject": "00287"},
    {"id": "318", "card": "7A00616DEC", "subject": "00288"},
    {"id": "319", "card": "7A00614BEF", "subject": "00289"},
    {"id": "320", "card": "7A00616A99", "subject": "00290"},
    {"id": "321", "card": "7A00617F5C", "subject": "00291"},
    {"id": "322", "card": "7A006181EF", "subject": "00292"},
    {"id": "323", "card": "7A00616348", "subject": "00293"},
    {"id": "324", "card": "7A006162B7", "subject": "00294"},
    {"id": "325", "card": "7A00618B90", "subject": "00295"},
    {"id": "326", "card": "7A006185DC", "subject": "00296"},
    {"id": "327", "card": "7A00616396", "subject": "00297"},
    {"id": "328", "card": "7A00618846", "subject": "00298"},
    {"id": "329", "card": "7A00618D79", "subject": "00299"},
    {"id": "330", "card": "7A00615DAA", "subject": "00300"},
    {"id": "331", "card": "7A0061620C", "subject": "00301"},
    {"id": "332", "card": "7A00618B8C", "subject": "00302"},
    {"id": "333", "card": "7A00618196", "subject": "00303"},
    {"id": "334", "card": "7A00615CC6", "subject": "00304"},
    {"id": "335", "card": "7A0061841D", "subject": "00305"},
    {"id": "336", "card": "7A006179DA", "subject": "00306"},
    {"id": "337", "card": "7A00613A7E", "subject": "00307"},
    {"id": "338", "card": "7A00613C09", "subject": "00308"},
    {"id": "339", "card": "7A00619F03", "subject": "00309"},
    {"id": "340", "card": "7A006166C0", "subject": "00310"},
    {"id": "341", "card": "7A00614FBD", "subject": "00311"},
    {"id": "342", "card": "7A0061402F", "subject": "00312"},
    {"id": "343", "card": "7A006158A7", "subject": "00313"},
    {"id": "344", "card": "7A00615F44", "subject": "00314"},
    {"id": "345", "card": "7A00615E3D", "subject": "00315"},
    {"id": "346", "card": "7A00616D0C", "subject": "00316"},
    {"id": "347", "card": "7A0061A2E0", "subject": "00317"},
    {"id": "348", "card": "7A0061A102", "subject": "00318"},
    {"id": "349", "card": "7A00616115", "subject": "00319"},
    {"id": "350", "card": "7A00613BCD", "subject": "00320"},
    {"id": "416", "card": "6F0065BDB4", "subject": "00386"},
    {"id": "417", "card": "6F0065C6F3", "subject": "00387"},
    {"id": "418", "card": "6F00659455", "subject": "00388"},
    {"id": "419", "card": "6F0065759F", "subject": "00389"},
    {"id": "420", "card": "6F0065AF5E", "subject": "00390"},
    {"id": "421", "card": "6F006587EE", "subject": "00391"},
    {"id": "422", "card": "6F00658535", "subject": "00392"},
    {"id": "423", "card": "6F00656923", "subject": "00393"},
    {"id": "424", "card": "6F0065AC7F", "subject": "00394"},
    {"id": "425", "card": "6F0065A2DE", "subject": "00395"},
    {"id": "426", "card": "6F00658406", "subject": "00396"},
    {"id": "427", "card": "6F00656C5C", "subject": "00397"},
    {"id": "428", "card": "6F0065AB81", "subject": "00398"},
    {"id": "429", "card": "6F00659090", "subject": "00399"},
    {"id": "430", "card": "6F006569CB", "subject": "00400"},
    {"id": "431", "card": "7A00615E05", "subject": "00401"},
    {"id": "432", "card": "6F0065626B", "subject": "00402"},
    {"id": "433", "card": "6F0065C3EE", "subject": "00403"},
    {"id": "434", "card": "6F006599EE", "subject": "00404"},
    {"id": "435", "card": "6F0065A39A", "subject": "00405"},
    {"id": "436", "card": "6F0065C352", "subject": "00406"},
    {"id": "437", "card": "6F0065BB32", "subject": "00407"},
    {"id": "438", "card": "6F00657D53", "subject": "00408"},
    {"id": "439", "card": "6F00659825", "subject": "00409"},
    {"id": "440", "card": "6F006582D4", "subject": "00410"},
    {"id": "442", "card": "6F00655E50", "subject": "00412"},
    {"id": "443", "card": "6F00655E72", "subject": "00413"},
    {"id": "444", "card": "6F00656B38", "subject": "00414"},
    {"id": "445", "card": "6F00655DCA", "subject": "00415"},
    {"id": "446", "card": "6F0065AE78", "subject": "00416"},
    {"id": "447", "card": "6F00656DFD", "subject": "00417"},
    {"id": "448", "card": "6F006578FE", "subject": "00418"},
    {"id": "449", "card": "6F006575BF", "subject": "00419"},
    {"id": "450", "card": "6F0065C6EC", "subject": "00420"},
    {"id": "451", "card": "6F0065B38A", "subject": "00421"},
    {"id": "452", "card": "6F0065C595", "subject": "00422"},
    {"id": "453", "card": "6F0065C094", "subject": "00423"},
    {"id": "454", "card": "6F00659A98", "subject": "00424"},
    {"id": "455", "card": "01142891B0", "subject": "00425"},
    {"id": "456", "card": "6F00659845", "subject": "00426"},
    {"id": "457", "card": "6F0065B8AA", "subject": "00427"},
    {"id": "458", "card": "6F0065BD9E", "subject": "00428"},
    {"id": "459", "card": "6F00658B84", "subject": "00429"},
    {"id": "460", "card": "6F0065783D", "subject": "00430"},
    {"id": "461", "card": "6F00656236", "subject": "00431"},
    {"id": "462", "card": "6F006584CE", "subject": "00432"},
    {"id": "463", "card": "6F0065A245", "subject": "00433"},
    {"id": "464", "card": "6F00657EDA", "subject": "00434"},
    {"id": "465", "card": "6F00658393", "subject": "00435"},
    {"id": "466", "card": "6F006591ED", "subject": "00436"},
    {"id": "467", "card": "6F0065BD93", "subject": "00437"},
    {"id": "468", "card": "6F0065C1F2", "subject": "00438"},
    {"id": "469", "card": "6F006584D1", "subject": "00439"},
    {"id": "470", "card": "6F0065AACD", "subject": "00440"},
    {"id": "471", "card": "6F0065A743", "subject": "00441"},
    {"id": "472", "card": "6F0065A832", "subject": "00442"},
    {"id": "473", "card": "6F00656368", "subject": "00443"},
    {"id": "474", "card": "6F0065A515", "subject": "00444"},
    {"id": "475", "card": "75000FF6B2", "subject": "00445"},
    {"id": "476", "card": "75000FE389", "subject": "00446"},
    {"id": "477", "card": "75000FF1A1", "subject": "00447"},
    {"id": "478", "card": "75000FE9CB", "subject": "00448"},
    {"id": "479", "card": "75000FF31E", "subject": "00449"},
    {"id": "480", "card": "73000A5D08", "subject": "00450"},
    {"id": "481", "card": "3C00C9E6BD", "subject": "00481"},
    {"id": "482", "card": "3C00B3B793", "subject": "00482"},
    {"id": "483", "card": "3C00C93950", "subject": "00483"},
    {"id": "484", "card": "3C00B4A9CC", "subject": "00484"},
    {"id": "485", "card": "3C00B4A1AC", "subject": "00485"},
    {"id": "486", "card": "3C00C9F081", "subject": "00486"},
    {"id": "487", "card": "3C00CA3493", "subject": "00487"},
    {"id": "488", "card": "3C00B4648E", "subject": "00488"},
    {"id": "489", "card": "3C00C98C84", "subject": "00489"},
    {"id": "490", "card": "3C00B42BD7", "subject": "00490"},
    {"id": "492", "card": "01149B555E", "subject": "00492"},
    {"id": "493", "card": "01149BD5E4", "subject": "00493"},
    {"id": "494", "card": "01149BDC1D", "subject": "00494"},
    {"id": "495", "card": "01149BDC36", "subject": "00495"},
    {"id": "496", "card": "01149BEDAD", "subject": "00496"},
    {"id": "497", "card": "01149BBA44", "subject": "00497"},
    {"id": "498", "card": "01149BDD6A", "subject": "00498"},
    {"id": "499", "card": "01149BE797", "subject": "00499"},
    {"id": "500", "card": "01149BED64", "subject": "00500"},
    {"id": "501", "card": "01154A7260", "subject": "00501"},
    {"id": "502", "card": "01154A7DA8", "subject": "00502"},
    {"id": "503", "card": "01154A79F2", "subject": "00503"},
    {"id": "504", "card": "01154A7CB9", "subject": "00504"},
    {"id": "505", "card": "01154A7B45", "subject": "00505"},
    {"id": "506", "card": "01154A7C64", "subject": "00506"},
    {"id": "507", "card": "01154A5829", "subject": "00507"},
    {"id": "508", "card": "01154A8501", "subject": "00508"},
    {"id": "509", "card": "01154A7BC5", "subject": "00509"},
    {"id": "510", "card": "01154A696B", "subject": "00510"},
    {"id": "511", "card": "3C00B3EE3B", "subject": "00511"},
    {"id": "512", "card": "01154A5F6C", "subject": "00512"},
    {"id": "513", "card": "01154A6A03", "subject": "00513"},
    {"id": "514", "card": "01154A5FED", "subject": "00514"},
    {"id": "515", "card": "01154A669C", "subject": "00515"},
    {"id": "516", "card": "01154A64FD", "subject": "00516"},
    {"id": "517", "card": "01154A85B9", "subject": "00517"},
    {"id": "518", "card": "01154A6BEC", "subject": "00518"},
    {"id": "519", "card": "01154A5AFE", "subject": "00519"},
    {"id": "520", "card": "01154A8180", "subject": "00520"},
    {"id": "521", "card": "01154A743D", "subject": "00521"},
    {"id": "522", "card": "01154A8C30", "subject": "00522"},
    {"id": "523", "card": "01154A806D", "subject": "00523"},
    {"id": "524", "card": "01154A8065", "subject": "00524"},
    {"id": "525", "card": "01154A789E", "subject": "00525"},
    {"id": "526", "card": "01154A7CFD", "subject": "00526"},
    {"id": "527", "card": "01154A6CBC", "subject": "00527"},
    {"id": "528", "card": "01154A6CF5", "subject": "00528"},
    {"id": "529", "card": "01154A8F6C", "subject": "00529"},
    {"id": "530", "card": "01154A6C56", "subject": "00530"},
    {"id": "531", "card": "01154A5A89", "subject": "00531"},
    {"id": "532", "card": "01154A5A89", "subject": "00532"},
    {"id": "533", "card": "01154A6E08", "subject": "00533"},
    {"id": "534", "card": "01154A6C91", "subject": "00534"},
    {"id": "535", "card": "01154A91D6", "subject": "00535"},
    {"id": "536", "card": "01154A7598", "subject": "00536"},
    {"id": "537", "card": "01154A6C49", "subject": "00537"},
    {"id": "538", "card": "01154A7654", "subject": "00538"},
    {"id": "539", "card": "01154A84FD", "subject": "00539"},
    {"id": "540", "card": "01154A65A8", "subject": "00540"},
    {"id": "541", "card": "01154A5B41", "subject": "00541"},
    {"id": "542", "card": "01154A7558", "subject": "00542"},
    {"id": "543", "card": "01154A8CAC", "subject": "00543"},
    {"id": "544", "card": "01154A5434", "subject": "00544"},
    {"id": "545", "card": "01154A640B", "subject": "00545"},
    {"id": "546", "card": "01154A6885", "subject": "00546"},
    {"id": "547", "card": "0114C2B201", "subject": "00547"},
    {"id": "548", "card": "0114C24E21", "subject": "00548"},
    {"id": "549", "card": "0114C2ADB7", "subject": "00549"},
    {"id": "550", "card": "0114C27F91", "subject": "00550"},
    {"id": "551", "card": "0114C28AD7", "subject": "00551"},
    {"id": "552", "card": "0114C2C254", "subject": "00552"},
    {"id": "553", "card": "0114C2C12B", "subject": "00553"},
    {"id": "554", "card": "0114C28E8D", "subject": "00554"},
    {"id": "555", "card": "0114C2A6C0", "subject": "00555"},
    {"id": "556", "card": "0114C2B9AF", "subject": "00556"},
    {"id": "557", "card": "0114C293CB", "subject": "00557"},
    {"id": "558", "card": "0114C2542E", "subject": "00558"},
    {"id": "559", "card": "0114C2A22B", "subject": "00559"},
    {"id": "560", "card": "0114C2AB95", "subject": "00560"},
    {"id": "531", "card": "01154A84F4", "subject": "00531"},
]


def unique(values):
    return list(dict.fromkeys(values))


# Tessera e codice cliente devono essere univoci (targa e tessera sono campi unique):
# in caso di doppioni si tiene la prima riga e si segnalano le altre.
_seen_cards, _seen_subjects, _rows = set(), set(), []
for r in reservations:
    if r["card"].upper() in _seen_cards or r["subject"].upper() in _seen_subjects:
        print(f"Riga duplicata ignorata: tessera {r['card']} cliente {r['subject']}")
        continue
    _seen_cards.add(r["card"].upper())
    _seen_subjects.add(r["subject"].upper())
    _rows.append(r)
reservations = _rows

# Anagrafiche ricavate dalle prenotazioni
vehicles = [{"plate": r["card"]} for r in reservations]
drivers = []
vectors = []
subjects = [{"social_reason": s} for s in unique(r["subject"] for r in reservations)]
materials = []
# number = ID_Preferiti (numero tessera), code = codice letto dal lettore
card_registry = [{"number": r["id"], "code": r["card"]} for r in reservations]

# Token di autenticazione
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwidXNlcm5hbWUiOiJiYXJvbnBlc2kiLCJwYXNzd29yZCI6IiQyYiQxMiRQQUhFNGtoNmxuWG8zdzlTRjl0ajdPamVjbzkxdmdXNzVDcFM5QzBuM0JPNHNoYVdHR08ubSIsImxldmVsIjo0LCJkZXNjcmlwdGlvbiI6ImJhcm9ub3Blc2kiLCJkYXRlX2NyZWF0ZWQiOiIyMDI1LTEwLTMxVDEwOjIyOjEwLjIyODgyNiIsImV4cCI6NDkxNTUwNjk1OH0.EsGLRj73mXHK5hJ-FUyKyy51VKKMvIwODXMi5H4Kpos"
HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}

# Base URL
base_url = "http://localhost/api/anagrafic"


# Funzione per creare e inviare file xlsx
def create_and_upload_xlsx(data, filename, endpoint):
    if not data:
        print(f"{filename}: nessun dato, salto")
        print("-" * 60)
        return None
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


def rename_locked(anagrafic, id_record, body, ws, id_request):
    """Il server accetta la modifica solo se il record è bloccato via websocket."""
    ws.send(json.dumps({"action": "lock", "anagrafic": anagrafic, "idRecord": id_record, "type": "UPDATE", "idRequest": id_request}))
    while True:
        message = json.loads(ws.recv(timeout=10))
        if message.get("action") == "lock" and message.get("idRequest") == id_request:
            break
    if not message.get("success"):
        return False, message.get("error")
    response = requests.patch(f"{base_url}/{anagrafic}/{id_record}", json=body, headers=HEADERS)
    return response.ok, f"{response.status_code} {response.text}"


def ensure_subjects():
    """Crea i clienti via JSON (l'upload xlsx trasforma "00321" in 321).
    I clienti già caricati senza zeri iniziali vengono rinominati."""
    existing = get_ids("subject", "social_reason")
    created, renamed = 0, 0
    ws_url = base_url.replace("http", "ws", 1) + f"/subject?token={AUTH_TOKEN}"
    with ws_connect(ws_url) as ws:
        for i, s in enumerate(subjects, start=1):
            name = s["social_reason"]
            if name.upper() in existing:
                continue
            stripped = name.lstrip("0") or "0"
            if stripped in existing:
                ok, detail = rename_locked("subject", existing[stripped], {"social_reason": name}, ws, i)
                if ok:
                    renamed += 1
                else:
                    print(f"Cliente {stripped} → {name}: errore {detail}")
                continue
            response = requests.post(f"{base_url}/subject", json=s, headers=HEADERS)
            if response.ok:
                created += 1
            else:
                print(f"Cliente {name}: errore {response.status_code} {response.text}")
    print(f"Clienti creati: {created} | rinominati: {renamed}")
    print("-" * 60)


def ensure_cards():
    """Registra le tessere una per una (non esiste un upload xlsx per le tessere)."""
    existing = get_ids("card-registry", "code")
    created = 0
    for c in card_registry:
        if c["code"].upper() in existing:
            continue
        response = requests.post(f"{base_url}/card-registry", json=c, headers=HEADERS)
        if response.ok:
            created += 1
        else:
            print(f"Tessera {c['code']} ({c['number']}): errore {response.status_code} {response.text}")
    print(f"Tessere create: {created}")
    print("-" * 60)


def create_reservations():
    subject_ids = get_ids("subject", "social_reason")
    vehicle_ids = get_ids("vehicle", "plate")
    card_ids = get_ids("card-registry", "code")
    already_reserved = get_vehicles_with_permanent_access()

    created, skipped, errors = 0, 0, 0
    for r in reservations:
        try:
            id_vehicle = vehicle_ids[r["card"].upper()]
            if id_vehicle in already_reserved:
                print(f"{r['card']}: prenotazione permanente già presente, salto")
                skipped += 1
                continue
            body = {
                "typeSubject": "CUSTOMER",
                "subject": {"id": subject_ids[r["subject"].upper()]},
                "vehicle": {"id": id_vehicle},
                "idCardRegistry": card_ids[r["card"].upper()],
                "number_in_out": None,  # None = prenotazione permanente
                "type": "RESERVATION",
                "mode": "STANDARD",
            }
        except KeyError as e:
            print(f"{r['card']}: anagrafica non trovata {e}")
            errors += 1
            continue

        response = requests.post(f"{base_url}/access", json=body, headers=HEADERS)
        if response.ok:
            created += 1
            print(f"{r['card']}: prenotazione creata")
        else:
            errors += 1
            print(f"{r['card']}: errore {response.status_code} {response.text}")

    print("-" * 60)
    print(f"Prenotazioni create: {created} | già presenti: {skipped} | errori: {errors}")


# Carica tutti i file
print("Inizio caricamento anagrafiche...\n")

existing_plates = get_ids("vehicle", "plate")
create_and_upload_xlsx([v for v in vehicles if v["plate"].upper() not in existing_plates], "vehicle", f"{base_url}/vehicle/upload-file")
ensure_subjects()
ensure_cards()

print("\nCaricamento anagrafiche completato!\n")

print("Creazione prenotazioni permanenti...\n")
create_reservations()
