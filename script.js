const STORAGE_KEYS = {
  pizzas: "pdv_pizzas",
  products: "pdv_products",
  orders: "pdv_orders",
  tabs: "pdv_tabs"
};

let currentMode = null;
let cart = [];

const defaultPizzas = [
  { id: crypto.randomUUID(), code: "01", name: "Mussarela", broto: 25, grande: 45 },
  { id: crypto.randomUUID(), code: "02", name: "Calabresa", broto: 27, grande: 48 },
  { id: crypto.randomUUID(), code: "03", name: "Portuguesa", broto: 30, grande: 55 },
  { id: crypto.randomUUID(), code: "04", name: "Frango com Catupiry", broto: 32, grande: 58 }
];

const defaultProducts = [
  { id: crypto.randomUUID(), type: "borda", drinkType: "", name: "Sem borda", price: 0 },
  { id: crypto.randomUUID(), type: "borda", drinkType: "", name: "Borda Catupiry", price: 8 },
  { id: crypto.randomUUID(), type: "borda", drinkType: "", name: "Borda Cheddar", price: 8 },
  { id: crypto.randomUUID(), type: "bebida", drinkType: "Refrigerante", name: "Coca-Cola 2L", price: 14 },
  { id: crypto.randomUUID(), type: "bebida", drinkType: "Refrigerante", name: "Guaraná 2L", price: 12 },
  { id: crypto.randomUUID(), type: "bebida", drinkType: "Cerveja", name: "Heineken Long Neck", price: 10 },
  { id: crypto.randomUUID(), type: "bebida", drinkType: "Vinho", name: "Vinho da casa", price: 45 },
  { id: crypto.randomUUID(), type: "adicional", drinkType: "", name: "Mussarela extra", price: 7 }
];

function getData(key, fallback) {
  const data = localStorage.getItem(key);
  return data ? JSON.parse(data) : fallback;
}

function setData(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

function getPizzas() {
  return getData(STORAGE_KEYS.pizzas, defaultPizzas);
}

function savePizzas(pizzas) {
  setData(STORAGE_KEYS.pizzas, pizzas);
}

function getProducts() {
  return getData(STORAGE_KEYS.products, defaultProducts);
}

function saveProducts(products) {
  setData(STORAGE_KEYS.products, products);
}

function getOrders() {
  return getData(STORAGE_KEYS.orders, []);
}

function saveOrders(orders) {
  setData(STORAGE_KEYS.orders, orders);
}

function getTabs() {
  return getData(STORAGE_KEYS.tabs, []);
}

function saveTabs(tabs) {
  setData(STORAGE_KEYS.tabs, tabs);
}

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

function updatePageTitle(title, subtitle) {
  document.getElementById("pageTitle").textContent = title;
  document.getElementById("pageSubtitle").textContent = subtitle;
}

function setupNavigation() {
  const buttons = document.querySelectorAll(".menu-btn");

  buttons.forEach(button => {
    button.addEventListener("click", () => {
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
        renderOrders();
      }

      if (page === "cardapio") {
        updatePageTitle("Cardápio", "Cadastre pizzas, bordas, bebidas e adicionais");
        renderAdminLists();
      }

      if (page === "relatorio") {
        updatePageTitle("Relatório", "Resumo das vendas e comandas");
        renderReport();
      }

      if (page === "config") {
        updatePageTitle("Configurações", "Ajustes do sistema");
      }
    });
  });
}

