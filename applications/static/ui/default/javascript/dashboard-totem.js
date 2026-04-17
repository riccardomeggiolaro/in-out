// ===== TOTEM - Weigher Selection =====

window.addEventListener('load', () => {
    setTimeout(() => {
        document.querySelector('.loading').style.display = 'none';
        document.getElementById('weigherSelection').style.display = 'flex';
    }, 300);
});

document.addEventListener('DOMContentLoaded', () => {
    fetch('/api/config-weigher/configuration')
    .then(res => res.json())
    .then(res => {
        const weigherOptions = [];
        for (let instance in res["weighers"]) {
            for (let weigher in res["weighers"][instance]["nodes"]) {
                weigherOptions.push({
                    path: `?instance_name=${instance}&weigher_name=${weigher}`,
                    label: weigher
                });
            }
        }

        const weigherList = document.getElementById('weigherList');
        weigherList.innerHTML = '';
        weigherOptions.forEach(opt => {
            const btn = document.createElement('button');
            btn.className = 'weigher-option';
            btn.textContent = opt.label;
            btn.addEventListener('click', () => {
                localStorage.setItem('currentWeigherPath', opt.path);
                window.location.href = 'totem.html';
            });
            weigherList.appendChild(btn);
        });
    });
});

// --- Fullscreen control (triple click top-left + F11, auto re-enter on accidental exit) ---
(function () {
    let _clicks = 0;
    let _clickTimer = null;
    let _intentionalExit = false;

    function enterFs() { document.documentElement.requestFullscreen().catch(() => {}); }
    function exitFs() {
        _intentionalExit = true;
        document.exitFullscreen().catch(() => { _intentionalExit = false; });
    }

    document.addEventListener('fullscreenchange', () => {
        if (!document.fullscreenElement) {
            if (_intentionalExit) {
                _intentionalExit = false;
            } else {
                setTimeout(enterFs, 0);
            }
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'F11') {
            e.preventDefault();
            document.fullscreenElement ? exitFs() : enterFs();
        }
    });

    const zone = document.createElement('div');
    zone.style.cssText = 'position:fixed;top:0;left:0;width:60px;height:60px;z-index:9999;cursor:default;-webkit-tap-highlight-color:transparent;';

    function handleTap() {
        _clicks++;
        clearTimeout(_clickTimer);
        if (_clicks >= 3) {
            _clicks = 0;
            document.fullscreenElement ? exitFs() : enterFs();
        } else {
            _clickTimer = setTimeout(() => { _clicks = 0; }, 800);
        }
    }

    zone.addEventListener('click', handleTap);
    document.body.appendChild(zone);
})();