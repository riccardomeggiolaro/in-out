# ==============================================================
# = Module......: md_desktop_interface                       =
# = Description.: Interfaccia desktop per visualizzare IP   =
# = Author......: Sistema BARON                              =
# = Last rev....: 0.0001                                     =
# ==============================================================

# ==== LIBRERIE DA IMPORTARE ===================================
import time
import tkinter as tk
from tkinter import ttk
import socket
import libs.lb_log as lb_log
import libs.lb_config as lb_config
from libs.lb_utils import createThread, startThread, closeThread
# ==============================================================

name_module = "md_desktop_interface"

# Variabile globale per l'istanza della classe
desktop_interface = None

def init():
    """Inizializzazione del modulo"""
    global desktop_interface
    lb_log.info("init")
    desktop_interface = DesktopInterface()
    lb_log.info("end")

def start():
    """Avvio del modulo"""
    lb_log.info("start")
    while lb_config.g_enabled:  # CORRETTO: uso lb_config.g_enabled invece di lb_config.g_config.g_enabled
        time.sleep(1)
    lb_log.info("end")

class DesktopInterface:
    def __init__(self):
        """Inizializza l'interfaccia desktop"""
        self.window = None
        self.ip_label = None
        self.status_label = None
        self.thread_interface = None
        self.thread_update_ip = None
        self.enabled = True
        self.interface_closed_by_user = False  # Flag per sapere se chiusa dall'utente
        
        # Avvia l'interfaccia desktop
        self._start_interface()
    
    def _start_interface(self):
        """Avvia l'interfaccia desktop in un thread separato"""
        # Controlla se l'interfaccia desktop è abilitata nella configurazione
        desktop_config = lb_config.g_config.get("desktop_interface", {}) if hasattr(lb_config, 'g_config') else {}
        if desktop_config.get("enabled", True):  # Default abilitato se non specificato
            self.thread_interface = createThread(self._run_interface, ())
            startThread(self.thread_interface)
            
            # Avvia il thread di aggiornamento IP
            self.thread_update_ip = createThread(self._update_ip_loop, ())
            startThread(self.thread_update_ip)
    
    def show_interface(self):
        """Mostra l'interfaccia (riapre se chiusa)"""
        try:
            # Controlla se la finestra esiste ed è visibile
            if self.window is not None:
                try:
                    # Verifica se la finestra esiste ancora
                    if self.window.winfo_exists():
                        # La finestra esiste già - portala in primo piano
                        self.window.deiconify()  # Ripristina se minimizzata
                        self.window.lift()       # Porta in primo piano
                        self.window.focus_force()  # Forza il focus
                        self.window.attributes('-topmost', True)  # Temporaneamente in primo piano
                        self.window.after(100, lambda: self.window.attributes('-topmost', False))  # Rimuovi topmost dopo 100ms
                        lb_log.info("Interfaccia desktop già aperta - portata in primo piano")
                        return  # IMPORTANTE: esci senza creare nuove finestre
                    else:
                        # La finestra non esiste più, resetta il riferimento
                        self.window = None
                        self.ip_label = None
                        self.status_label = None
                except tk.TclError:
                    # La finestra è stata distrutta, resetta i riferimenti
                    self.window = None
                    self.ip_label = None
                    self.status_label = None
            
            # Se arriviamo qui, la finestra non esiste - creane una nuova
            # ma NON ricreare i thread, solo la finestra
            lb_log.info("Riaprendo interfaccia desktop...")
            self.interface_closed_by_user = False
            self._recreate_window_only()
            
        except Exception as e:
            lb_log.error(f"Errore nel mostrare interfaccia: {e}")
            # Tenta di ricreare solo la finestra
            self._recreate_window_only()
    
    def _recreate_window_only(self):
        """Ricrea solo la finestra senza toccare i thread"""
        try:
            lb_log.info("Richiesta riapertura interfaccia")
            
            # Resetta semplicemente il flag - il thread dell'interfaccia farà il resto
            self.interface_closed_by_user = False
            
            # Controlla se i thread sono ancora attivi
            interface_thread_alive = self.thread_interface and self.thread_interface.is_alive()
            update_thread_alive = self.thread_update_ip and self.thread_update_ip.is_alive()
            
            lb_log.info(f"Thread interfaccia attivo: {interface_thread_alive}")
            lb_log.info(f"Thread aggiornamento attivo: {update_thread_alive}")
            
            # Se il thread dell'interfaccia è attivo, lascia che gestisca la riapertura
            if interface_thread_alive:
                lb_log.info("Thread interfaccia attivo - lascio che gestisca la riapertura")
                # Il thread vedrà che interface_closed_by_user=False e ricreerà la finestra
            else:
                # Thread morto, ricrealo
                lb_log.info("Thread interfaccia morto - lo ricreo")
                self.thread_interface = createThread(self._run_interface, ())
                startThread(self.thread_interface)
            
            # Controlla il thread di aggiornamento
            if not update_thread_alive:
                lb_log.info("Thread aggiornamento morto - lo ricreo")
                self.thread_update_ip = createThread(self._update_ip_loop, ())
                startThread(self.thread_update_ip)
                
        except Exception as e:
            lb_log.error(f"Errore nel ricreare la finestra: {e}")
    
    def _restart_interface(self):
        """Riavvia completamente l'interfaccia"""
        try:
            lb_log.info("Riavvio interfaccia richiesto")
            
            # IMPORTANTE: Ferma prima i thread esistenti
            self._cleanup_threads()
            
            # Riavvia l'interfaccia
            self.enabled = True
            self.interface_closed_by_user = False
            
            # Crea NUOVI thread
            self.thread_interface = createThread(self._run_interface, ())
            startThread(self.thread_interface)
            
            self.thread_update_ip = createThread(self._update_ip_loop, ())
            startThread(self.thread_update_ip)
                
            lb_log.info("Interfaccia desktop riavviata con nuovi thread")
                
        except Exception as e:
            lb_log.error(f"Errore nel riavviare interfaccia: {e}")
    
    def _cleanup_threads(self):
        """Pulisce i thread esistenti"""
        lb_log.info("Pulizia thread esistenti...")
        
        # Segna come chiuso per far terminare i loop
        old_flag = self.interface_closed_by_user
        self.interface_closed_by_user = True
        
        # Aspetta che i thread terminino naturalmente
        if self.thread_interface and self.thread_interface.is_alive():
            lb_log.info("Aspettando terminazione thread interfaccia...")
            # Non possiamo fare join() sul thread GUI perché potrebbe essere bloccato su mainloop
            # Il thread si chiuderà quando la finestra viene distrutta
        
        if self.thread_update_ip and self.thread_update_ip.is_alive():
            lb_log.info("Aspettando terminazione thread aggiornamento IP...")
            self.thread_update_ip.join(timeout=2)  # Aspetta max 2 secondi
            if self.thread_update_ip.is_alive():
                lb_log.warning("Thread aggiornamento IP non si è fermato in tempo")
        
        # Ripristina il flag per il nuovo avvio
        self.interface_closed_by_user = old_flag
        
        lb_log.info("Pulizia thread completata")
    
    def _run_interface(self):
        """Esegue l'interfaccia tkinter - rimane attivo anche dopo chiusura finestra"""
        lb_log.info("Thread interfaccia GUI avviato")
        
        while self.enabled and lb_config.g_enabled:
            try:
                # Se non c'è finestra e non è stata chiusa dall'utente, creala
                if self.window is None and not self.interface_closed_by_user:
                    lb_log.info("Creando finestra interfaccia...")
                    self._create_window()
                    if self.window:
                        lb_log.info("Avvio mainloop...")
                        self.window.mainloop()  # Questo blocca finché la finestra non viene chiusa
                        lb_log.info("Mainloop terminato - finestra chiusa")
                        # NON terminare il thread, continua il loop
                
                # Se la finestra è stata chiusa dall'utente, aspetta che venga riaperta
                if self.interface_closed_by_user:
                    time.sleep(1)  # Aspetta 1 secondo prima di ricontrollare
                    continue
                
                # Se arriviamo qui senza finestra, aspetta un po'
                if self.window is None:
                    time.sleep(1)
                    
            except Exception as e:
                lb_log.error(f"Errore nell'interfaccia desktop: {e}")
                time.sleep(5)  # Aspetta prima di riprovare
        
        # Pulizia finale quando il thread deve terminare
        if self.window:
            try:
                self.window.quit()
                self.window.destroy()
            except:
                pass
        self.window = None
        self.ip_label = None
        self.status_label = None
        lb_log.info("Thread interfaccia GUI terminato")
    
    def _create_window(self):
        """Crea la finestra dell'interfaccia"""
        try:
            # Crea la finestra principale
            app_name = getattr(lb_config, 'g_name', 'BARON')
            self.window = tk.Tk()
            self.window.title(f"BARON {app_name}")
            
            # Dimensioni iniziali compatibili con TUTTI i PC
            self.window.geometry("350x280")
            self.window.resizable(True, True)  # RIDIMENSIONABILE dall'utente
            self.window.minsize(300, 250)  # Dimensioni minime per funzionalità
            # Nessun maxsize = può ingrandire quanto vuole
            
            # Configura lo stile
            style = ttk.Style()
            style.theme_use('clam')
            
            # Frame principale con padding ridotto per PC piccoli
            main_frame = ttk.Frame(self.window, padding="15")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # FRAME SUPERIORE - contenuto fisso
            top_frame = ttk.Frame(main_frame)
            top_frame.pack(fill=tk.X, pady=(0, 5))
            
            # Titolo (font ridotto per PC piccoli)
            title_label = ttk.Label(
                top_frame, 
                text=f"BARON {app_name}",
                font=('Arial', 14, 'bold')
            )
            title_label.pack()
            
            # Etichetta IP
            ip_title = ttk.Label(top_frame, text="Indirizzo IP:", font=('Arial', 10))
            ip_title.pack(pady=(8, 0))
            
            self.ip_label = ttk.Label(
                top_frame, 
                text="Caricamento...",
                font=('Arial', 18, 'bold'),
                foreground='blue'
            )
            self.ip_label.pack(pady=(3, 8))
            
            # Separatore
            separator = ttk.Separator(top_frame, orient='horizontal')
            separator.pack(fill=tk.X, pady=3)
            
            # FRAME CENTRALE - status che si espande con la finestra
            middle_frame = ttk.Frame(main_frame)
            middle_frame.pack(fill=tk.BOTH, expand=True, pady=3)  # Si espande
            
            self.status_label = ttk.Label(
                middle_frame,
                text="Inizializzazione...",
                font=('Arial', 9),
                justify=tk.CENTER,
                wraplength=300,  # Si adatta al ridimensionamento
                anchor='center'
            )
            self.status_label.pack(expand=True, fill=tk.BOTH)
            
            # FRAME INFERIORE - pulsante SEMPRE in fondo
            bottom_frame = ttk.Frame(main_frame)
            bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)
            
            # Separatore
            separator2 = ttk.Separator(bottom_frame, orient='horizontal')
            separator2.pack(fill=tk.X, pady=(5, 8))
            
            # Pulsante Spegni Programma - SEMPRE VISIBILE
            self.shutdown_button = ttk.Button(
                bottom_frame,
                text="🔴 Spegni Programma",
                command=self._shutdown_program
            )
            self.shutdown_button.pack(pady=(0, 5))
            
            # Posiziona la finestra al centro dello schermo
            self.window.update_idletasks()
            
            # Ottieni dimensioni schermo
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            
            # Calcola posizione centrata
            x = max(0, (screen_width - 350) // 2)
            y = max(0, (screen_height - 280) // 2)
            
            # Se lo schermo è troppo piccolo, posiziona in alto a sinistra
            if screen_width < 400 or screen_height < 320:
                x, y = 10, 10
            
            self.window.geometry(f"+{x}+{y}")
            
            # Gestione chiusura finestra
            self.window.protocol("WM_DELETE_WINDOW", self._on_closing)
            
            # Bind evento ridimensionamento per aggiornare wraplength
            self.window.bind('<Configure>', self._on_window_resize)
            
            lb_log.info(f"Interfaccia desktop ridimensionabile creata 350x280 su schermo {screen_width}x{screen_height}")
            
        except Exception as e:
            lb_log.error(f"Errore nella creazione interfaccia: {e}")
    
    def _on_window_resize(self, event):
        """Gestisce il ridimensionamento della finestra"""
        try:
            # Aggiorna il wraplength del testo in base alla larghezza della finestra
            if event.widget == self.window and self.status_label:
                new_width = max(200, self.window.winfo_width() - 60)  # Margine 60px
                self.status_label.configure(wraplength=new_width)
        except Exception as e:
            pass  # Ignora errori durante il ridimensionamento
    
    def _shutdown_program(self):
        """Spegne completamente il programma BARON"""
        try:
            lb_log.info("Richiesta spegnimento programma dall'interfaccia desktop")
            
            # Mostra dialog di conferma
            from tkinter import messagebox
            result = messagebox.askyesno(
                "Conferma Spegnimento",
                "Sei sicuro di voler spegnere completamente il programma BARON?",
                parent=self.window
            )
            
            if result:  # Se l'utente clicca "Sì"
                lb_log.info("Spegnimento confermato - avvio shutdown")
                
                # Ferma tutti i loop del sistema
                lb_config.g_enabled = False
                
                # Forza chiusura interfaccia
                self.enabled = False
                
                # Chiudi la finestra
                if self.window:
                    self.window.destroy()
                
                # Termina il programma
                import os
                os._exit(0)
                
        except Exception as e:
            lb_log.error(f"Errore nello spegnimento: {e}")
            import os
            os._exit(1)
    
    def _update_ip_loop(self):
        """Loop di aggiornamento dell'IP"""
        lb_log.info("Thread aggiornamento IP avviato")
        
        while self.enabled and lb_config.g_enabled:
            try:
                # Continua sempre ad aggiornare, anche se la finestra è chiusa
                # così quando viene riaperta ha già i dati aggiornati
                if self.window and self.ip_label and not self.interface_closed_by_user:
                    try:
                        # Verifica che la finestra esista ancora
                        if self.window.winfo_exists():
                            # Ottiene l'IP corrente
                            current_ip = self.getLocalIP()
                            all_ips = self.getAllIPs()
                            
                            # Aggiorna l'interfaccia nel thread principale
                            self.window.after(0, lambda ip=current_ip, ips=all_ips: self._update_labels(ip, ips))
                    except tk.TclError:
                        # Finestra distrutta, continua comunque il loop
                        pass
                    except Exception as e:
                        lb_log.error(f"Errore nell'aggiornamento interfaccia: {e}")
                
                time.sleep(5)  # Aggiorna ogni 5 secondi
            except Exception as e:
                lb_log.error(f"Errore nell'aggiornamento IP: {e}")
                time.sleep(5)
        
        lb_log.info("Thread aggiornamento IP terminato")
    
    def _update_labels(self, primary_ip, all_ips):
        """Aggiorna le etichette nell'interfaccia"""
        try:
            if self.ip_label:
                self.ip_label.config(text=primary_ip)
            
            if self.status_label:
                # Ottieni nome e versione in modo sicuro
                app_name = getattr(lb_config, 'g_name', 'BARON')
                app_version = getattr(lb_config, 'g_vers', '1.0')
                
                status_text = f"BARON {app_name} v{app_version}\n"
                status_text += f"Status: {'RUNNING' if lb_config.g_enabled else 'STOPPED'}\n"
                if len(all_ips) > 1:
                    status_text += f"Altri IP: {', '.join(all_ips[1:])}"
                self.status_label.config(text=status_text)
        except Exception as e:
            lb_log.error(f"Errore nell'aggiornamento etichette: {e}")
    
    def _on_closing(self):
        """Gestisce la chiusura della finestra"""
        lb_log.info("Chiusura interfaccia richiesta dall'utente")
        self.interface_closed_by_user = True
        
        # Chiudi solo la finestra, ma lascia i thread attivi
        if self.window:
            try:
                self.window.quit()  # Ferma il mainloop
                self.window.destroy()
            except:
                pass
        
        # Resetta i riferimenti alla finestra ma NON fermare i thread
        self.window = None
        self.ip_label = None
        self.status_label = None
        
        lb_log.info("Interfaccia desktop chiusa - thread rimangono attivi per riapertura")
    
    def getLocalIP(self):
        """Ottiene l'indirizzo IP locale principale"""
        try:
            # Crea una connessione temporanea per ottenere l'IP locale
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            try:
                # Metodo alternativo
                hostname = socket.gethostname()
                return socket.gethostbyname(hostname)
            except Exception:
                return "N/A"
    
    def getAllIPs(self):
        """Ottiene tutti gli indirizzi IP della macchina"""
        ips = []
        try:
            hostname = socket.gethostname()
            # Ottiene tutti gli indirizzi IP associati all'hostname
            for info in socket.getaddrinfo(hostname, None):
                ip = info[4][0]
                if ip not in ips and not ip.startswith('127.'):
                    ips.append(ip)
        except Exception:
            pass
        
        if not ips:
            ips.append(self.getLocalIP())
        
        return ips
    
    def setWindowTitle(self, title):
        """Imposta il titolo della finestra"""
        if self.window:
            self.window.after(0, lambda: self.window.title(title))
    
    def showMessage(self, message):
        """Mostra un messaggio nell'interfaccia"""
        if self.status_label:
            self.window.after(0, lambda: self.status_label.config(text=message))
    
    def isEnabled(self):
        """Verifica se l'interfaccia è abilitata"""
        return self.enabled and self.window is not None
    
    def isWindowVisible(self):
        """Verifica se la finestra è visibile"""
        try:
            if self.window is not None:
                return self.window.winfo_exists() and self.window.winfo_viewable()
            return False
        except tk.TclError:
            return False
    
    def getThreadsStatus(self):
        """Ottiene lo stato dei thread per debug"""
        interface_alive = self.thread_interface and self.thread_interface.is_alive()
        update_alive = self.thread_update_ip and self.thread_update_ip.is_alive()
        
        return {
            "interface_thread": {
                "exists": self.thread_interface is not None,
                "alive": interface_alive,
                "id": self.thread_interface.ident if self.thread_interface else None
            },
            "update_thread": {
                "exists": self.thread_update_ip is not None, 
                "alive": update_alive,
                "id": self.thread_update_ip.ident if self.thread_update_ip else None
            },
            "window_exists": self.window is not None,
            "interface_closed_by_user": self.interface_closed_by_user,
            "enabled": self.enabled
        }
    
    def closeInterface(self):
        """Chiude l'interfaccia desktop"""
        self.enabled = False
        
        # Chiude il thread di aggiornamento IP
        if self.thread_update_ip:
            closeThread(self.thread_update_ip)
            self.thread_update_ip = None
        
        # Chiude la finestra
        if self.window:
            try:
                self.window.quit()
                self.window.destroy()
            except:
                pass
            self.window = None
        
        # Chiude il thread dell'interfaccia
        if self.thread_interface:
            closeThread(self.thread_interface)
            self.thread_interface = None
        
        lb_log.info("Interfaccia desktop chiusa")

# ==============================================================