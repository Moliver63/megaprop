// Função para inicializar animações de cards (usando CSS)
function setupCardAnimations() {
    const cards = document.querySelectorAll('.card');
    if (!cards.length) return;

    cards.forEach(card => {
        card.classList.add('animated-card');

        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-5px)';
            card.style.boxShadow = '0 8px 15px rgba(0, 0, 0, 0.2)';
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = 'translateY(0)';
            card.style.boxShadow = '0 4px 10px rgba(0, 0, 0, 0.1)';
        });
    });
}

// Função para configurar o filtro de atividades
function setupActivityFilter() {
    const filterDropdown = document.getElementById('filterActivities');
    if (!filterDropdown) return;

    filterDropdown.addEventListener('change', function () {
        const selectedValue = this.value;
        const activityCards = document.querySelectorAll('.activity-card');

        activityCards.forEach(card => {
            const category = card.dataset.category;
            card.style.display = (selectedValue === 'all' || category === selectedValue) ? 'block' : 'none';
        });
    });
}

// Função para configurar o toggle do menu lateral
function setupSidebarToggle() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const content = document.getElementById('content');

    if (!sidebarToggle || !sidebar || !content) return;

    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
        content.classList.toggle('ms-lg-250');
    });
}

// Inicialização de Scripts
document.addEventListener('DOMContentLoaded', () => {
    setupCardAnimations();
    setupActivityFilter();
    setupSidebarToggle();
});