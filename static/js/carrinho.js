// static/js/carrinho.js

// Cupom de desconto
document.addEventListener('DOMContentLoaded', function() {
    const cupomInput = document.getElementById('cupom-input');
    const aplicarCupomBtn = document.getElementById('aplicar-cupom');
    const cupomAplicadoDiv = document.getElementById('cupom-aplicado');
    const removerCupomBtn = document.getElementById('remover-cupom');
    
    if (aplicarCupomBtn) {
        aplicarCupomBtn.addEventListener('click', function() {
            const cupom = cupomInput.value.trim();
            
            if (cupom === 'SABOR10') {
                // Aplicar 10% de desconto
                aplicarDesconto(0.1, 'Cupom SABOR10 - 10% off');
            } else if (cupom === 'PRIMEIRACOMPRA') {
                // Aplicar 15% de desconto
                aplicarDesconto(0.15, 'Cupom PRIMEIRACOMPRA - 15% off');
            } else if (cupom) {
                alert('Cupom inválido!');
            }
        });
    }
    
    if (removerCupomBtn) {
        removerCupomBtn.addEventListener('click', function() {
            removerDesconto();
        });
    }
    
    // Opções de entrega
    const deliveryOptions = document.querySelectorAll('input[name="delivery"]');
    deliveryOptions.forEach(option => {
        option.addEventListener('change', function() {
            atualizarTaxaEntrega(this.value);
        });
    });
});

function aplicarDesconto(percentual, cupomTexto) {
    // Aqui você implementaria a lógica de desconto
    // Por enquanto vamos apenas mostrar visualmente
    const cupomAplicado = document.getElementById('cupom-aplicado');
    const cupomText = document.getElementById('cupom-texto');
    
    cupomText.textContent = cupomTexto;
    cupomAplicado.classList.remove('hidden');
    document.querySelector('.coupon-input').classList.add('hidden');
    
    // Em uma implementação real, você faria uma requisição AJAX
    // para atualizar os valores no servidor
    alert('Cupom aplicado! Atualizando valores...');
    location.reload(); // Recarregar para ver mudanças
}

function removerDesconto() {
    const cupomAplicado = document.getElementById('cupom-aplicado');
    const couponInput = document.querySelector('.coupon-input');
    
    cupomAplicado.classList.add('hidden');
    couponInput.classList.remove('hidden');
    
    // Recarregar para remover desconto
    location.reload();
}

function atualizarTaxaEntrega(tipo) {
    // Em uma implementação real, isso seria feito via AJAX
    if (tipo === 'pickup') {
        alert('Alterado para retirada no local - Sem taxa de entrega');
    } else {
        alert('Alterado para delivery - Taxa de entrega aplicada');
    }
    location.reload();
}