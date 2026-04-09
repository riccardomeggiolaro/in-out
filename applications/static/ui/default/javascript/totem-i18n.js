// ===== TOTEM I18N - Language dictionaries =====

const totemTranslations = {
    it: {
        // Page titles
        plate_title: 'Targa',
        card_title: 'Tessera',
        subject_title: 'Ragione Sociale',
        customer: 'Cliente',
        supplier: 'Fornitore',
        vector_title: 'Vettore',
        driver_title: 'Autista',
        material_title: 'Materiale',
        summary_title: 'Riepilogo',

        // Buttons
        cancel: 'Cancella',
        undo: 'Annulla',
        confirm: 'Conferma',
        next: 'Avanti',
        back: 'Indietro',
        more: 'Altro',
        weigh: 'Pesa',
        entry: 'Entrata',
        exit: 'Uscita',
        reconnect: 'Riconnetti',

        // Messages
        reconnecting: 'Riconnessione in corso...',
        weighing_success: 'Pesata completata',
        weighing_error: 'Pesata non riuscita',
        weighing_generic_error: 'Errore durante la pesatura',
        create_new: 'Crea',
        max_threshold_exceeded: 'Soglia massima di <strong>{value} kg</strong> superata, procedere con la pesatura?',
        auto_plate_confirm: 'Lettura automatica della targa <strong>\'{plate}\'</strong>. <br> Effettuare la pesatura?',

        // RFID
        rfid_read_card: 'Leggere tessera',
        card_instruction: 'Avvicina la tessera al lettore',
        skip: 'Salta',

        // Anagrafic labels
        label_vehicle: 'Veicolo',
        label_subject: 'Soggetto',
        label_vector: 'Vettore',
        label_driver: 'Autista',
        label_material: 'Materiale',
        net_weight: 'Netto in tempo reale',
    },
    en: {
        // Page titles
        plate_title: 'License Plate',
        card_title: 'Card',
        subject_title: 'Company Name',
        customer: 'Customer',
        supplier: 'Supplier',
        vector_title: 'Carrier',
        driver_title: 'Driver',
        material_title: 'Material',
        summary_title: 'Summary',

        // Buttons
        cancel: 'Cancel',
        undo: 'Undo',
        confirm: 'Confirm',
        next: 'Next',
        back: 'Back',
        more: 'More',
        weigh: 'Weigh',
        entry: 'Weight 1',
        exit: 'Weight 2',
        reconnect: 'Reconnect',

        // Messages
        reconnecting: 'Reconnecting...',
        weighing_success: 'Weighing completed',
        weighing_error: 'Weighing failed',
        weighing_generic_error: 'Error during weighing',
        create_new: 'Create',
        max_threshold_exceeded: 'Maximum threshold of <strong>{value} kg</strong> exceeded, proceed with weighing?',
        auto_plate_confirm: 'Automatic plate reading <strong>\'{plate}\'</strong>. <br> Proceed with weighing?',

        // RFID
        rfid_read_card: 'Read card',
        card_instruction: 'Hold card near reader',
        skip: 'Skip',

        // Anagrafic labels
        label_vehicle: 'Vehicle',
        label_subject: 'Subject',
        label_vector: 'Carrier',
        label_driver: 'Driver',
        label_material: 'Material',
        net_weight: 'Real-time Net',
    }
};

// Current language
let currentLang = 'it';

// Get cookie value
function _getCookie(name) {
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? match[2] : null;
}

// Set cookie (expires in 1 year)
function _setCookie(name, value) {
    document.cookie = name + '=' + value + ';path=/;max-age=31536000;SameSite=Lax';
}

// Initialize language from cookie
function initLang() {
    const saved = _getCookie('totem_lang');
    currentLang = (saved === 'en') ? 'en' : 'it';
}

// Translate key
function t(key) {
    return (totemTranslations[currentLang] && totemTranslations[currentLang][key]) || key;
}

// Track current view name for re-rendering on lang switch
let _currentViewName = null;

// Switch language
function switchLang(lang) {
    if (lang !== 'it' && lang !== 'en') return;
    currentLang = lang;
    _setCookie('totem_lang', lang);
    _updateLangSwitcherUI();
    // Re-render current view
    if (_currentViewName && typeof showView === 'function') {
        showView(_currentViewName);
    }
    // Update static popup texts
    _updatePopupTexts();
}

function _updateLangSwitcherUI() {
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.lang === currentLang);
    });
}

function _updatePopupTexts() {
    const reconnPopup = document.querySelector('#reconnectionPopup .popup-content p');
    if (reconnPopup) reconnPopup.textContent = t('reconnecting');
    const reconnBtn = document.getElementById('reconnectionButton');
    if (reconnBtn) reconnBtn.textContent = t('reconnect');
    const confirmBack = document.querySelector('#confirmPopup .close-button');
    if (confirmBack) confirmBack.textContent = t('back');
    const confirmBtn = document.querySelector('#confirmPopup .btn-primary');
    if (confirmBtn) confirmBtn.textContent = t('confirm');
}

// Initialize on load
initLang();
