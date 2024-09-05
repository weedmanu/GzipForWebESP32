import gzip
import PySimpleGUI as sg
import os

# Fonction pour compresser le fichier HTML
def compresser_html(html_file_path, gzip_file_path):
    try:
        with open(html_file_path, 'rb') as f_in:
            with gzip.open(gzip_file_path, 'wb') as f_out:
                f_out.writelines(f_in)
        #sg.popup('Compression réussie!')
    except Exception as e:
        sg.popup_error(f"Erreur lors de la compression : {e}", icon=sg.SYSTEM_TRAY_MESSAGE_ICON_CRITICAL)

# Fonction pour lire le fichier compressé et le convertir en tableau de uint8_t
def lire_gzip(gzip_file_path):
    try:
        with open(gzip_file_path, 'rb') as f:
            return f.read()
    except Exception as e:
        sg.popup_error(f"Erreur lors de la lecture du fichier gzip : {e}", icon=sg.SYSTEM_TRAY_MESSAGE_ICON_CRITICAL)
        return None

# Fonction pour écrire le tableau dans un fichier .h
def ecrire_header(header_file_path, byte_array, array_name):
    try:
        with open(header_file_path, 'w') as f:
            f.write(f'#ifndef {array_name.upper()}_H\n')
            f.write(f'#define {array_name.upper()}_H\n\n')
            f.write('#include <stdint.h>\n\n')
            f.write(f'const uint8_t {array_name}[] = {{')
            f.write(', '.join(f'0x{byte:02x}' for byte in byte_array))
            f.write('};\n\n')
            f.write(f'const size_t {array_name}_len = {len(byte_array)};\n\n')
            f.write(f'#endif // {array_name.upper()}_H\n')
        #sg.popup('Fichier header créé avec succès!')
    except Exception as e:
        sg.popup_error(f"Erreur lors de l'écriture du fichier header : {e}", icon=sg.SYSTEM_TRAY_MESSAGE_ICON_CRITICAL)
        return False
    return True

# Fonction pour supprimer le fichier compressé
def supprimer_fichier(fichier_path):
    try:
        os.remove(fichier_path)
        #sg.popup('Fichier compressé supprimé avec succès!')
    except Exception as e:
        sg.popup_error(f"Erreur lors de la suppression du fichier compressé : {e}", icon=sg.SYSTEM_TRAY_MESSAGE_ICON_CRITICAL)

# Définir la mise en page de l'interface graphique
sg.theme('TanBlue')  # Choisir un thème

tab1_layout = [
    [sg.Text('Chemin vers le fichier HTML', size=(22, 1), font=('Helvetica', 12, 'bold')), sg.InputText(key='html_file', font=('Helvetica', 12, 'bold')), sg.FileBrowse(font=('Helvetica', 12, 'bold'))],
    [sg.Button('Compresser et Convertir', size=(22, 1),font=('Helvetica', 12, 'bold')), sg.Button('Quitter', size=(10, 1), font=('Helvetica', 12, 'bold'))],
    [sg.Multiline(size=(100, 20), key='header_content', disabled=True, font=('Helvetica', 10, 'bold'))]
]

tab2_layout = [
    [sg.Text('Exemple', font=('Helvetica', 12, 'bold'))],
    [sg.Radio('Asynchrone', 'mode', key='asynchrone', font=('Helvetica', 12)), sg.Radio('Synchrone', 'mode', key='synchrone', font=('Helvetica', 12))],
    [sg.Button('Générer', size=(10, 1))],
    [sg.Multiline(size=(100, 20), key='integration_example', disabled=True, font=('Helvetica', 10, 'bold'))]
]

layout = [
    [sg.TabGroup([[sg.Tab('Compression', tab1_layout), sg.Tab('Exemple d\'intégration', tab2_layout, visible=False)]], key='tabs', font=('Helvetica', 14, 'bold'))]
]

# Créer la fenêtre
window = sg.Window('Compresser HTML et Convertir en Header', layout, finalize=True)

# Masquer l'onglet "Exemple d'intégration" au démarrage
window['tabs'].Widget.tab(1, state='hidden')

# Boucle d'événements
while True:
    event, values = window.read()
    if event == sg.WINDOW_CLOSED or event == 'Quitter':
        break
    if event == 'Compresser et Convertir':
        html_file_path = values['html_file']
        if not os.path.isfile(html_file_path):
            sg.popup_error("Le fichier HTML spécifié n'existe pas.", icon=sg.SYSTEM_TRAY_MESSAGE_ICON_CRITICAL)
            continue
        gzip_file_path = html_file_path + '.gz'
        base_name = os.path.splitext(os.path.basename(html_file_path))[0]
        header_file_path = os.path.join(os.path.dirname(html_file_path), base_name + '_html.h')
        array_name = base_name
        
        compresser_html(html_file_path, gzip_file_path)
        byte_array = lire_gzip(gzip_file_path)
        if byte_array:
            if ecrire_header(header_file_path, byte_array, array_name):
                supprimer_fichier(gzip_file_path)
                with open(header_file_path, 'r') as f:
                    header_content = f.read()
                window['header_content'].update(header_content)
                sg.popup('Conversion terminée!')
                window['tabs'].Widget.tab(1, state='normal')  # Afficher l'onglet "Exemple d'intégration"
    if event == 'Générer':
        mode = 'Asynchrone' if values['asynchrone'] else 'Synchrone'
        if mode == 'Synchrone':
            example_code = f"""#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include "{base_name}_html.h"

const char* ssid = "VOTRE_SSID";
const char* password = "VOTRE_PASSWORD";

WebServer server(80);

void handleRoot() {{
    server.sendHeader("Content-Encoding", "gzip");
    server.send_P(200, "text/html", (const char*){array_name}, {array_name}_len);
}}

void setup() {{
    Serial.begin(115200);
    Serial.print("Connexion au réseau : ");
    Serial.println(ssid);
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {{
        delay(1000);
        Serial.print(".");
    }}
    Serial.println();
    Serial.print("Connecté au WiFi, IP: ");
    Serial.println(WiFi.localIP());
    // Définir la route pour servir la page HTML décompressée
    server.on("/",handleRoot);
    server.begin();
}}

void loop() {{
    server.handleClient();
}}"""            
        else:
            example_code = f"""#include <Arduino.h>
#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include "{base_name}_html.h"

const char* ssid = "VOTRE_SSID";
const char* password = "VOTRE_PASSWORD";

AsyncWebServer server(80);

void setup() {{
    Serial.begin(115200);
    delay(1000);
    Serial.println();
    Serial.print("Connexion au réseau : ");
    Serial.println(ssid);
    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {{
        delay(1000);
        Serial.print(".");
    }}
    Serial.println();
    Serial.print("Connecté au WiFi, IP: ");
    Serial.println(WiFi.localIP());
    // Définir la route pour servir la page HTML décompressée
    server.on("/", HTTP_GET, [](AsyncWebServerRequest * request) {{
        AsyncWebServerResponse *response = request->beginResponse_P(200, "text/html", {array_name}, {array_name}_len);
        response->addHeader("Content-Encoding", "gzip");
        request->send(response);
    }});
    server.begin();
}}

void loop() {{
    // Rien à faire ici
}}"""

        window['integration_example'].update(example_code)

window.close()
