let pizzas = [];
let produtos = [];
let cart = [];
let currentMode = null;

function money(value) {
  return Number(value || 0).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL"
  });
}

function showToast(message) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.add("show");

  setTimeout(() => {
    toast.classList.remove("show");
  }, 2500);
}

async function apiGet(url) {
  const response = await fetch(url);
  return await response.json();
}

async function apiPost(url, data = {}) {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
  });

  return await response.json();
}

async function apiDelete(url) {
  const response = await fetch(url, {
    method: "DELETE"
  });

  return await response.json();
}

function updatePageTitle(title, subtitle) {
  document.getElementById("pageTitle").textContent = title;
  document.getElementById("pageSubtitle").textContent = subtitle;
}

function setupNavigation() {
  const buttons = document.querySelectorAll(".menu-btn");

  buttons.forEach(button => {
    button.addEventListener("click", async () => {
      buttons.forEach(btn => btn.classList.remove("active"));
      button.classList.add("active");

      const page = button.dataset.page;

      document.querySelectorAll(".page").forEach(section => {
        section.classList.remove("active");
      });

      document.getElementById(`page-${page}`).classList.add("active");

      if (page === "pdv") {
        updatePageTitle("PDV", "Escolha o tipo de atendimento");
      }

      if (page === "pedidos") {
        updatePageTitle("Pedidos", "Histórico de pedidos finalizados");
        await renderOrders();
      }

      if (page === "cardapio") {
        updatePageTitle("Cardápio", "Cadastre pizzas, bordas, bebidas e adicionais");
        await loadCatalog();
        renderAdminLists();
      }

      if (page === "relatorio") {
        updatePageTitle("Relatório", "Resumo das vendas e comandas");
        await renderReport();
      }

      if (page === "backup") {
        updatePageTitle("Backup", "Backup do banco SQLite");
      }

      if (page === "config") {
        updatePageTitle("Configurações", "Ajustes do sistema");
      }
    });
  });
}

function setupModes() {
  document.querySelectorAll(".mode-card").forEach(card => {
    card.addEventListener("click", async () => {
      currentMode = card.dataset.mode;
      cart = [];

      document.getElementById("modeSelection").classList.add("hidden");
      document.getElementById("orderArea").classList.remove("hidden");

      document.getElementById("deliveryFields").classList.add("hidden");
      document.getElementById("balcaoFields").classList.add("hidden");
      document.getElementById("salaoFields").classList.add("hidden");
      document.getElementById("openTabsBox").classList.add("hidden");

      if (currentMode === "delivery") {
        document.getElementById("currentModeTitle").textContent = "Novo pedido Delivery";
        document.getElementById("deliveryFields").classList.remove("hidden");
      }

      if (currentMode === "balcao") {
        document.getElementById("currentModeTitle").textContent = "Novo pedido Balcão";
        document.getElementById("balcaoFields").classList.remove("hidden");
      }

      if (currentMode === "salao") {
        document.getElementById("currentModeTitle").textContent = "Pedido Salão";
        document.getElementById("salaoFields").classList.remove("hidden");
        document.getElementById("openTabsBox").classList.remove("hidden");
        await renderOpenTabs();
      }

      await loadCatalog();
      renderSelectors();
      renderCart();
    });
  });

  document.getElementById("backToModes").addEventListener("click", () => {
    currentMode = null;
    cart = [];

    document.getElementById("modeSelection").classList.remove("hidden");
    document.getElementById("orderArea").classList.add("hidden");

    renderCart();
  });
}

async function loadCatalog() {
  pizzas = await apiGet("/api/pizzas");
  produtos = await apiGet("/api/produtos");
}

function renderSelectors() {
  const flavorOne = document.getElementById("flavorOne");
  const flavorTwo = document.getElementById("flavorTwo");
  const borderSelect = document.getElementById("borderSelect");
  const productSelect = document.getElementById("productSelect");

  flavorOne.innerHTML = "";
  flavorTwo.innerHTML = "";
  borderSelect.innerHTML = "";
  productSelect.innerHTML = "";

  pizzas.forEach(pizza => {
    const label = `${pizza.codigo} - ${pizza.nome}`;

    const opt1 = document.createElement("option");
    opt1.value = pizza.id;
    opt1.textContent = label;
    flavorOne.appendChild(opt1);

    const opt2 = document.createElement("option");
    opt2.value = pizza.id;
    opt2.textContent = label;
    flavorTwo.appendChild(opt2);
  });

  produtos
    .filter(produto => produto.tipo === "borda")
    .forEach(produto => {
      const option = document.createElement("option");
      option.value = produto.id;
      option.textContent = `${produto.nome} - ${money(produto.preco)}`;
      borderSelect.appendChild(option);
    });

  produtos
    .filter(produto => produto.tipo !== "borda")
    .forEach(produto => {
      const option = document.createElement("option");
      option.value = produto.id;

      const categoria = produto.tipo === "bebida" && produto.categoria
        ? ` - ${produto.categoria}`
        : "";

      option.textContent = `${produto.nome}${categoria} - ${money(produto.preco)}`;
      productSelect.appendChild(option);
    });

  updateSecondFlavorVisibility();
}

