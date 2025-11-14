// checkout.js
document.addEventListener('DOMContentLoaded', function() {
  const deliveryTypeRadios = document.querySelectorAll('input[name="delivery-type"]');
  const addressRadios = document.querySelectorAll('input[name="address"]');
  const newAddressBtn = document.querySelector('.btn-new-address');
  const newAddressForm = document.querySelector('.new-address-form');
  const continueBtn = document.querySelector('.btn-continue');
  const backBtn = document.querySelector('.btn-back');
  const zipcodeInput = document.getElementById('zipcode');

  // Dados do usuário (simulados)
  const userData = {
    addresses: [
      {
        id: 1,
        type: 'Casa',
        street: 'Rua das Flores',
        number: '123',
        complement: 'Apt 45',
        neighborhood: 'Jardim Paulista',
        city: 'São Paulo',
        state: 'SP',
        zipcode: '01415-001'
      },
      {
        id: 2,
        type: 'Trabalho',
        street: 'Av. Paulista',
        number: '1000',
        complement: 'Sala 10',
        neighborhood: 'Bela Vista',
        city: 'São Paulo',
        state: 'SP',
        zipcode: '01310-100'
      }
    ]
  };

  // Alternar tipo de entrega
  deliveryTypeRadios.forEach(radio => {
    radio.addEventListener('change', function() {
      if (this.id === 'delivery-home') {
        document.getElementById('address-section').style.display = 'block';
      } else {
        document.getElementById('address-section').style.display = 'none';
      }
      
      updateOrderSummary();
    });
  });

  // Alternar endereço
  addressRadios.forEach(radio => {
    radio.addEventListener('change', function() {
      updateActiveAddress();
      updateOrderSummary();
    });
  });

  // Novo endereço
  newAddressBtn.addEventListener('click', function() {
    newAddressForm.classList.toggle('hidden');
    this.textContent = newAddressForm.classList.contains('hidden') 
      ? '+ Novo Endereço' 
      : 'Cancelar';
  });

  // Buscar CEP
  zipcodeInput.addEventListener('input', function(e) {
    let value = e.target.value.replace(/\D/g, '');
    
    if (value.length > 8) {
      value = value.substring(0, 8);
    }
    
    if (value.length === 8) {
      value = value.replace(/^(\d{5})(\d{3})/, '$1-$2');
      searchCEP(value);
    }
    
    e.target.value = value;
  });

  // Continuar para pagamento
  continueBtn.addEventListener('click', function() {
    if (validateForm()) {
      // Simular processamento
      this.textContent = 'Processando...';
      this.disabled = true;
      
      setTimeout(() => {
        window.location.href = '/pagamento';
      }, 1000);
    }
  });

  // Voltar ao carrinho
  backBtn.addEventListener('click', function() {
    window.location.href = '/carrinho';
  });

  // Funções auxiliares
  function updateActiveAddress() {
    document.querySelectorAll('.address-option').forEach(option => {
      option.classList.remove('active');
    });
    
    const selectedAddress = document.querySelector('input[name="address"]:checked');
    if (selectedAddress) {
      selectedAddress.closest('.address-option').classList.add('active');
    }
  }

  function updateOrderSummary() {
    const deliveryType = document.querySelector('input[name="delivery-type"]:checked').value;
    const deliveryDetail = document.querySelector('.delivery-detail:first-child span:last-child');
    
    if (deliveryType === 'delivery-home') {
      deliveryDetail.textContent = '30-45 minutos';
      
      const selectedAddress = document.querySelector('input[name="address"]:checked');
      if (selectedAddress) {
        const addressLabel = selectedAddress.closest('label');
        const addressText = addressLabel.querySelector('span:nth-child(2)').textContent;
        document.querySelector('.delivery-detail:last-child span:last-child').textContent = addressText;
      }
    } else {
      deliveryDetail.textContent = '15-25 minutos';
      document.querySelector('.delivery-detail:last-child span:last-child').textContent = 'Retirar no restaurante';
    }
  }

  function searchCEP(cep) {
    // Simular busca de CEP
    const loadingDiv = document.createElement('div');
    loadingDiv.textContent = 'Buscando...';
    loadingDiv.style.cssText = 'color: var(--primary-color); font-size: 0.9rem; margin-top: 5px;';
    zipcodeInput.parentElement.appendChild(loadingDiv);
    
    setTimeout(() => {
      loadingDiv.remove();
      
      // Dados simulados
      const mockAddress = {
        street: 'Rua das Flores',
        neighborhood: 'Jardim Paulista',
        city: 'São Paulo',
        state: 'SP'
      };
      
      document.getElementById('street').value = mockAddress.street;
      document.getElementById('neighborhood').value = mockAddress.neighborhood;
      document.getElementById('city').value = mockAddress.city;
      document.getElementById('state').value = mockAddress.state;
      
      showMessage('Endereço preenchido automaticamente!', 'success');
    }, 1500);
  }

  function validateForm() {
    const deliveryType = document.querySelector('input[name="delivery-type"]:checked').value;
    
    if (deliveryType === 'delivery-home') {
      const selectedAddress = document.querySelector('input[name="address"]:checked');
      const newAddressVisible = !newAddressForm.classList.contains('hidden');
      
      if (!selectedAddress && !newAddressVisible) {
        showMessage('Por favor, selecione ou adicione um endereço de entrega.', 'error');
        return false;
      }
      
      if (newAddressVisible) {
        const requiredFields = ['zipcode', 'street', 'number', 'neighborhood', 'city', 'state'];
        for (let field of requiredFields) {
          const input = document.getElementById(field);
          if (!input.value.trim()) {
            showMessage(`Por favor, preencha o campo ${input.previousElementSibling.textContent}.`, 'error');
            input.focus();
            return false;
          }
        }
      }
    }
    
    const phone = document.getElementById('customer-phone').value;
    if (!validatePhone(phone)) {
      showMessage('Por favor, insira um telefone válido.', 'error');
      return false;
    }
    
    return true;
  }

  function validatePhone(phone) {
    const re = /^\(\d{2}\) \d{4,5}-\d{4}$/;
    return re.test(phone);
  }

  function showMessage(message, type) {
    // Remover mensagem anterior
    const existingMessage = document.querySelector('.checkout-message');
    if (existingMessage) {
      existingMessage.remove();
    }
    
    // Criar nova mensagem
    const messageDiv = document.createElement('div');
    messageDiv.className = `checkout-message ${type}`;
    messageDiv.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 15px 20px;
      border-radius: 8px;
      color: white;
      font-weight: 600;
      z-index: 1000;
      animation: slideIn 0.3s ease;
    `;
    
    // Cores baseadas no tipo
    const colors = {
      success: '#27ae60',
      error: '#e74c3c',
      info: '#3498db'
    };
    
    messageDiv.style.backgroundColor = colors[type] || colors.info;
    messageDiv.textContent = message;
    
    document.body.appendChild(messageDiv);
    
    // Auto-remover após 3 segundos
    setTimeout(() => {
      messageDiv.style.animation = 'slideOut 0.3s ease';
      setTimeout(() => messageDiv.remove(), 300);
    }, 3000);
  }

  // Formatação automática do telefone
  const phoneInput = document.getElementById('customer-phone');
  phoneInput.addEventListener('input', function(e) {
    let value = e.target.value.replace(/\D/g, '');
    
    if (value.length > 11) {
      value = value.substring(0, 11);
    }
    
    if (value.length > 10) {
      value = value.replace(/^(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
    } else if (value.length > 6) {
      value = value.replace(/^(\d{2})(\d{4})(\d{0,4})/, '($1) $2-$3');
    } else if (value.length > 2) {
      value = value.replace(/^(\d{2})(\d{0,5})/, '($1) $2');
    } else if (value.length > 0) {
      value = value.replace(/^(\d*)/, '($1');
    }
    
    e.target.value = value;
  });

  // Inicializar
  updateActiveAddress();
  updateOrderSummary();
});