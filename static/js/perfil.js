// perfil.js
document.addEventListener('DOMContentLoaded', function() {
  const navItems = document.querySelectorAll('.nav-item');
  const profileSections = document.querySelectorAll('.profile-section');
  const filterButtons = document.querySelectorAll('.orders-filter .filter-btn');
  const editProfileBtn = document.querySelector('.btn-edit-profile');
  const profileForm = document.querySelector('.profile-form');
  const addAddressBtn = document.querySelector('.btn-add-address');
  const removeFavoriteBtns = document.querySelectorAll('.btn-remove-favorite');
  const addCartBtns = document.querySelectorAll('.btn-add-cart');

  // Dados do usuário (simulados)
  const userData = {
    name: 'João Silva',
    email: 'joao.silva@email.com',
    phone: '(11) 99999-9999',
    cpf: '123.456.789-00',
    birthdate: '1990-05-15',
    memberSince: 'Jan 2024',
    addresses: [
      {
        id: 1,
        type: 'Casa',
        default: true,
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
        default: false,
        street: 'Av. Paulista',
        number: '1000',
        complement: 'Sala 10',
        neighborhood: 'Bela Vista',
        city: 'São Paulo',
        state: 'SP',
        zipcode: '01310-100'
      }
    ],
    favorites: [
      { id: 1, name: 'MegaBurger', price: 32.90, image: '/static/img/cardapio/megaburger.jpg' },
      { id: 2, name: 'MixFrango', price: 28.90, image: '/static/img/cardapio/mixfrango.jpg' }
    ],
    orders: [
      {
        id: 'PED-2024-001',
        date: '15 Jan 2024 • 19:30',
        status: 'delivered',
        items: ['1x MegaBurger', '2x Fritas Especiais', '1x Refrigerante'],
        total: 68.70
      },
      {
        id: 'PED-2024-002',
        date: '20 Jan 2024 • 12:15',
        status: 'preparing',
        items: ['1x MixFrango', '1x Onion Rings', '1x Suco Natural'],
        total: 52.80
      }
    ]
  };

  // Navegação entre seções
  navItems.forEach(item => {
    item.addEventListener('click', function(e) {
      e.preventDefault();
      
      const targetId = this.getAttribute('href').substring(1);
      
      // Atualizar navegação ativa
      navItems.forEach(nav => nav.classList.remove('active'));
      this.classList.add('active');
      
      // Mostrar seção correspondente
      profileSections.forEach(section => {
        section.classList.remove('active');
        if (section.id === targetId) {
          section.classList.add('active');
        }
      });
    });
  });

  // Filtros de pedidos
  filterButtons.forEach(button => {
    button.addEventListener('click', function() {
      filterButtons.forEach(btn => btn.classList.remove('active'));
      this.classList.add('active');
      
      // Em uma aplicação real, aqui filtraria os pedidos
      filterOrders(this.textContent);
    });
  });

  // Editar perfil
  editProfileBtn.addEventListener('click', function() {
    const inputs = profileForm.querySelectorAll('input');
    const isEditing = profileForm.querySelector('button[type="submit"]');
    
    if (!isEditing) {
      // Entrar no modo de edição
      inputs.forEach(input => {
        if (input.id !== 'cpf') { // CPF não é editável
          input.removeAttribute('readonly');
        }
      });
      
      // Adicionar botões de ação
      const formActions = document.createElement('div');
      formActions.className = 'form-actions';
      formActions.innerHTML = `
        <button type="button" class="btn-secondary">Cancelar</button>
        <button type="submit" class="btn-primary">Salvar Alterações</button>
      `;
      
      profileForm.appendChild(formActions);
      
      // Evento de cancelar
      formActions.querySelector('.btn-secondary').addEventListener('click', cancelEdit);
      
      this.textContent = 'Saindo da Edição';
    } else {
      // Sair do modo de edição
      cancelEdit();
    }
  });

  // Formatar telefone automaticamente
  const phoneInput = document.getElementById('phone');
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

  // Adicionar novo endereço
  addAddressBtn.addEventListener('click', function() {
    showAddressModal();
  });

  // Remover favorito
  removeFavoriteBtns.forEach(button => {
    button.addEventListener('click', function() {
      const favoriteItem = this.closest('.favorite-item');
      const itemName = favoriteItem.querySelector('h3').textContent;
      
      removeFavorite(itemName, favoriteItem);
    });
  });

  // Adicionar ao carrinho a partir dos favoritos
  addCartBtns.forEach(button => {
    button.addEventListener('click', function() {
      const favoriteItem = this.closest('.favorite-item');
      const itemName = favoriteItem.querySelector('h3').textContent;
      const itemPrice = parseFloat(favoriteItem.querySelector('.price').textContent.replace('R$ ', '').replace(',', '.'));
      
      addToCartFromFavorites(itemName, itemPrice);
    });
  });

  // Funções auxiliares
  function cancelEdit() {
    const inputs = profileForm.querySelectorAll('input');
    inputs.forEach(input => {
      if (input.id !== 'cpf') {
        input.setAttribute('readonly', 'true');
      }
    });
    
    const formActions = profileForm.querySelector('.form-actions');
    if (formActions) {
      formActions.remove();
    }
    
    editProfileBtn.textContent = 'Editar Perfil';
    
    // Restaurar valores originais
    restoreOriginalValues();
  }

  function restoreOriginalValues() {
    document.getElementById('full-name').value = userData.name;
    document.getElementById('email').value = userData.email;
    document.getElementById('phone').value = userData.phone;
    document.getElementById('birthdate').value = userData.birthdate;
  }

  function filterOrders(filter) {
    const orders = document.querySelectorAll('.order-card');
    
    orders.forEach(order => {
      const orderDate = order.querySelector('.order-date').textContent;
      let shouldShow = true;
      
      switch(filter) {
        case 'Este mês':
          shouldShow = orderDate.includes('Jan 2024');
          break;
        case 'Últimos 3 meses':
          shouldShow = true; // Simulação
          break;
        case '2024':
          shouldShow = orderDate.includes('2024');
          break;
        default:
          shouldShow = true;
      }
      
      order.style.display = shouldShow ? 'block' : 'none';
    });
  }

  function showAddressModal() {
    // Em uma aplicação real, isso abriria um modal
    alert('Funcionalidade de adicionar endereço será implementada em breve!');
  }

  function removeFavorite(itemName, element) {
    if (confirm(`Remover ${itemName} dos favoritos?`)) {
      element.style.animation = 'fadeOut 0.3s ease';
      
      setTimeout(() => {
        element.remove();
        showMessage(`${itemName} removido dos favoritos.`, 'success');
        
        // Atualizar dados
        userData.favorites = userData.favorites.filter(fav => fav.name !== itemName);
      }, 300);
    }
  }

  function addToCartFromFavorites(itemName, itemPrice) {
    // Simular adição ao carrinho
    showMessage(`${itemName} adicionado ao carrinho!`, 'success');
    
    // Em uma aplicação real, isso faria uma requisição para a API do carrinho
    setTimeout(() => {
      window.location.href = '/carrinho';
    }, 1000);
  }

  function showMessage(message, type) {
    // Remover mensagem anterior
    const existingMessage = document.querySelector('.profile-message');
    if (existingMessage) {
      existingMessage.remove();
    }
    
    // Criar nova mensagem
    const messageDiv = document.createElement('div');
    messageDiv.className = `profile-message ${type}`;
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

  // Animação CSS
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn {
      from { transform: translateX(100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
      from { transform: translateX(0); opacity: 1; }
      to { transform: translateX(100%); opacity: 0; }
    }
    
    @keyframes fadeOut {
      from { opacity: 1; transform: scale(1); }
      to { opacity: 0; transform: scale(0.8); }
    }
  `;
  document.head.appendChild(style);
});