function updateSecondFlavorVisibility() {
  const flavorCount = document.getElementById("flavorCount").value;
  const box = document.getElementById("secondFlavorBox");

  if (flavorCount === "2") {
    box.classList.remove("hidden");
  } else {
    box.classList.add("hidden");
  }
}

function getPizzaPrice(pizza, size) {
  if (size === "broto") {
    return Number(pizza.preco_broto);
  }

  return Number(pizza.preco_grande);
}

function addPizzaToCart() {
  const size = document.getElementById("pizzaSize").value;
  const flavorCount = document.getElementById("flavorCount").value;
  const flavorOneId = Number(document.getElementById("flavorOne").value);
  const flavorTwoId = Number(document.getElementById("flavorTwo").value);
  const borderId = Number(document.getElementById("borderSelect").value);
  const quantidade = Number(document.getElementById("pizzaQty").value || 1);

  const pizzaOne = pizzas.find(pizza => pizza.id === flavorOneId);
  const pizzaTwo = pizzas.find(pizza => pizza.id === flavorTwoId);
  const borda = produtos.find(produto => produto.id === borderId);

  if (!pizzaOne) {
    showToast("Cadastre pelo menos uma pizza no cardápio.");
    return;
  }

  if (flavorCount === "2" && !pizzaTwo) {
    showToast("Selecione o segundo sabor.");
    return;
  }

  const priceOne = getPizzaPrice(pizzaOne, size);
  const priceTwo = flavorCount === "2" ? getPizzaPrice(pizzaTwo, size) : 0;

  const basePrice = flavorCount === "2"
    ? Math.max(priceOne, priceTwo)
    : priceOne;

  const borderPrice = borda ? Number(borda.preco) : 0;
  const precoUnitario = basePrice + borderPrice;
  const total = precoUnitario * quantidade;

  const sizeLabel = size === "broto" ? "Broto" : "Grande";

  let descricao = `Pizza ${sizeLabel} - ${pizzaOne.nome}`;

  if (flavorCount === "2") {
    descricao += ` / ${pizzaTwo.nome}`;
  }

  if (borda && borda.nome !== "Sem borda") {
    descricao += ` + ${borda.nome}`;
  }

  cart.push({
    id: crypto.randomUUID(),
    descricao,
    quantidade,
    preco_unitario: precoUnitario,
    total
  });

  document.getElementById("pizzaQty").value = 1;

  renderCart();
  showToast("Pizza adicionada.");
}

function addProductToCart() {
  const productId = Number(document.getElementById("productSelect").value);
  const quantidade = Number(document.getElementById("productQty").value || 1);

  const produto = produtos.find(item => item.id === productId);

  if (!produto) {
    showToast("Cadastre produtos no cardápio.");
    return;
  }

  const precoUnitario = Number(produto.preco);
  const total = precoUnitario * quantidade;

  cart.push({
    id: crypto.randomUUID(),
    descricao: produto.nome,
    quantidade,
    preco_unitario: precoUnitario,
    total
  });

  document.getElementById("productQty").value = 1;

  renderCart();
  showToast("Produto adicionado.");
}

function cartTotal() {
  return cart.reduce((sum, item) => sum + Number(item.total), 0);
}

function renderCart() {
  const cartList = document.getElementById("cartList");
  const cartTotalElement = document.getElementById("cartTotal");

  cartTotalElement.textContent = money(cartTotal());

  if (cart.length === 0) {
    cartList.className = "cart-list empty";
    cartList.textContent = "Nenhum item adicionado.";
    return;
  }

  cartList.className = "cart-list";
  cartList.innerHTML = "";

  cart.forEach(item => {
    const div = document.createElement("div");
    div.className = "cart-item";

    div.innerHTML = `
      <div>
        <strong>${item.descricao}</strong>
        <small>${item.quantidade}x ${money(item.preco_unitario)} = ${money(item.total)}</small>
      </div>

      <div class="item-actions">
        <button class="icon-btn" onclick="removeCartItem('${item.id}')">X</button>
      </div>
    `;

    cartList.appendChild(div);
  });
}

