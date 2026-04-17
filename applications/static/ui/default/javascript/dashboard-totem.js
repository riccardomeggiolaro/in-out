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

// --- Fullscreen control (triple click top-left) ---
(function () {
    let _f11Clicks = 0;
    let _f11Timer = null;

    const zone = document.createElement('div');
    zone.style.cssText = 'position:fixed;top:0;left:0;width:60px;height:60px;z-index:9999;cursor:default;-webkit-tap-highlight-color:transparent;';

    zone.addEventListener('click', () => {
        _f11Clicks++;
        clearTimeout(_f11Timer);

        if (_f11Clicks >= 3) {
            _f11Clicks = 0;
            fetch('/api/generic/show-desktop', { method: 'POST' }).catch(() => {});
        } else {
            _f11Timer = setTimeout(() => { _f11Clicks = 0; }, 800);
        }
    });

    document.body.appendChild(zone);

})();