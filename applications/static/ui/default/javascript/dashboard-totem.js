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
                window.location.href = 'totem-plate.html';
            });
            weigherList.appendChild(btn);
        });
    });
});
