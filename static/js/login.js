// login.js
document.addEventListener('DOMContentLoaded', function() {
  const tabButtons = document.querySelectorAll('.tab-btn');
  const authForms = document.querySelectorAll('.auth-form');
  const togglePasswordButtons = document.querySelectorAll('.toggle-password');
  const loginForm = document.getElementById('login-form');
  const registerForm = document.getElementById('register-form');

  // Alternar entre login e cadastro
  tabButtons.forEach(button => {
    button.addEventListener('click', function() {
      const targetTab = this.dataset.tab;
      
      // Atualizar botões ativos
      tabButtons.forEach(btn => btn.classList.remove('active'));
      this.classList.add('active');
      
      // Mostrar formulário correto
      authForms.forEach(form => {
        form.classList.remove('active');
        if (form.id === `${targetTab}-form`) {
          form.classList.add('active');
        }
      });
    });
  });

  // Mostrar/ocultar senha
  togglePasswordButtons.forEach(button => {
    button.addEventListener('click', function() {
      const input = this.parentElement.querySelector('input');
      const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
      input.setAttribute('type', type);
      this.textContent = type === 'password' ? '👁️' : '👁️‍🗨️';
    });
  });

  // Validação do formulário de login
  loginForm.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    if (!validateEmail(email)) {
      showError('Por favor, insira um e-mail válido.');
      return;
    }
    
    if (password.length < 6) {
      showError('A senha deve ter pelo menos 6 caracteres.');
      return;
    }
    
    // Simular login
    simulateLogin(email, password);
  });

  // Validação do formulário de cadastro
  registerForm.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const name = document.getElementById('register-name').value;
    const phone = document.getElementById('register-phone').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('register-confirm-password').value;
    const acceptTerms = document.getElementById('accept-terms').checked;
    
    if (name.length < 2) {
      showError('Por favor, insira seu nome completo.');
      return;
    }
    
    if (!validatePhone(phone)) {
      showError('Por favor, insira um telefone válido.');
      return;
    }
    
    if (!validateEmail(email)) {
      showError('Por favor, insira um e-mail válido.');
      return;
    }
    
    if (password.length < 8) {
      showError('A senha deve ter pelo menos 8 caracteres.');
      return;
    }
    
    if (password !== confirmPassword) {
      showError('As senhas não coincidem.');
      return;
    }
    
    if (!acceptTerms) {
      showError('Você deve aceitar os termos de uso.');
      return;
    }
    
    // Simular cadastro
    simulateRegister({ name, phone, email, password });
  });

  // Formatação automática do telefone
  const phoneInput = document.getElementById('register-phone');
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

  // Funções auxiliares
  function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  }

  function validatePhone(phone) {
    const re = /^\(\d{2}\) \d{4,5}-\d{4}$/;
    return re.test(phone);
  }

  function showError(message) {
    // Remover erro anterior
    const existingError = document.querySelector('.error-message');
    if (existingError) {
      existingError.remove();
    }
    
    // Criar nova mensagem de erro
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.style.cssText = `
      background: #fee;
      color: #c33;
      padding: 10px;
      border-radius: 5px;
      margin-bottom: 15px;
      border: 1px solid #fcc;
    `;
    errorDiv.textContent = message;
    
    const activeForm = document.querySelector('.auth-form.active');
    activeForm.insertBefore(errorDiv, activeForm.firstChild);
    
    // Auto-remover após 5 segundos
    setTimeout(() => {
      errorDiv.remove();
    }, 5000);
  }

  function simulateLogin(email, password) {
    const btn = loginForm.querySelector('.btn-primary');
    const originalText = btn.textContent;
    
    btn.textContent = 'Entrando...';
    btn.disabled = true;
    
    // Simular requisição
    setTimeout(() => {
      btn.textContent = originalText;
      btn.disabled = false;
      
      // Em uma aplicação real, aqui seria o redirecionamento
      alert('Login realizado com sucesso! Redirecionando...');
      window.location.href = '/cardapio.html';
    }, 2000);
  }

  function simulateRegister(userData) {
    const btn = registerForm.querySelector('.btn-primary');
    const originalText = btn.textContent;
    
    btn.textContent = 'Criando conta...';
    btn.disabled = true;
    
    // Simular requisição
    setTimeout(() => {
      btn.textContent = originalText;
      btn.disabled = false;
      
      alert('Conta criada com sucesso! Faça login para continuar.');
      
      // Mudar para aba de login
      document.querySelector('[data-tab="login"]').click();
      document.getElementById('login-email').value = userData.email;
    }, 2000);
  }
});