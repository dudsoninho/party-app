function triggerButterflyEffect() {
    const container = document.getElementById('butterfly-container');
    if (!container) return;
    const butterflyCount = 12;

    for (let i = 0; i < butterflyCount; i++) {
        const butterfly = document.createElement('div');
        butterfly.className = 'butterfly';
        butterfly.innerText = '🦋';

        const startX = Math.random() * window.innerWidth;
        butterfly.style.left = startX + 'px';
        butterfly.style.bottom = '10px';

        const dx = (Math.random() - 0.5) * 300 + 'px';
        const dy = -(Math.random() * 300 + 200) + 'px';
        
        butterfly.style.setProperty('--dx', dx);
        butterfly.style.setProperty('--dy', dy);

        container.appendChild(butterfly);

        setTimeout(() => {
            butterfly.remove();
        }, 2500);
    }
}