function setupModes() {
  document.querySelectorAll(".mode-card").forEach(card => {
    card.addEventListener("click", () => {
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
        renderOpenTabs();
      }

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

function renderSelectors() {
  const pizzas = getPizzas();
  const products = getProducts();

  const flavorOne = document.getElementById("flavorOne");
  const flavorTwo = document.getElementById("flavorTwo");
  const borderSelect = document.getElementById("borderSelect");
  const productSelect = document.getElementById("productSelect");

  flavorOne.innerHTML = "";
  flavorTwo.innerHTML = "";
  borderSelect.innerHTML = "";
  productSelect.innerHTML = "";

  pizzas.forEach(pizza => {
    const label = `${pizza.code} - ${pizza.name}`;

    const opt1 = document.createElement("option");
    opt1.value = pizza.id;
    opt1.textContent = label;
    flavorOne.appendChild(opt1);

    const opt2 = document.createElement("option");
    opt2.value = pizza.id;
    opt2.textContent = label;
    flavorTwo.appendChild(opt2);
  });

  products
    .filter(product => product.type === "borda")
    .forEach(product => {
      const option = document.createElement("option");
      option.value = product.id;
      option.textContent = `${product.name} - ${money(product.price)}`;
      borderSelect.appendChild(option);
    });

  products
    .filter(product => product.type !== "borda")
    .forEach(product => {
      const option = document.createElement("option");
      option.value = product.id;

      const category = product.type === "bebida" && product.drinkType
        ? ` - ${product.drinkType}`
        : "";

      option.textContent = `${product.name}${category} - ${money(product.price)}`;
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
  if (size === "broto") return Number(pizza.broto);
  return Number(pizza.grande);
}

function addPizzaToCart() {
  const pizzas = getPizzas();
  const products = getProducts();

  const size = document.getElementById("pizzaSize").value;
  const flavorCount = document.getElementById("flavorCount").value;
  const flavorOneId = document.getElementById("flavorOne").value;
  const flavorTwoId = document.getElementById("flavorTwo").value;
  const borderId = document.getElementById("borderSelect").value;
  const qty = Number(document.getElementById("pizzaQty").value || 1);

  const pizzaOne = pizzas.find(pizza => pizza.id === flavorOneId);
  const pizzaTwo = pizzas.find(pizza => pizza.id === flavorTwoId);
  const border = products.find(product => product.id === borderId);

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

  const borderPrice = border ? Number(border.price) : 0;
  const unitPrice = basePrice + borderPrice;
  const total = unitPrice * qty;

  const sizeLabel = size === "broto" ? "Broto" : "Grande";

  let description = `Pizza ${sizeLabel} - ${pizzaOne.name}`;

  if (flavorCount === "2") {
    description += ` / ${pizzaTwo.name}`;
  }

  if (border && border.name !== "Sem borda") {
    description += ` + ${border.name}`;
  }

  cart.push({
    id: crypto.randomUUID(),
    type: "pizza",
    description,
    qty,
    unitPrice,
    total
  });

  document.getElementById("pizzaQty").value = 1;
  renderCart();
  showToast("Pizza adicionada.");
}

function addProductToCart() {
  const products = getProducts();
  const productId = document.getElementById("productSelect").value;
  const qty = Number(document.getElementById("productQty").value || 1);

  const product = products.find(item => item.id === productId);

  if (!product) {
    showToast("Cadastre produtos no cardápio.");
    return;
  }

  const unitPrice = Number(product.price);
  const total = unitPrice * qty;

  cart.push({
    id: crypto.randomUUID(),
    type: product.type,
    description: product.name,
    qty,
    unitPrice,
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
        <strong>${item.description}</strong>
        <small>${item.qty}x ${money(item.unitPrice)} = ${money(item.total)}</small>
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

function finishOrder() {
  if (!currentMode) {
    showToast("Escolha Delivery, Salão ou Balcão.");
    return;
  }

  if (cart.length === 0) {
    showToast("Adicione pelo menos um item.");
    return;
  }

  const paymentMethod = document.getElementById("paymentMethod").value;

  if (currentMode === "delivery") {
    const name = document.getElementById("deliveryName").value.trim();
    const phone = document.getElementById("deliveryPhone").value.trim();
    const address = document.getElementById("deliveryAddress").value.trim();

    if (!name || !phone || !address) {
      showToast("Preencha nome, telefone e endereço.");
      return;
    }

    saveFinishedOrder({
      type: "Delivery",
      customer: name,
      phone,
      address,
      paymentMethod
    });

    clearDeliveryFields();
    return;
  }

  if (currentMode === "balcao") {
    const name = document.getElementById("balcaoName").value.trim();

    if (!name) {
      showToast("Preencha o nome do cliente.");
      return;
    }

    saveFinishedOrder({
      type: "Balcão",
      customer: name,
      phone: "",
      address: "",
      paymentMethod
    });

    document.getElementById("balcaoName").value = "";
    return;
  }

  if (currentMode === "salao") {
    const tableNumber = document.getElementById("mesaNumber").value.trim();

    if (!tableNumber) {
      showToast("Informe o número da mesa.");
      return;
    }

    addItemsToTable(tableNumber, paymentMethod);
    document.getElementById("mesaNumber").value = "";
    return;
  }
}

function saveFinishedOrder(extraData) {
  const orders = getOrders();

  const order = {
    id: crypto.randomUUID(),
    createdAt: new Date().toISOString(),
    items: [...cart],
    total: cartTotal(),
    ...extraData
  };

  orders.unshift(order);
  saveOrders(orders);

  cart = [];
  renderCart();
  renderOrders();
  renderReport();

  showToast("Pedido finalizado.");
}

function clearDeliveryFields() {
  document.getElementById("deliveryName").value = "";
  document.getElementById("deliveryPhone").value = "";
  document.getElementById("deliveryAddress").value = "";
}

function addItemsToTable(tableNumber, paymentMethod) {
  const tabs = getTabs();

  let tab = tabs.find(item => item.tableNumber === tableNumber && item.status === "open");

  if (!tab) {
    tab = {
      id: crypto.randomUUID(),
      tableNumber,
      status: "open",
      createdAt: new Date().toISOString(),
      paymentMethod,
      items: []
    };

    tabs.unshift(tab);
  }

  tab.items.push(...cart);
  tab.paymentMethod = paymentMethod;

  saveTabs(tabs);

  cart = [];
  renderCart();
  renderOpenTabs();
  renderReport();

  showToast(`Itens adicionados na mesa ${tableNumber}.`);
}

function renderOpenTabs() {
  const tabs = getTabs().filter(tab => tab.status === "open");
  const list = document.getElementById("openTabsList");

  if (tabs.length === 0) {
    list.innerHTML = `<div class="hint">Nenhuma comanda aberta.</div>`;
    return;
  }

  list.innerHTML = "";

  tabs.forEach(tab => {
    const total = tab.items.reduce((sum, item) => sum + Number(item.total), 0);

    const div = document.createElement("div");
    div.className = "tab-item";

    div.innerHTML = `
      <header>
        <strong>Mesa ${tab.tableNumber}</strong>
        <strong>${money(total)}</strong>
      </header>

      <ul>
        ${tab.items.map(item => `<li>${item.qty}x ${item.description} - ${money(item.total)}</li>`).join("")}
      </ul>

      <div class="actions-row">
        <button class="btn secondary" onclick="loadTabToCart('${tab.id}')">Adicionar mais</button>
        <button class="btn success" onclick="closeTableTab('${tab.id}')">Fechar comanda</button>
      </div>
    `;

    list.appendChild(div);
  });
}

function loadTabToCart(tabId) {
  const tabs = getTabs();
  const tab = tabs.find(item => item.id === tabId);

  if (!tab) return;

  document.getElementById("mesaNumber").value = tab.tableNumber;
  showToast(`Mesa ${tab.tableNumber} selecionada.`);
}

function closeTableTab(tabId) {
  const tabs = getTabs();
  const tab = tabs.find(item => item.id === tabId);

  if (!tab) return;

  const total = tab.items.reduce((sum, item) => sum + Number(item.total), 0);

  const orders = getOrders();

  orders.unshift({
    id: crypto.randomUUID(),
    createdAt: new Date().toISOString(),
    type: "Salão",
    customer: `Mesa ${tab.tableNumber}`,
    phone: "",
    address: "",
    paymentMethod: tab.paymentMethod || "Não informado",
    items: tab.items,
    total
  });

  const updatedTabs = tabs.filter(item => item.id !== tabId);

  saveOrders(orders);
  saveTabs(updatedTabs);

  renderOpenTabs();
  renderOrders();
  renderReport();

  showToast(`Comanda da mesa ${tab.tableNumber} fechada.`);
}

function renderOrders() {
  const orders = getOrders();
  const list = document.getElementById("ordersList");

  if (!list) return;

  if (orders.length === 0) {
    list.innerHTML = `<div class="hint">Nenhum pedido finalizado.</div>`;
    return;
  }

  list.innerHTML = "";

  orders.forEach(order => {
    const date = new Date(order.createdAt).toLocaleString("pt-BR");

    const div = document.createElement("div");
    div.className = "order-item";

    div.innerHTML = `
      <header>
        <strong>${order.type} - ${order.customer}</strong>
        <strong>${money(order.total)}</strong>
      </header>

      <div class="order-meta">
        ${date} • Pagamento: ${order.paymentMethod}
        ${order.phone ? ` • Tel: ${order.phone}` : ""}
        ${order.address ? `<br>Endereço: ${order.address}` : ""}
      </div>

      <ul>
        ${order.items.map(item => `<li>${item.qty}x ${item.description} - ${money(item.total)}</li>`).join("")}
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
  const pizzas = getPizzas();
  const list = document.getElementById("pizzaList");

  list.innerHTML = "";

  pizzas.forEach(pizza => {
    const div = document.createElement("div");
    div.className = "admin-item";

    div.innerHTML = `
      <header>
        <strong>${pizza.code} - ${pizza.name}</strong>
      </header>

      <div>
        Broto: ${money(pizza.broto)} • Grande: ${money(pizza.grande)}
      </div>

      <div class="admin-actions">
        <button class="btn secondary" onclick="editPizza('${pizza.id}')">Editar</button>
        <button class="btn danger" onclick="deletePizza('${pizza.id}')">Excluir</button>
      </div>
    `;

    list.appendChild(div);
  });
}

function renderProductAdminList() {
  const products = getProducts();
  const list = document.getElementById("productList");

  list.innerHTML = "";

  products.forEach(product => {
    const div = document.createElement("div");
    div.className = "admin-item";

    const category = product.type === "bebida" && product.drinkType
      ? ` • ${product.drinkType}`
      : "";

    div.innerHTML = `
      <header>
        <strong>${product.name}</strong>
        <strong>${money(product.price)}</strong>
      </header>

      <div>
        Tipo: ${product.type}${category}
      </div>

      <div class="admin-actions">
        <button class="btn secondary" onclick="editProduct('${product.id}')">Editar</button>
        <button class="btn danger" onclick="deleteProduct('${product.id}')">Excluir</button>
      </div>
    `;

    list.appendChild(div);
  });
}

function savePizzaFromForm() {
  const code = document.getElementById("pizzaCodeInput").value.trim();
  const name = document.getElementById("pizzaNameInput").value.trim();
  const broto = Number(document.getElementById("pizzaBrotoInput").value);
  const grande = Number(document.getElementById("pizzaGrandeInput").value);

  if (!code || !name || !broto || !grande) {
    showToast("Preencha código, nome, preço broto e preço grande.");
    return;
  }

  const pizzas = getPizzas();

  const editingId = document.getElementById("savePizza").dataset.editingId;

  if (editingId) {
    const pizza = pizzas.find(item => item.id === editingId);

    if (pizza) {
      pizza.code = code;
      pizza.name = name;
      pizza.broto = broto;
      pizza.grande = grande;
    }

    delete document.getElementById("savePizza").dataset.editingId;
    document.getElementById("savePizza").textContent = "Salvar pizza";
  } else {
    pizzas.push({
      id: crypto.randomUUID(),
      code,
      name,
      broto,
      grande
    });
  }

  savePizzas(pizzas);
  clearPizzaForm();
  renderAdminLists();
  showToast("Pizza salva.");
}

function editPizza(id) {
  const pizza = getPizzas().find(item => item.id === id);

  if (!pizza) return;

  document.getElementById("pizzaCodeInput").value = pizza.code;
  document.getElementById("pizzaNameInput").value = pizza.name;
  document.getElementById("pizzaBrotoInput").value = pizza.broto;
  document.getElementById("pizzaGrandeInput").value = pizza.grande;

  document.getElementById("savePizza").dataset.editingId = id;
  document.getElementById("savePizza").textContent = "Atualizar pizza";
}

function deletePizza(id) {
  const pizzas = getPizzas().filter(item => item.id !== id);
  savePizzas(pizzas);
  renderAdminLists();
  showToast("Pizza excluída.");
}

function clearPizzaForm() {
  document.getElementById("pizzaCodeInput").value = "";
  document.getElementById("pizzaNameInput").value = "";
  document.getElementById("pizzaBrotoInput").value = "";
  document.getElementById("pizzaGrandeInput").value = "";
}

function saveProductFromForm() {
  const type = document.getElementById("productTypeInput").value;
  const drinkType = document.getElementById("drinkTypeInput").value;
  const name = document.getElementById("productNameInput").value.trim();
  const price = Number(document.getElementById("productPriceInput").value);

  if (!type || !name && name !== "Sem borda" || Number.isNaN(price)) {
    showToast("Preencha tipo, nome e preço.");
    return;
  }

  const products = getProducts();

  const editingId = document.getElementById("saveProduct").dataset.editingId;

  if (editingId) {
    const product = products.find(item => item.id === editingId);

    if (product) {
      product.type = type;
      product.drinkType = type === "bebida" ? drinkType : "";
      product.name = name;
      product.price = price;
    }

    delete document.getElementById("saveProduct").dataset.editingId;
    document.getElementById("saveProduct").textContent = "Salvar produto";
  } else {
    products.push({
      id: crypto.randomUUID(),
      type,
      drinkType: type === "bebida" ? drinkType : "",
      name,
      price
    });
  }

  saveProducts(products);
  clearProductForm();
  renderAdminLists();
  showToast("Produto salvo.");
}

function editProduct(id) {
  const product = getProducts().find(item => item.id === id);

  if (!product) return;

  document.getElementById("productTypeInput").value = product.type;
  document.getElementById("drinkTypeInput").value = product.drinkType || "";
  document.getElementById("productNameInput").value = product.name;
  document.getElementById("productPriceInput").value = product.price;

  document.getElementById("saveProduct").dataset.editingId = id;
  document.getElementById("saveProduct").textContent = "Atualizar produto";
}

function deleteProduct(id) {
  const products = getProducts().filter(item => item.id !== id);
  saveProducts(products);
  renderAdminLists();
  showToast("Produto excluído.");
}

function clearProductForm() {
  document.getElementById("productTypeInput").value = "bebida";
  document.getElementById("drinkTypeInput").value = "";
  document.getElementById("productNameInput").value = "";
  document.getElementById("productPriceInput").value = "";
}

function clearOrders() {
  saveOrders([]);
  renderOrders();
  renderReport();
  showToast("Histórico de pedidos limpo.");
}

function renderReport() {
  const orders = getOrders();
  const tabs = getTabs().filter(tab => tab.status === "open");

  const totalRevenue = orders.reduce((sum, order) => sum + Number(order.total), 0);

  document.getElementById("statSales").textContent = orders.length;
  document.getElementById("statRevenue").textContent = money(totalRevenue);
  document.getElementById("statTabs").textContent = tabs.length;

  const byType = {
    Delivery: 0,
    Balcão: 0,
    Salão: 0
  };

  orders.forEach(order => {
    if (!byType[order.type]) byType[order.type] = 0;
    byType[order.type] += Number(order.total);
  });

  const list = document.getElementById("reportByType");
  list.innerHTML = "";

  Object.entries(byType).forEach(([type, total]) => {
    const div = document.createElement("div");
    div.className = "report-item";
    div.innerHTML = `
      <strong>${type}</strong>
      <span>${money(total)}</span>
    `;
    list.appendChild(div);
  });
}

function resetSystem() {
  localStorage.removeItem(STORAGE_KEYS.pizzas);
  localStorage.removeItem(STORAGE_KEYS.products);
  localStorage.removeItem(STORAGE_KEYS.orders);
  localStorage.removeItem(STORAGE_KEYS.tabs);

  cart = [];
  currentMode = null;

  renderSelectors();
  renderCart();
  renderOrders();
  renderAdminLists();
  renderReport();
  renderOpenTabs();

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

  document.getElementById("clearOrders").addEventListener("click", clearOrders);
  document.getElementById("resetSystem").addEventListener("click", resetSystem);
}

function initStorage() {
  if (!localStorage.getItem(STORAGE_KEYS.pizzas)) {
    savePizzas(defaultPizzas);
  }

  if (!localStorage.getItem(STORAGE_KEYS.products)) {
    saveProducts(defaultProducts);
  }

  if (!localStorage.getItem(STORAGE_KEYS.orders)) {
    saveOrders([]);
  }

  if (!localStorage.getItem(STORAGE_KEYS.tabs)) {
    saveTabs([]);
  }
}

function init() {
  initStorage();
  setupNavigation();
  setupModes();
  setupEvents();
  renderSelectors();
  renderCart();
  renderOrders();
  renderAdminLists();
  renderReport();
}

init();