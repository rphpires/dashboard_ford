// Função para ajustar os gráficos dinamicamente
document.addEventListener('DOMContentLoaded', function() {
    // Forçar redesenho de todos os gráficos após o carregamento completo
    setTimeout(function() {
        // Obter todas as instâncias de gráficos Plotly
        var allPlots = document.querySelectorAll('.js-plotly-plot');
        
        // Para cada gráfico, forçar o redesenho
        allPlots.forEach(function(plot) {
            if (window.Plotly && plot && plot.id) {
                var plotElement = document.getElementById(plot.id);
                if (plotElement && plotElement._fullLayout) {
                    try {
                        window.Plotly.relayout(plot.id, {
                            'autosize': true
                        });
                    } catch (e) {
                        console.error('Error resizing plot:', e);
                    }
                }
            }
        });
        
        // Forçar redesenho da tela
        window.dispatchEvent(new Event('resize'));
    }, 100);  // Pequeno atraso para garantir que os elementos estejam renderizados
    
    // Também redesenhar ao redimensionar a janela
    window.addEventListener('resize', function() {
        // Forçar redesenho após redimensionamento
        setTimeout(function() {
            var allPlots = document.querySelectorAll('.js-plotly-plot');
            allPlots.forEach(function(plot) {
                if (window.Plotly && plot && plot.id) {
                    try {
                        window.Plotly.relayout(plot.id, {
                            'autosize': true
                        });
                    } catch (e) {
                        console.error('Error resizing plot:', e);
                    }
                }
            });
        }, 100);
    });
});