function removeCartItem(id) {
  cart = cart.filter(item => item.id !== id);
  renderCart();
}

function clearCart() {
  cart = [];
  renderCart();
  showToast("Carrinho limpo.");
}

async function finishOrder() {
  if (!currentMode) {
    showToast("Escolha Delivery, Salão ou Balcão.");
    return;
  }

  if (cart.length === 0) {
    showToast("Adicione pelo menos um item.");
    return;
  }

  const pagamento = document.getElementById("paymentMethod").value;

  if (currentMode === "delivery") {
    const cliente = document.getElementById("deliveryName").value.trim();
    const telefone = document.getElementById("deliveryPhone").value.trim();
    const endereco = document.getElementById("deliveryAddress").value.trim();

    if (!cliente || !telefone || !endereco) {
      showToast("Preencha nome, telefone e endereço.");
      return;
    }

    await apiPost("/api/pedidos", {
      tipo: "Delivery",
      cliente,
      telefone,
      endereco,
      mesa: "",
      pagamento,
      itens: cart
    });

    document.getElementById("deliveryName").value = "";
    document.getElementById("deliveryPhone").value = "";
    document.getElementById("deliveryAddress").value = "";

    cart = [];
    renderCart();
    showToast("Pedido delivery salvo no SQLite.");
    return;
  }

  if (currentMode === "balcao") {
    const cliente = document.getElementById("balcaoName").value.trim();

    if (!cliente) {
      showToast("Preencha o nome do cliente.");
      return;
    }

    await apiPost("/api/pedidos", {
      tipo: "Balcão",
      cliente,
      telefone: "",
      endereco: "",
      mesa: "",
      pagamento,
      itens: cart
    });

    document.getElementById("balcaoName").value = "";

    cart = [];
    renderCart();
    showToast("Pedido balcão salvo no SQLite.");
    return;
  }

  if (currentMode === "salao") {
    const mesa = document.getElementById("mesaNumber").value.trim();

    if (!mesa) {
      showToast("Informe o número da mesa.");
      return;
    }

    await apiPost("/api/comandas/adicionar", {
      mesa,
      pagamento,
      itens: cart
    });

    document.getElementById("mesaNumber").value = "";

    cart = [];
    renderCart();
    await renderOpenTabs();
    showToast(`Itens adicionados na mesa ${mesa}.`);
  }
}

async function renderOpenTabs() {
  const comandas = await apiGet("/api/comandas");
  const list = document.getElementById("openTabsList");

  if (comandas.length === 0) {
    list.innerHTML = `<div class="hint">Nenhuma comanda aberta.</div>`;
    return;
  }

  list.innerHTML = "";

  comandas.forEach(comanda => {
    const div = document.createElement("div");
    div.className = "tab-item";

    div.innerHTML = `
      <header>
        <strong>Mesa ${comanda.mesa}</strong>
        <strong>${money(comanda.total)}</strong>
      </header>

      <ul>
        ${comanda.itens.map(item => `<li>${item.quantidade}x ${item.descricao} - ${money(item.total)}</li>`).join("")}
      </ul>

      <div class="actions-row">
        <button class="btn secondary" onclick="selecionarMesa('${comanda.mesa}')">Adicionar mais</button>
        <button class="btn success" onclick="closeTableTab(${comanda.id})">Fechar comanda</button>
      </div>
    `;

    list.appendChild(div);
  });
}

function selecionarMesa(mesa) {
  document.getElementById("mesaNumber").value = mesa;
  showToast(`Mesa ${mesa} selecionada.`);
}

async function closeTableTab(comandaId) {
  const pagamento = document.getElementById("paymentMethod").value;

  await apiPost(`/api/comandas/${comandaId}/fechar`, {
    pagamento
  });

  await renderOpenTabs();
  showToast("Comanda fechada e venda salva.");
}

