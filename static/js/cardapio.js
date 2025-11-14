// Funcionalidades básicas do cardápio
document.addEventListener('DOMContentLoaded', function() {
  // Elementos do DOM
  const filterButtons = document.querySelectorAll('.filter-btn');
  const menuItems = document.querySelectorAll('.menu-item');
  const searchInput = document.getElementById('search-input');
  const sortSelect = document.getElementById('sort-select');
  const addCartButtons = document.querySelectorAll('.btn-add-cart');
  const customizeButtons = document.querySelectorAll('.btn-customize');
  const modal = document.getElementById('customize-modal');
  const cartCount = document.querySelector('.cart-count');
  const cartTotal = document.querySelector('.cart-total');

  // Estado do carrinho
  let cart = [];
  let cartItemCount = 0;

  // Filtragem por categoria
  filterButtons.forEach(button => {
    button.addEventListener('click', function() {
      const category = this.dataset.category;
      
      // Atualizar botão ativo
      filterButtons.forEach(btn => btn.classList.remove('active'));
      this.classList.add('active');
      
      // Filtrar itens
      menuItems.forEach(item => {
        if (category === 'all' || item.dataset.category === category) {
          item.style.display = 'block';
        } else {
          item.style.display = 'none';
        }
      });
    });
  });

  // Busca em tempo real
  searchInput.addEventListener('input', function() {
    const searchTerm = this.value.toLowerCase();
    
    menuItems.forEach(item => {
      const title = item.querySelector('.item-title').textContent.toLowerCase();
      const description = item.querySelector('.item-description').textContent.toLowerCase();
      
      if (title.includes(searchTerm) || description.includes(searchTerm)) {
        item.style.display = 'block';
      } else {
        item.style.display = 'none';
      }
    });
  });

  // Ordenação
  sortSelect.addEventListener('change', function() {
    const sortBy = this.value;
    const container = document.querySelector('.menu-grid');
    const items = Array.from(container.querySelectorAll('.menu-item'));
    
    items.sort((a, b) => {
      switch(sortBy) {
        case 'price-asc':
          return parseFloat(a.dataset.price) - parseFloat(b.dataset.price);
        case 'price-desc':
          return parseFloat(b.dataset.price) - parseFloat(a.dataset.price);
        case 'name':
          return a.querySelector('.item-title').textContent.localeCompare(
            b.querySelector('.item-title').textContent
          );
        default:
          return 0;
      }
    });
    
    // Reordenar itens no DOM
    items.forEach(item => container.appendChild(item));
  });

  // Adicionar ao carrinho
  addCartButtons.forEach(button => {
    button.addEventListener('click', function() {
      const itemId = this.dataset.item;
      const itemElement = this.closest('.menu-item');
      const itemName = itemElement.querySelector('.item-title').textContent;
      const itemPrice = parseFloat(itemElement.dataset.price);
      
      // Adicionar ao carrinho
      cart.push({
        id: itemId,
        name: itemName,
        price: itemPrice,
        quantity: 1
      });
      
      // Atualizar contador
      cartItemCount++;
      cartCount.textContent = cartItemCount;
      cartTotal.textContent = cartItemCount;
      
      // Feedback visual
      const originalText = this.textContent;
      this.textContent = '✓ Adicionado!';
      this.style.backgroundColor = '#27ae60';
      
      setTimeout(() => {
        this.textContent = originalText;
        this.style.backgroundColor = '';
      }, 2000);
      
      console.log('Carrinho:', cart);
    });
  });

  // Personalização (modal básico)
  customizeButtons.forEach(button => {
    button.addEventListener('click', function() {
      const itemId = this.dataset.item;
      openCustomizeModal(itemId);
    });
  });

  // Fechar modal
  modal.querySelector('.modal-close').addEventListener('click', closeModal);
  modal.querySelector('.btn-cancel').addEventListener('click', closeModal);

  function openCustomizeModal(itemId) {
    // Aqui você implementaria a lógica de personalização
    modal.querySelector('.modal-body').innerHTML = `
      <div class="customize-options">
        <h4>Personalize seu pedido</h4>
        <p>Em desenvolvimento...</p>
      </div>
    `;
    modal.classList.add('show');
  }

  function closeModal() {
    modal.classList.remove('show');
  }

  // Fechar modal ao clicar fora
  modal.addEventListener('click', function(e) {
    if (e.target === modal) {
      closeModal();
    }
  });
});