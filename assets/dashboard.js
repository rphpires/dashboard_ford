// Função para ajustar os gráficos dinamicamente baseado no tamanho da viewport
document.addEventListener('DOMContentLoaded', function() {
    // Para cada container de gráfico, adicione uma classe específica para facilitar o styling
    const graphContainers = {
        'utilization-graph': 'utilization-graph',
        'availability-graph': 'availability-graph',
        'programs-graph': 'programs-graph',
        'other-skills-graph': 'other-skills-graph',
        'internal-users-graph': 'internal-users-graph',
        'external-sales-graph': 'external-sales-graph',
        'monthly-tracks-graph': 'monthly-tracks-graph',
        'monthly-areas-graph': 'monthly-areas-graph',
        'ytd-customers-graph': 'ytd-customers-graph'
    };
    
    // Adicionar classes aos containers
    Object.entries(graphContainers).forEach(([id, className]) => {
        const container = document.getElementById(id);
        if (container && container.parentElement) {
            container.parentElement.classList.add(className);
        }
    });
    
    // Função para ajustar layout baseado no tamanho da tela
    function adjustLayout() {
        const windowHeight = window.innerHeight;
        const windowWidth = window.innerWidth;
        
        // Adicionar classe específica para o tamanho da tela atual
        document.body.classList.remove('screen-large', 'screen-medium', 'screen-small');
        
        if (windowWidth > 1200 && windowHeight > 900) {
            document.body.classList.add('screen-large');
        } else if (windowWidth > 992 || windowHeight > 700) {
            document.body.classList.add('screen-medium');
        } else {
            document.body.classList.add('screen-small');
        }
    }
    
    // Executar ao carregar
    adjustLayout();
    
    // Evento de redimensionamento
    window.addEventListener('resize', adjustLayout);
});