async function renderOrders() {
  const pedidos = await apiGet("/api/pedidos");
  const list = document.getElementById("ordersList");

  if (!list) return;

  if (pedidos.length === 0) {
    list.innerHTML = `<div class="hint">Nenhum pedido finalizado.</div>`;
    return;
  }

  list.innerHTML = "";

  pedidos.forEach(pedido => {
    const div = document.createElement("div");
    div.className = "order-item";

    div.innerHTML = `
      <header>
        <strong>${pedido.tipo} - ${pedido.cliente || "Cliente"}</strong>
        <strong>${money(pedido.total)}</strong>
      </header>

      <div class="order-meta">
        ${pedido.criado_em} • Pagamento: ${pedido.pagamento || "Não informado"}
        ${pedido.telefone ? ` • Tel: ${pedido.telefone}` : ""}
        ${pedido.endereco ? `<br>Endereço: ${pedido.endereco}` : ""}
      </div>

      <ul>
        ${pedido.itens.map(item => `<li>${item.quantidade}x ${item.descricao} - ${money(item.total)}</li>`).join("")}
      </ul>
    `;

    list.appendChild(div);
  });
}

function renderAdminLists() {
  renderPizzaAdminList();
  renderProductAdminList();
  renderSelectors();
}

function renderPizzaAdminList() {
  const list = document.getElementById("pizzaList");
  list.innerHTML = "";

  pizzas.forEach(pizza => {
    const div = document.createElement("div");
    div.className = "admin-item";

    div.innerHTML = `
      <header>
        <strong>${pizza.codigo} - ${pizza.nome}</strong>
      </header>

      <div>
        Broto: ${money(pizza.preco_broto)} • Grande: ${money(pizza.preco_grande)}
      </div>

      <div class="admin-actions">
        <button class="btn secondary" onclick="editPizza(${pizza.id})">Editar</button>
        <button class="btn danger" onclick="deletePizza(${pizza.id})">Excluir</button>
      </div>
    `;

    list.appendChild(div);
  });
}

function renderProductAdminList() {
  const list = document.getElementById("productList");
  list.innerHTML = "";

  produtos.forEach(produto => {
    const div = document.createElement("div");
    div.className = "admin-item";

    const categoria = produto.tipo === "bebida" && produto.categoria
      ? ` • ${produto.categoria}`
      : "";

    div.innerHTML = `
      <header>
        <strong>${produto.nome}</strong>
        <strong>${money(produto.preco)}</strong>
      </header>

      <div>
        Tipo: ${produto.tipo}${categoria}
      </div>

      <div class="admin-actions">
        <button class="btn secondary" onclick="editProduct(${produto.id})">Editar</button>
        <button class="btn danger" onclick="deleteProduct(${produto.id})">Excluir</button>
      </div>
    `;

    list.appendChild(div);
  });
}

async function savePizzaFromForm() {
  const id = document.getElementById("pizzaIdInput").value;
  const codigo = document.getElementById("pizzaCodeInput").value.trim();
  const nome = document.getElementById("pizzaNameInput").value.trim();
  const preco_broto = Number(document.getElementById("pizzaBrotoInput").value || 0);
  const preco_grande = Number(document.getElementById("pizzaGrandeInput").value || 0);

  if (!codigo || !nome || preco_broto <= 0 || preco_grande <= 0) {
    showToast("Preencha código, nome, preço broto e preço grande.");
    return;
  }

  await apiPost("/api/pizzas", {
    id: id || null,
    codigo,
    nome,
    preco_broto,
    preco_grande
  });

  clearPizzaForm();
  await loadCatalog();
  renderAdminLists();

  showToast("Pizza salva no SQLite.");
}

function editPizza(id) {
  const pizza = pizzas.find(item => item.id === id);

  if (!pizza) return;

  document.getElementById("pizzaIdInput").value = pizza.id;
  document.getElementById("pizzaCodeInput").value = pizza.codigo;
  document.getElementById("pizzaNameInput").value = pizza.nome;
  document.getElementById("pizzaBrotoInput").value = pizza.preco_broto;
  document.getElementById("pizzaGrandeInput").value = pizza.preco_grande;

  document.getElementById("savePizza").textContent = "Atualizar pizza";
}

async function deletePizza(id) {
  await apiDelete(`/api/pizzas/${id}`);

  await loadCatalog();
  renderAdminLists();

  showToast("Pizza excluída.");
}

