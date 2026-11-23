import json
import pandas as pd
import requests
from io import BytesIO
from websockets.sync.client import connect as ws_connect

# Prenotazioni permanenti (da pesatura.xlsx, foglio Preferiti)
# Ogni riga: tessera (codice letto dal lettore) e codice cliente.
# La targa del mezzo coincide con il codice della tessera.
reservations = [
    {"card": "7A00618303", "subject": "00321"},
    {"card": "7A00613A4C", "subject": "00322"},
    {"card": "7A00618753", "subject": "00323"},
    {"card": "7A00615379", "subject": "00324"},
    {"card": "7A00616242", "subject": "00325"},
    {"card": "7A006153F6", "subject": "00326"},
    {"card": "7A00613FAB", "subject": "00327"},
    {"card": "7A0061972F", "subject": "00328"},
    {"card": "7A006173AA", "subject": "00329"},
    {"card": "7A0061792C", "subject": "00330"},
    {"card": "7A0061822A", "subject": "00331"},
    {"card": "7A006173E2", "subject": "00332"},
    {"card": "7A0061412B", "subject": "00333"},
    {"card": "7A00617FDB", "subject": "00334"},
    {"card": "7A00619324", "subject": "00335"},
    {"card": "7A00615725", "subject": "00336"},
    {"card": "7A00619CBC", "subject": "00337"},
    {"card": "7A00619B42", "subject": "00338"},
    {"card": "7A0061A289", "subject": "00339"},
    {"card": "7A0061810E", "subject": "00340"},
    {"card": "7A00619720", "subject": "00341"},
    {"card": "7A0061995D", "subject": "00342"},
    {"card": "7A00614054", "subject": "00343"},
    {"card": "7A00615173", "subject": "00344"},
    {"card": "7A00614C9B", "subject": "00345"},
    {"card": "7A00617102", "subject": "00346"},
    {"card": "7A00614CC9", "subject": "00347"},
    {"card": "7A006156D7", "subject": "00348"},
    {"card": "7A00615242", "subject": "00349"},
    {"card": "7A00615794", "subject": "00350"},
    {"card": "7A006171A9", "subject": "00351"},
    {"card": "6F0065642A", "subject": "00352"},
    {"card": "6F006597B4", "subject": "00353"},
    {"card": "6F0065BB4B", "subject": "00354"},
    {"card": "6F0065ADC6", "subject": "00355"},
    {"card": "6F00656381", "subject": "00356"},
    {"card": "6F006563F5", "subject": "00357"},
    {"card": "6F00659DD6", "subject": "00358"},
    {"card": "6F00658525", "subject": "00359"},
    {"card": "6F00659115", "subject": "00360"},
    {"card": "6F00657791", "subject": "00361"},
    {"card": "6F0065C7F3", "subject": "00362"},
    {"card": "7500104495", "subject": "00363"},
    {"card": "75001040CF", "subject": "00364"},
    {"card": "7500104242", "subject": "00365"},
    {"card": "75000FE7FD", "subject": "00366"},
    {"card": "6F00659837", "subject": "00367"},
    {"card": "6F00657A58", "subject": "00368"},
    {"card": "6F00656D91", "subject": "00369"},
    {"card": "6F0065876A", "subject": "00370"},
    {"card": "6F00655F33", "subject": "00371"},
    {"card": "6F006588E1", "subject": "00372"},
    {"card": "6F00658E21", "subject": "00373"},
    {"card": "6F0065BE25", "subject": "00374"},
    {"card": "6F00659517", "subject": "00375"},
    {"card": "6F0065B609", "subject": "00376"},
    {"card": "6F00658344", "subject": "00377"},
    {"card": "6F00657889", "subject": "00378"},
    {"card": "6F0065AEA5", "subject": "00379"},
    {"card": "6F0065658A", "subject": "00380"},
    {"card": "6F0065A059", "subject": "00381"},
    {"card": "6F00655CBE", "subject": "00382"},
    {"card": "6F00657109", "subject": "00383"},
    {"card": "6F0065844F", "subject": "00384"},
    {"card": "6F0065AFCA", "subject": "00385"},
    {"card": "7A00613E55", "subject": "00001"},
    {"card": "6D001F3BE4", "subject": "00002"},
    {"card": "6D001F07DC", "subject": "00003"},
    {"card": "6D00067383", "subject": "00004"},
    {"card": "7A00615849", "subject": "00005"},
    {"card": "7A0061A367", "subject": "00006"},
    {"card": "7A00618F51", "subject": "00007"},
    {"card": "7A006183C3", "subject": "00008"},
    {"card": "7A00617387", "subject": "00009"},
    {"card": "7A00618A07", "subject": "00010"},
    {"card": "7A00615D75", "subject": "00011"},
    {"card": "7A006181D0", "subject": "00012"},
    {"card": "7A0061770F", "subject": "00013"},
    {"card": "7A00616641", "subject": "00014"},
    {"card": "7A0061A1E8", "subject": "00015"},
    {"card": "7A00614368", "subject": "00016"},
    {"card": "7A00614388", "subject": "00017"},
    {"card": "7A00613884", "subject": "00018"},
    {"card": "7A006164E7", "subject": "00019"},
    {"card": "7A0061576A", "subject": "00020"},
    {"card": "7A00619343", "subject": "00021"},
    {"card": "7A0061825A", "subject": "00022"},
    {"card": "7A0061899D", "subject": "00023"},
    {"card": "7A00615858", "subject": "00024"},
    {"card": "7A006160F3", "subject": "00025"},
    {"card": "7A00618246", "subject": "00026"},
    {"card": "7A00615D40", "subject": "00027"},
    {"card": "7A00614631", "subject": "00028"},
    {"card": "7A00618A73", "subject": "00029"},
    {"card": "7A00614927", "subject": "00030"},
    {"card": "7A0061534E", "subject": "00031"},
    {"card": "7A00619DF5", "subject": "00032"},
    {"card": "7A006183F0", "subject": "00033"},
    {"card": "7A00615CA6", "subject": "00034"},
    {"card": "7A00614123", "subject": "00035"},
    {"card": "7A006199F2", "subject": "00036"},
    {"card": "01130F097D", "subject": "00037"},
    {"card": "7A006150B1", "subject": "00038"},
    {"card": "7A0061386F", "subject": "00039"},
    {"card": "7A00616FE2", "subject": "00040"},
    {"card": "7A006166A5", "subject": "00041"},
    {"card": "7A006156E9", "subject": "00042"},
    {"card": "7A00619E84", "subject": "00043"},
    {"card": "7A006195B5", "subject": "00044"},
    {"card": "7A0061A276", "subject": "00045"},
    {"card": "7A00617A6C", "subject": "00046"},
    {"card": "7A00614214", "subject": "00047"},
    {"card": "7A00618574", "subject": "00048"},
    {"card": "7A006193B0", "subject": "00049"},
    {"card": "7A006149FC", "subject": "00050"},
    {"card": "7A006182DE", "subject": "00051"},
    {"card": "7A00617DE6", "subject": "00052"},
    {"card": "7A006198BC", "subject": "00053"},
    {"card": "7A006176D1", "subject": "00054"},
    {"card": "7A00616C8A", "subject": "00055"},
    {"card": "7A0061954D", "subject": "00056"},
    {"card": "7A00614616", "subject": "00057"},
    {"card": "7A006184DA", "subject": "00058"},
    {"card": "7A00614F5B", "subject": "00059"},
    {"card": "7A0061501F", "subject": "00060"},
    {"card": "7A00615707", "subject": "00061"},
    {"card": "7A00618E06", "subject": "00062"},
    {"card": "7A00615556", "subject": "00063"},
    {"card": "7A00615F08", "subject": "00064"},
    {"card": "7A006142DB", "subject": "00065"},
    {"card": "7A00614D3D", "subject": "00066"},
    {"card": "7A00613C52", "subject": "00067"},
    {"card": "7A006178CF", "subject": "00068"},
    {"card": "7A006163E5", "subject": "00069"},
    {"card": "7A006192C9", "subject": "00070"},
    {"card": "7A0061694F", "subject": "00071"},
    {"card": "7A00616319", "subject": "00072"},
    {"card": "7A00614F59", "subject": "00073"},
    {"card": "7A00618DE0", "subject": "00074"},
    {"card": "7A00617ED3", "subject": "00075"},
    {"card": "7A00617863", "subject": "00076"},
    {"card": "7A00618BA3", "subject": "00077"},
    {"card": "7A0078E293", "subject": "00078"},
    {"card": "7A0078FB0D", "subject": "00079"},
    {"card": "7A0079337B", "subject": "00080"},
    {"card": "7A00790747", "subject": "00081"},
    {"card": "7A0078D9AA", "subject": "00082"},
    {"card": "7A0078C90D", "subject": "00083"},
    {"card": "7A00791E39", "subject": "00084"},
    {"card": "7A0079330B", "subject": "00085"},
    {"card": "7A0078E783", "subject": "00086"},
    {"card": "7A0078F767", "subject": "00087"},
    {"card": "7A00792969", "subject": "00088"},
    {"card": "7A00790674", "subject": "00089"},
    {"card": "7A00792EAB", "subject": "00090"},
    {"card": "7A0078DE54", "subject": "00091"},
    {"card": "7A0079073D", "subject": "00092"},
    {"card": "7A0078FB68", "subject": "00093"},
    {"card": "7A0078EB26", "subject": "00094"},
    {"card": "7A00790133", "subject": "00095"},
    {"card": "7A007910A6", "subject": "00096"},
    {"card": "7A0078DBFB", "subject": "00097"},
    {"card": "7A0079311D", "subject": "00098"},
    {"card": "7A0078F6EE", "subject": "00099"},
    {"card": "7A0078E20D", "subject": "00100"},
    {"card": "7A00790B62", "subject": "00101"},
    {"card": "7A00790DCE", "subject": "00102"},
    {"card": "7A0078EA8E", "subject": "00103"},
    {"card": "7A0078E9A7", "subject": "00104"},
    {"card": "7A00790ADD", "subject": "00105"},
    {"card": "7A00792AD3", "subject": "00106"},
    {"card": "7A007926C2", "subject": "00107"},
    {"card": "7A0078FA68", "subject": "00108"},
    {"card": "7A0078FE49", "subject": "00109"},
    {"card": "7A006199E5", "subject": "00110"},
    {"card": "7A00618D9C", "subject": "00111"},
    {"card": "7A00617D3F", "subject": "00112"},
    {"card": "7A00613A21", "subject": "00113"},
    {"card": "7A00615ED6", "subject": "00114"},
    {"card": "7A00619DA4", "subject": "00115"},
    {"card": "7A00616C54", "subject": "00116"},
    {"card": "7A00614763", "subject": "00117"},
    {"card": "7A006197BE", "subject": "00118"},
    {"card": "7A006143F0", "subject": "00119"},
    {"card": "7A0061677E", "subject": "00120"},
    {"card": "7A00618106", "subject": "00121"},
    {"card": "7A00616537", "subject": "00122"},
    {"card": "7A00618C25", "subject": "00123"},
    {"card": "7A00618486", "subject": "00124"},
    {"card": "7A00614FF3", "subject": "00125"},
    {"card": "7A00616E41", "subject": "00126"},
    {"card": "7A006162C9", "subject": "00127"},
    {"card": "7A00619791", "subject": "00128"},
    {"card": "7A00615F3D", "subject": "00129"},
    {"card": "7A006161DE", "subject": "00130"},
    {"card": "7A00617B50", "subject": "00131"},
    {"card": "7A00617E8B", "subject": "00132"},
    {"card": "7A006189ED", "subject": "00133"},
    {"card": "7A00617F78", "subject": "00134"},
    {"card": "7A00619A1E", "subject": "00135"},
    {"card": "7A00617B88", "subject": "00136"},
    {"card": "7A006141EC", "subject": "00137"},
    {"card": "7A00613E1E", "subject": "00138"},
    {"card": "7A00618E14", "subject": "00139"},
    {"card": "7A006176DE", "subject": "00140"},
    {"card": "7A0061661B", "subject": "00141"},
    {"card": "7A00617933", "subject": "00142"},
    {"card": "7A00616856", "subject": "00143"},
    {"card": "7A00619F54", "subject": "00144"},
    {"card": "7A00613D10", "subject": "00145"},
    {"card": "7A00617502", "subject": "00146"},
    {"card": "7A0079165C", "subject": "00147"},
    {"card": "7A00619AEC", "subject": "00148"},
    {"card": "7A00617206", "subject": "00149"},
    {"card": "7A00792A13", "subject": "00150"},
    {"card": "7A00616716", "subject": "00151"},
    {"card": "7A00614708", "subject": "00152"},
    {"card": "7A0078CB3B", "subject": "00153"},
    {"card": "7A0078F7B0", "subject": "00154"},
    {"card": "7A00619B5F", "subject": "00155"},
    {"card": "7A00614DCD", "subject": "00156"},
    {"card": "7A0061A157", "subject": "00157"},
    {"card": "7A00614FFC", "subject": "00158"},
    {"card": "7A0061829A", "subject": "00159"},
    {"card": "7A00613A34", "subject": "00160"},
    {"card": "7A00615705", "subject": "00161"},
    {"card": "7A0061A31B", "subject": "00162"},
    {"card": "7A006189FA", "subject": "00163"},
    {"card": "7A006199EF", "subject": "00164"},
    {"card": "7A00618EBE", "subject": "00165"},
    {"card": "7A00616F55", "subject": "00166"},
    {"card": "7A0061658D", "subject": "00167"},
    {"card": "7A006176DF", "subject": "00168"},
    {"card": "7A0061804A", "subject": "00169"},
    {"card": "7A006180B3", "subject": "00170"},
    {"card": "7A00617CEC", "subject": "00171"},
    {"card": "7A00616A40", "subject": "00172"},
    {"card": "7A00614B75", "subject": "00173"},
    {"card": "7A006170A2", "subject": "00174"},
    {"card": "7A00613C3B", "subject": "00175"},
    {"card": "7A0061390A", "subject": "00176"},
    {"card": "7A006169DC", "subject": "00177"},
    {"card": "7A00618D8A", "subject": "00178"},
    {"card": "7A006172F8", "subject": "00179"},
    {"card": "7A0061A27F", "subject": "00180"},
    {"card": "7A0061731B", "subject": "00181"},
    {"card": "7A00618A31", "subject": "00182"},
    {"card": "7A0061768A", "subject": "00183"},
    {"card": "7A00619C7E", "subject": "00184"},
    {"card": "7A00619683", "subject": "00185"},
    {"card": "7A0061A228", "subject": "00186"},
    {"card": "7A00617EFE", "subject": "00187"},
    {"card": "7A00616B2A", "subject": "00188"},
    {"card": "7A00613AC5", "subject": "00189"},
    {"card": "7A00617E0C", "subject": "00190"},
    {"card": "7A006184B1", "subject": "00191"},
    {"card": "7A00618C12", "subject": "00192"},
    {"card": "7A00613D00", "subject": "00193"},
    {"card": "7A00613805", "subject": "00194"},
    {"card": "7A00618190", "subject": "00195"},
    {"card": "7A006190AF", "subject": "00196"},
    {"card": "7A006190F7", "subject": "00197"},
    {"card": "7A00616041", "subject": "00198"},
    {"card": "7A0077A3A0", "subject": "00199"},
    {"card": "7A00619907", "subject": "00200"},
    {"card": "7A00618969", "subject": "00201"},
    {"card": "7A005A09C2", "subject": "00202"},
    {"card": "7A00617457", "subject": "00203"},
    {"card": "7A00616B3C", "subject": "00204"},
    {"card": "7A00614F98", "subject": "00205"},
    {"card": "7A00614AE3", "subject": "00206"},
    {"card": "7A00617F99", "subject": "00207"},
    {"card": "7A006149A7", "subject": "00208"},
    {"card": "7A006187C9", "subject": "00209"},
    {"card": "7A006174BD", "subject": "00210"},
    {"card": "7A00615259", "subject": "00211"},
    {"card": "7A006146C3", "subject": "00212"},
    {"card": "7A00613BF3", "subject": "00213"},
    {"card": "7A00619CE6", "subject": "00214"},
    {"card": "7A006171CC", "subject": "00215"},
    {"card": "7A00618DFE", "subject": "00216"},
    {"card": "7A00615A07", "subject": "00217"},
    {"card": "7A00618D3E", "subject": "00218"},
    {"card": "7A00617BDE", "subject": "00219"},
    {"card": "7A00618CE3", "subject": "00220"},
    {"card": "7A006165D3", "subject": "00221"},
    {"card": "7A006159AE", "subject": "00222"},
    {"card": "7A00617B26", "subject": "00223"},
    {"card": "7A006197C6", "subject": "00224"},
    {"card": "7A00618BD2", "subject": "00225"},
    {"card": "7A0061643F", "subject": "00226"},
    {"card": "7A0061591E", "subject": "00227"},
    {"card": "7A00615091", "subject": "00228"},
    {"card": "7A00619612", "subject": "00229"},
    {"card": "7A00618F68", "subject": "00230"},
    {"card": "7A00618151", "subject": "00231"},
    {"card": "7A006199A1", "subject": "00232"},
    {"card": "7A00616241", "subject": "00233"},
    {"card": "7A0061496A", "subject": "00234"},
    {"card": "7A00619A61", "subject": "00235"},
    {"card": "7A006177D0", "subject": "00236"},
    {"card": "7A0077D44F", "subject": "00237"},
    {"card": "7A0077849B", "subject": "00238"},
    {"card": "7A0077B625", "subject": "00239"},
    {"card": "7A00778D6B", "subject": "00240"},
    {"card": "7A0077CAF7", "subject": "00241"},
    {"card": "7A006141AF", "subject": "00251"},
    {"card": "7A00613882", "subject": "00252"},
    {"card": "7A00614224", "subject": "00253"},
    {"card": "7A00613F36", "subject": "00254"},
    {"card": "7A00619C08", "subject": "00255"},
    {"card": "7A00614FDA", "subject": "00256"},
    {"card": "7A00619462", "subject": "00257"},
    {"card": "7A00613D6A", "subject": "00258"},
    {"card": "7A006195A7", "subject": "00259"},
    {"card": "7A00617904", "subject": "00260"},
    {"card": "7A00614193", "subject": "00261"},
    {"card": "7A0061952B", "subject": "00262"},
    {"card": "7A00615FDA", "subject": "00263"},
    {"card": "7A00618AF7", "subject": "00264"},
    {"card": "7A0061697D", "subject": "00265"},
    {"card": "7A00614B64", "subject": "00242"},
    {"card": "7A0077CDF5", "subject": "00243"},
    {"card": "7A00617E5F", "subject": "00244"},
    {"card": "7A0061A57A", "subject": "00245"},
    {"card": "7A00619F34", "subject": "00246"},
    {"card": "7A006156A1", "subject": "00247"},
    {"card": "7A00619B63", "subject": "00248"},
    {"card": "7A006173FE", "subject": "00249"},
    {"card": "7A00617C71", "subject": "00250"},
    {"card": "7A00616300", "subject": "00266"},
    {"card": "7A006185CF", "subject": "00267"},
    {"card": "7A006166C5", "subject": "00268"},
    {"card": "7A00619C9D", "subject": "00269"},
    {"card": "7A00617A56", "subject": "00270"},
    {"card": "7A00614002", "subject": "00271"},
    {"card": "7A00619CDE", "subject": "00272"},
    {"card": "7A0061826B", "subject": "00273"},
    {"card": "7A006198AC", "subject": "00274"},
    {"card": "7A00614691", "subject": "00275"},
    {"card": "7A006160DD", "subject": "00276"},
    {"card": "7A00616704", "subject": "00277"},
    {"card": "7A006168B7", "subject": "00278"},
    {"card": "7A00617168", "subject": "00279"},
    {"card": "7A0061481A", "subject": "00280"},
    {"card": "7A006195EA", "subject": "00281"},
    {"card": "7A00617BF4", "subject": "00282"},
    {"card": "7A00614BAA", "subject": "00283"},
    {"card": "7A006173B5", "subject": "00284"},
    {"card": "7A006187C5", "subject": "00285"},
    {"card": "7A00617E03", "subject": "00286"},
    {"card": "7A0061818B", "subject": "00287"},
    {"card": "7A00616DEC", "subject": "00288"},
    {"card": "7A00614BEF", "subject": "00289"},
    {"card": "7A00616A99", "subject": "00290"},
    {"card": "7A00617F5C", "subject": "00291"},
    {"card": "7A006181EF", "subject": "00292"},
    {"card": "7A00616348", "subject": "00293"},
    {"card": "7A006162B7", "subject": "00294"},
    {"card": "7A00618B90", "subject": "00295"},
    {"card": "7A006185DC", "subject": "00296"},
    {"card": "7A00616396", "subject": "00297"},
    {"card": "7A00618846", "subject": "00298"},
    {"card": "7A00618D79", "subject": "00299"},
    {"card": "7A00615DAA", "subject": "00300"},
    {"card": "7A0061620C", "subject": "00301"},
    {"card": "7A00618B8C", "subject": "00302"},
    {"card": "7A00618196", "subject": "00303"},
    {"card": "7A00615CC6", "subject": "00304"},
    {"card": "7A0061841D", "subject": "00305"},
    {"card": "7A006179DA", "subject": "00306"},
    {"card": "7A00613A7E", "subject": "00307"},
    {"card": "7A00613C09", "subject": "00308"},
    {"card": "7A00619F03", "subject": "00309"},
    {"card": "7A006166C0", "subject": "00310"},
    {"card": "7A00614FBD", "subject": "00311"},
    {"card": "7A0061402F", "subject": "00312"},
    {"card": "7A006158A7", "subject": "00313"},
    {"card": "7A00615F44", "subject": "00314"},
    {"card": "7A00615E3D", "subject": "00315"},
    {"card": "7A00616D0C", "subject": "00316"},
    {"card": "7A0061A2E0", "subject": "00317"},
    {"card": "7A0061A102", "subject": "00318"},
    {"card": "7A00616115", "subject": "00319"},
    {"card": "7A00613BCD", "subject": "00320"},
    {"card": "6F0065BDB4", "subject": "00386"},
    {"card": "6F0065C6F3", "subject": "00387"},
    {"card": "6F00659455", "subject": "00388"},
    {"card": "6F0065759F", "subject": "00389"},
    {"card": "6F0065AF5E", "subject": "00390"},
    {"card": "6F006587EE", "subject": "00391"},
    {"card": "6F00658535", "subject": "00392"},
    {"card": "6F00656923", "subject": "00393"},
    {"card": "6F0065AC7F", "subject": "00394"},
    {"card": "6F0065A2DE", "subject": "00395"},
    {"card": "6F00658406", "subject": "00396"},
    {"card": "6F00656C5C", "subject": "00397"},
    {"card": "6F0065AB81", "subject": "00398"},
    {"card": "6F00659090", "subject": "00399"},
    {"card": "6F006569CB", "subject": "00400"},
    {"card": "7A00615E05", "subject": "00401"},
    {"card": "6F0065626B", "subject": "00402"},
    {"card": "6F0065C3EE", "subject": "00403"},
    {"card": "6F006599EE", "subject": "00404"},
    {"card": "6F0065A39A", "subject": "00405"},
    {"card": "6F0065C352", "subject": "00406"},
    {"card": "6F0065BB32", "subject": "00407"},
    {"card": "6F00657D53", "subject": "00408"},
    {"card": "6F00659825", "subject": "00409"},
    {"card": "6F006582D4", "subject": "00410"},
    {"card": "6F00655E50", "subject": "00412"},
    {"card": "6F00655E72", "subject": "00413"},
    {"card": "6F00656B38", "subject": "00414"},
    {"card": "6F00655DCA", "subject": "00415"},
    {"card": "6F0065AE78", "subject": "00416"},
    {"card": "6F00656DFD", "subject": "00417"},
    {"card": "6F006578FE", "subject": "00418"},
    {"card": "6F006575BF", "subject": "00419"},
    {"card": "6F0065C6EC", "subject": "00420"},
    {"card": "6F0065B38A", "subject": "00421"},
    {"card": "6F0065C595", "subject": "00422"},
    {"card": "6F0065C094", "subject": "00423"},
    {"card": "6F00659A98", "subject": "00424"},
    {"card": "01142891B0", "subject": "00425"},
    {"card": "6F00659845", "subject": "00426"},
    {"card": "6F0065B8AA", "subject": "00427"},
    {"card": "6F0065BD9E", "subject": "00428"},
    {"card": "6F00658B84", "subject": "00429"},
    {"card": "6F0065783D", "subject": "00430"},
    {"card": "6F00656236", "subject": "00431"},
    {"card": "6F006584CE", "subject": "00432"},
    {"card": "6F0065A245", "subject": "00433"},
    {"card": "6F00657EDA", "subject": "00434"},
    {"card": "6F00658393", "subject": "00435"},
    {"card": "6F006591ED", "subject": "00436"},
    {"card": "6F0065BD93", "subject": "00437"},
    {"card": "6F0065C1F2", "subject": "00438"},
    {"card": "6F006584D1", "subject": "00439"},
    {"card": "6F0065AACD", "subject": "00440"},
    {"card": "6F0065A743", "subject": "00441"},
    {"card": "6F0065A832", "subject": "00442"},
    {"card": "6F00656368", "subject": "00443"},
    {"card": "6F0065A515", "subject": "00444"},
    {"card": "75000FF6B2", "subject": "00445"},
    {"card": "75000FE389", "subject": "00446"},
    {"card": "75000FF1A1", "subject": "00447"},
    {"card": "75000FE9CB", "subject": "00448"},
    {"card": "75000FF31E", "subject": "00449"},
    {"card": "73000A5D08", "subject": "00450"},
    {"card": "3C00C9E6BD", "subject": "00481"},
    {"card": "3C00B3B793", "subject": "00482"},
    {"card": "3C00C93950", "subject": "00483"},
    {"card": "3C00B4A9CC", "subject": "00484"},
    {"card": "3C00B4A1AC", "subject": "00485"},
    {"card": "3C00C9F081", "subject": "00486"},
    {"card": "3C00CA3493", "subject": "00487"},
    {"card": "3C00B4648E", "subject": "00488"},
    {"card": "3C00C98C84", "subject": "00489"},
    {"card": "3C00B42BD7", "subject": "00490"},
    {"card": "01149B555E", "subject": "00492"},
    {"card": "01149BD5E4", "subject": "00493"},
    {"card": "01149BDC1D", "subject": "00494"},
    {"card": "01149BDC36", "subject": "00495"},
    {"card": "01149BEDAD", "subject": "00496"},
    {"card": "01149BBA44", "subject": "00497"},
    {"card": "01149BDD6A", "subject": "00498"},
    {"card": "01149BE797", "subject": "00499"},
    {"card": "01149BED64", "subject": "00500"},
    {"card": "01154A7260", "subject": "00501"},
    {"card": "01154A7DA8", "subject": "00502"},
    {"card": "01154A79F2", "subject": "00503"},
    {"card": "01154A7CB9", "subject": "00504"},
    {"card": "01154A7B45", "subject": "00505"},
    {"card": "01154A7C64", "subject": "00506"},
    {"card": "01154A5829", "subject": "00507"},
    {"card": "01154A8501", "subject": "00508"},
    {"card": "01154A7BC5", "subject": "00509"},
    {"card": "01154A696B", "subject": "00510"},
    {"card": "3C00B3EE3B", "subject": "00511"},
    {"card": "01154A5F6C", "subject": "00512"},
    {"card": "01154A6A03", "subject": "00513"},
    {"card": "01154A5FED", "subject": "00514"},
    {"card": "01154A669C", "subject": "00515"},
    {"card": "01154A64FD", "subject": "00516"},
    {"card": "01154A85B9", "subject": "00517"},
    {"card": "01154A6BEC", "subject": "00518"},
    {"card": "01154A5AFE", "subject": "00519"},
    {"card": "01154A8180", "subject": "00520"},
    {"card": "01154A743D", "subject": "00521"},
    {"card": "01154A8C30", "subject": "00522"},
    {"card": "01154A806D", "subject": "00523"},
    {"card": "01154A8065", "subject": "00524"},
    {"card": "01154A789E", "subject": "00525"},
    {"card": "01154A7CFD", "subject": "00526"},
    {"card": "01154A6CBC", "subject": "00527"},
    {"card": "01154A6CF5", "subject": "00528"},
    {"card": "01154A8F6C", "subject": "00529"},
    {"card": "01154A6C56", "subject": "00530"},
    {"card": "01154A5A89", "subject": "00531"},
    {"card": "01154A5A89", "subject": "00532"},
    {"card": "01154A6E08", "subject": "00533"},
    {"card": "01154A6C91", "subject": "00534"},
    {"card": "01154A91D6", "subject": "00535"},
    {"card": "01154A7598", "subject": "00536"},
    {"card": "01154A6C49", "subject": "00537"},
    {"card": "01154A7654", "subject": "00538"},
    {"card": "01154A84FD", "subject": "00539"},
    {"card": "01154A65A8", "subject": "00540"},
    {"card": "01154A5B41", "subject": "00541"},
    {"card": "01154A7558", "subject": "00542"},
    {"card": "01154A8CAC", "subject": "00543"},
    {"card": "01154A5434", "subject": "00544"},
    {"card": "01154A640B", "subject": "00545"},
    {"card": "01154A6885", "subject": "00546"},
    {"card": "0114C2B201", "subject": "00547"},
    {"card": "0114C24E21", "subject": "00548"},
    {"card": "0114C2ADB7", "subject": "00549"},
    {"card": "0114C27F91", "subject": "00550"},
    {"card": "0114C28AD7", "subject": "00551"},
    {"card": "0114C2C254", "subject": "00552"},
    {"card": "0114C2C12B", "subject": "00553"},
    {"card": "0114C28E8D", "subject": "00554"},
    {"card": "0114C2A6C0", "subject": "00555"},
    {"card": "0114C2B9AF", "subject": "00556"},
    {"card": "0114C293CB", "subject": "00557"},
    {"card": "0114C2542E", "subject": "00558"},
    {"card": "0114C2A22B", "subject": "00559"},
    {"card": "0114C2AB95", "subject": "00560"},
    {"card": "01154A84F4", "subject": "00531"},
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
# Badge: number (mostrato nella colonna Badge) e code (letto dal lettore) = codice tessera
card_registry = [{"number": r["card"], "code": r["card"]} for r in reservations]

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
    """Registra le tessere una per una (non esiste un upload xlsx per le tessere).
    Le tessere già registrate con un numero diverso dal codice vengono corrette."""
    response = requests.get(f"{base_url}/card-registry/list", headers=HEADERS)
    response.raise_for_status()
    existing = {str(c["code"]).strip().upper(): c for c in response.json()["data"] if c.get("code")}
    created, updated = 0, 0
    ws_url = base_url.replace("http", "ws", 1) + f"/card-registry?token={AUTH_TOKEN}"
    with ws_connect(ws_url) as ws:
        for i, c in enumerate(card_registry, start=1):
            current = existing.get(c["code"].upper())
            if current:
                if str(current.get("number")) != c["number"]:
                    ok, detail = rename_locked("card-registry", current["id"], c, ws, i)
                    if ok:
                        updated += 1
                    else:
                        print(f"Tessera {c['code']}: errore {detail}")
                continue
            response = requests.post(f"{base_url}/card-registry", json=c, headers=HEADERS)
            if response.ok:
                created += 1
            else:
                print(f"Tessera {c['code']}: errore {response.status_code} {response.text}")
    print(f"Tessere create: {created} | corrette: {updated}")
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