function clearPizzaForm() {
  document.getElementById("pizzaIdInput").value = "";
  document.getElementById("pizzaCodeInput").value = "";
  document.getElementById("pizzaNameInput").value = "";
  document.getElementById("pizzaBrotoInput").value = "";
  document.getElementById("pizzaGrandeInput").value = "";
  document.getElementById("savePizza").textContent = "Salvar pizza";
}

async function saveProductFromForm() {
  const id = document.getElementById("productIdInput").value;
  const tipo = document.getElementById("productTypeInput").value;
  const categoria = document.getElementById("drinkTypeInput").value;
  const nome = document.getElementById("productNameInput").value.trim();
  const preco = Number(document.getElementById("productPriceInput").value || 0);

  if (!tipo || !nome || preco < 0) {
    showToast("Preencha tipo, nome e preço.");
    return;
  }

  await apiPost("/api/produtos", {
    id: id || null,
    tipo,
    categoria,
    nome,
    preco
  });

  clearProductForm();
  await loadCatalog();
  renderAdminLists();

  showToast("Produto salvo no SQLite.");
}

function editProduct(id) {
  const produto = produtos.find(item => item.id === id);

  if (!produto) return;

  document.getElementById("productIdInput").value = produto.id;
  document.getElementById("productTypeInput").value = produto.tipo;
  document.getElementById("drinkTypeInput").value = produto.categoria || "";
  document.getElementById("productNameInput").value = produto.nome;
  document.getElementById("productPriceInput").value = produto.preco;

  document.getElementById("saveProduct").textContent = "Atualizar produto";
}

async function deleteProduct(id) {
  await apiDelete(`/api/produtos/${id}`);

  await loadCatalog();
  renderAdminLists();

  showToast("Produto excluído.");
}

function clearProductForm() {
  document.getElementById("productIdInput").value = "";
  document.getElementById("productTypeInput").value = "bebida";
  document.getElementById("drinkTypeInput").value = "";
  document.getElementById("productNameInput").value = "";
  document.getElementById("productPriceInput").value = "";
  document.getElementById("saveProduct").textContent = "Salvar produto";
}

async function renderReport() {
  const data = await apiGet("/api/relatorio");

  document.getElementById("statSales").textContent = data.total_vendas;
  document.getElementById("statRevenue").textContent = money(data.faturamento);
  document.getElementById("statTabs").textContent = data.comandas_abertas;

  const list = document.getElementById("reportByType");
  list.innerHTML = "";

  if (data.por_tipo.length === 0) {
    list.innerHTML = `<div class="hint">Nenhuma venda registrada.</div>`;
    return;
  }

  data.por_tipo.forEach(item => {
    const div = document.createElement("div");
    div.className = "report-item";
    div.innerHTML = `
      <strong>${item.tipo}</strong>
      <span>${money(item.total)}</span>
    `;
    list.appendChild(div);
  });
}

async function createBackup() {
  const result = await apiPost("/api/backup");

  if (result.ok) {
    showToast(`Backup criado: ${result.arquivo}`);
  } else {
    showToast("Erro ao criar backup.");
  }
}

function downloadDb() {
  window.location.href = "/api/backup/download";
}

async function resetSystem() {
  const confirmar = confirm("Tem certeza que deseja apagar tudo e recriar o sistema padrão?");

  if (!confirmar) return;

  await apiPost("/api/sistema/zerar");

  cart = [];
  currentMode = null;

  await loadCatalog();
  renderSelectors();
  renderCart();
  renderAdminLists();
  await renderOrders();
  await renderReport();

  showToast("Sistema zerado.");
}

function setupEvents() {
  document.getElementById("flavorCount").addEventListener("change", updateSecondFlavorVisibility);

  document.getElementById("addPizza").addEventListener("click", addPizzaToCart);
  document.getElementById("addProduct").addEventListener("click", addProductToCart);
  document.getElementById("clearCart").addEventListener("click", clearCart);
  document.getElementById("finishOrder").addEventListener("click", finishOrder);

  document.getElementById("savePizza").addEventListener("click", savePizzaFromForm);
  document.getElementById("saveProduct").addEventListener("click", saveProductFromForm);

  document.getElementById("createBackup").addEventListener("click", createBackup);
  document.getElementById("downloadDb").addEventListener("click", downloadDb);
  document.getElementById("resetSystem").addEventListener("click", resetSystem);
}

async function init() {
  setupNavigation();
  setupModes();
  setupEvents();

  await loadCatalog();

  renderSelectors();
  renderCart();
  renderAdminLists();
  await renderReport();
}

init();