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

  if (!toast) {
    alert(message);
    return;
  }

  toast.textContent = message;
  toast.classList.add("show");

  setTimeout(() => {
    toast.classList.remove("show");
  }, 3000);
}

function showConfirm(message) {
  return new Promise(resolve => {
    const modal = document.getElementById("confirmModal");
    const messageBox = document.getElementById("confirmMessage");
    const cancelBtn = document.getElementById("confirmCancel");
    const okBtn = document.getElementById("confirmOk");

    messageBox.textContent = message;
    modal.classList.remove("hidden");

    function cleanup(result) {
      modal.classList.add("hidden");
      cancelBtn.removeEventListener("click", cancelHandler);
      okBtn.removeEventListener("click", okHandler);
      resolve(result);
    }

    function cancelHandler() {
      cleanup(false);
    }

    function okHandler() {
      cleanup(true);
    }

    cancelBtn.addEventListener("click", cancelHandler);
    okBtn.addEventListener("click", okHandler);
  });
}

async function apiRequest(url, options = {}) {
  try {
    const response = await fetch(url, options);

    if (response.status === 401) {
      showToast("Sessão expirada. Faça login novamente.");
      setTimeout(() => {
        window.location.href = "/login";
      }, 1000);
      throw new Error("Sessão expirada.");
    }

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      const msg = data.erro || "Erro ao processar solicitação.";
      showToast(msg);
      throw new Error(msg);
    }

    return data;
  } catch (error) {
    if (!String(error.message).includes("Sessão")) {
      showToast(error.message || "Erro de conexão com o servidor.");
    }

    throw error;
  }
}

async function apiGet(url) {
  return await apiRequest(url);
}

async function apiPost(url, data = {}) {
  return await apiRequest(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
  });
}

async function apiPut(url, data = {}) {
  return await apiRequest(url, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
  });
}

async function apiDelete(url) {
  return await apiRequest(url, {
    method: "DELETE"
  });
}

function updatePageTitle(title, subtitle) {
  document.getElementById("pageTitle").textContent = title;
  document.getElementById("pageSubtitle").textContent = subtitle;
}

function getOrderObservation() {
  const field = document.getElementById("orderObservation");
  return field ? field.value.trim() : "";
}

function clearOrderObservation() {
  const field = document.getElementById("orderObservation");

  if (field) {
    field.value = "";
  }
}

function openPrintWindow(pedidoId) {
  if (!pedidoId) return;

  const url = `/cupom/${pedidoId}`;
  window.open(url, "_blank", "width=420,height=700");
}

function openCashPrintWindow(caixaId) {
  if (!caixaId) return;

  const url = `/caixa/cupom/${caixaId}`;
  window.open(url, "_blank", "width=420,height=700");
}

function openKitchenPrintWindow(comandaId, itensIds = [], observacao = "") {
  if (!comandaId) return;

  const params = new URLSearchParams();

  if (Array.isArray(itensIds) && itensIds.length > 0) {
    params.set("itens", itensIds.join(","));
  }

  if (observacao) {
    params.set("observacao", observacao);
  }

  const query = params.toString();
  const url = query
    ? `/cozinha/comanda/${comandaId}?${query}`
    : `/cozinha/comanda/${comandaId}`;

  window.open(url, "_blank", "width=420,height=700");
}

function updateFinishButtonText() {
  const button = document.getElementById("finishOrder");

  if (!button) return;

  if (currentMode === "salao") {
    button.textContent = "Adicionar na mesa e imprimir cozinha";
  } else {
    button.textContent = "Finalizar e imprimir";
  }
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
        await refreshTopCashStatus();
      }

      if (page === "caixa") {
        updatePageTitle("Caixa", "Abertura, fechamento, sangria e reforço");
        await renderCashPage();
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
      clearOrderObservation();
      updateFinishButtonText();

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
    clearOrderObservation();
    updateFinishButtonText();

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

  if (quantidade <= 0) {
    showToast("Informe uma quantidade válida.");
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

  if (quantidade <= 0) {
    showToast("Informe uma quantidade válida.");
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

async function clearCart() {
  if (cart.length === 0) return;

  const ok = await showConfirm("Deseja limpar todos os itens do carrinho?");

  if (!ok) return;

  cart = [];
  renderCart();
  showToast("Carrinho limpo.");
}

async function finishOrder() {
  try {
    if (!currentMode) {
      showToast("Escolha Delivery, Salão ou Balcão.");
      return;
    }

    if (cart.length === 0) {
      showToast("Adicione pelo menos um item.");
      return;
    }

    const pagamento = document.getElementById("paymentMethod").value;
    const observacao = getOrderObservation();

    if (currentMode === "delivery") {
      const cliente = document.getElementById("deliveryName").value.trim();
      const telefone = document.getElementById("deliveryPhone").value.trim();
      const endereco = document.getElementById("deliveryAddress").value.trim();

      if (!cliente || !telefone || !endereco) {
        showToast("Preencha nome, telefone e endereço.");
        return;
      }

      const result = await apiPost("/api/pedidos", {
        tipo: "Delivery",
        cliente,
        telefone,
        endereco,
        mesa: "",
        pagamento,
        observacao,
        itens: cart
      });

      document.getElementById("deliveryName").value = "";
      document.getElementById("deliveryPhone").value = "";
      document.getElementById("deliveryAddress").value = "";
      clearOrderObservation();

      cart = [];
      renderCart();
      await refreshTopCashStatus();

      showToast("Pedido delivery salvo. Abrindo impressão.");
      openPrintWindow(result.pedido_id);
      return;
    }

    if (currentMode === "balcao") {
      const cliente = document.getElementById("balcaoName").value.trim();

      if (!cliente) {
        showToast("Preencha o nome do cliente.");
        return;
      }

      const result = await apiPost("/api/pedidos", {
        tipo: "Balcão",
        cliente,
        telefone: "",
        endereco: "",
        mesa: "",
        pagamento,
        observacao,
        itens: cart
      });

      document.getElementById("balcaoName").value = "";
      clearOrderObservation();

      cart = [];
      renderCart();
      await refreshTopCashStatus();

      showToast("Pedido balcão salvo. Abrindo impressão.");
      openPrintWindow(result.pedido_id);
      return;
    }

    if (currentMode === "salao") {
      const mesa = document.getElementById("mesaNumber").value.trim();

      if (!mesa) {
        showToast("Informe o número da mesa.");
        return;
      }

      const result = await apiPost("/api/comandas/adicionar", {
        mesa,
        pagamento,
        observacao,
        itens: cart
      });

      openKitchenPrintWindow(
        result.comanda_id,
        result.itens_ids || [],
        observacao
      );

      document.getElementById("mesaNumber").value = "";
      clearOrderObservation();

      cart = [];
      renderCart();
      await renderOpenTabs();

      showToast(`Itens adicionados na mesa ${mesa}. Via da cozinha aberta para impressão.`);
    }
  } catch (error) {
    console.error(error);
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
    const observacaoHtml = comanda.observacao
      ? `<div class="hint"><strong>Observação:</strong><br>${comanda.observacao}</div>`
      : "";

    const div = document.createElement("div");
    div.className = "tab-item";

    div.innerHTML = `
      <header>
        <strong>Mesa ${comanda.mesa}</strong>
        <strong>${money(comanda.total)}</strong>
      </header>

      ${observacaoHtml}

      <ul>
        ${comanda.itens.map(item => `
          <li>
            <strong>${item.quantidade}x ${item.descricao}</strong><br>
            <span>${money(item.preco_unitario)} cada • Total: ${money(item.total)}</span>

            <div class="admin-actions" style="margin-top: 8px; margin-bottom: 10px;">
              <button class="btn secondary" onclick="alterarItemComanda(${item.id}, ${item.quantidade})">
                Alterar qtd
              </button>
              <button class="btn danger" onclick="excluirItemComanda(${item.id}, '${item.descricao.replace(/'/g, "\\'")}')">
                Excluir item
              </button>
            </div>
          </li>
        `).join("")}
      </ul>

      <div class="actions-row">
        <button class="btn secondary" onclick="selecionarMesa('${comanda.mesa}')">Adicionar mais</button>
        <button class="btn success" onclick="closeTableTab(${comanda.id})">Fechar e imprimir</button>
      </div>
    `;

    list.appendChild(div);
  });
}

function selecionarMesa(mesa) {
  document.getElementById("mesaNumber").value = mesa;
  showToast(`Mesa ${mesa} selecionada.`);
}

async function alterarItemComanda(itemId, quantidadeAtual) {
  try {
    const novaQuantidadeTexto = prompt(
      "Digite a nova quantidade do item:",
      quantidadeAtual
    );

    if (novaQuantidadeTexto === null) {
      return;
    }

    const novaQuantidade = Number(novaQuantidadeTexto);

    if (!Number.isInteger(novaQuantidade) || novaQuantidade <= 0) {
      showToast("Informe uma quantidade inteira maior que zero.");
      return;
    }

    await apiPut(`/api/comandas/item/${itemId}`, {
      quantidade: novaQuantidade
    });

    await renderOpenTabs();
    showToast("Quantidade do item alterada.");
  } catch (error) {
    console.error(error);
  }
}

async function excluirItemComanda(itemId, descricao) {
  try {
    const ok = await showConfirm(`Deseja excluir este item da comanda?\n\n${descricao}`);

    if (!ok) return;

    await apiDelete(`/api/comandas/item/${itemId}`);

    await renderOpenTabs();
    await renderReport();

    showToast("Item excluído da comanda.");
  } catch (error) {
    console.error(error);
  }
}

async function closeTableTab(comandaId) {
  try {
    const ok = await showConfirm("Deseja fechar esta comanda e salvar como venda?");
    if (!ok) return;

    const pagamento = document.getElementById("paymentMethod").value;

    const result = await apiPost(`/api/comandas/${comandaId}/fechar`, {
      pagamento
    });

    await renderOpenTabs();
    await refreshTopCashStatus();

    showToast("Comanda fechada. Abrindo impressão.");
    openPrintWindow(result.pedido_id);
  } catch (error) {
    console.error(error);
  }
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
    const observacaoHtml = pedido.observacao
      ? `<div class="hint"><strong>Observação:</strong><br>${pedido.observacao}</div>`
      : "";

    const div = document.createElement("div");
    div.className = "order-item";

    div.innerHTML = `
      <header>
        <strong>#${pedido.id} - ${pedido.tipo} - ${pedido.cliente || "Cliente"}</strong>
        <strong>${money(pedido.total)}</strong>
      </header>

      <div class="order-meta">
        ${pedido.criado_em} • Pagamento: ${pedido.pagamento || "Não informado"}
        ${pedido.telefone ? ` • Tel: ${pedido.telefone}` : ""}
        ${pedido.endereco ? `<br>Endereço: ${pedido.endereco}` : ""}
      </div>

      ${observacaoHtml}

      <ul>
        ${pedido.itens.map(item => `<li>${item.quantidade}x ${item.descricao} - ${money(item.total)}</li>`).join("")}
      </ul>

      <div class="admin-actions">
        <button class="btn secondary" onclick="openPrintWindow(${pedido.id})">Imprimir cupom</button>
      </div>
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
  try {
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
  } catch (error) {
    console.error(error);
  }
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
  try {
    const pizza = pizzas.find(item => item.id === id);
    const nome = pizza ? pizza.nome : "esta pizza";

    const ok = await showConfirm(`Deseja excluir ${nome}?`);
    if (!ok) return;

    await apiDelete(`/api/pizzas/${id}`);

    await loadCatalog();
    renderAdminLists();

    showToast("Pizza excluída.");
  } catch (error) {
    console.error(error);
  }
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
  try {
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
  } catch (error) {
    console.error(error);
  }
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
  try {
    const produto = produtos.find(item => item.id === id);
    const nome = produto ? produto.nome : "este produto";

    const ok = await showConfirm(`Deseja excluir ${nome}?`);
    if (!ok) return;

    await apiDelete(`/api/produtos/${id}`);

    await loadCatalog();
    renderAdminLists();

    showToast("Produto excluído.");
  } catch (error) {
    console.error(error);
  }
}

function clearProductForm() {
  document.getElementById("productIdInput").value = "";
  document.getElementById("productTypeInput").value = "bebida";
  document.getElementById("drinkTypeInput").value = "";
  document.getElementById("productNameInput").value = "";
  document.getElementById("productPriceInput").value = "";
  document.getElementById("saveProduct").textContent = "Salvar produto";
}

async function refreshTopCashStatus() {
  try {
    const data = await apiGet("/api/caixa/status");
    const box = document.getElementById("topCashStatus");

    if (!data.aberto) {
      box.className = "status-box status-danger";
      box.innerHTML = `
        <span>Status do caixa</span>
        <strong>Fechado</strong>
      `;
      return;
    }

    box.className = "status-box";
    box.innerHTML = `
      <span>Caixa aberto</span>
      <strong>${money(data.caixa.valor_sistema)}</strong>
    `;
  } catch (error) {
    console.error(error);
  }
}

async function renderCashPage() {
  const status = await apiGet("/api/caixa/status");
  const statusBox = document.getElementById("cashStatusBox");
  const openCashPanel = document.getElementById("openCashPanel");
  const cashControlsPanel = document.getElementById("cashControlsPanel");
  const movementsList = document.getElementById("cashMovementsList");

  if (!status.aberto) {
    statusBox.className = "cash-status-box closed";
    statusBox.innerHTML = `
      <strong>Caixa fechado</strong>
      <span>Abra o caixa antes de começar as vendas.</span>
    `;

    openCashPanel.classList.remove("hidden");
    cashControlsPanel.classList.add("hidden");
    movementsList.innerHTML = `<div class="hint">Nenhum caixa aberto.</div>`;
  } else {
    const caixa = status.caixa;

    statusBox.className = "cash-status-box opened";
    statusBox.innerHTML = `
      <strong>Caixa aberto</strong>
      <span>Abertura: ${caixa.aberto_em}</span>
      <span>Valor inicial: ${money(caixa.valor_inicial)}</span>
      <span>Vendas: ${caixa.vendas_qtd} pedido(s) • ${money(caixa.vendas_total)}</span>
      <span>Valor atual no sistema: ${money(caixa.valor_sistema)}</span>
    `;

    openCashPanel.classList.add("hidden");
    cashControlsPanel.classList.remove("hidden");

    if (!caixa.movimentos || caixa.movimentos.length === 0) {
      movementsList.innerHTML = `<div class="hint">Nenhum movimento lançado.</div>`;
    } else {
      movementsList.innerHTML = "";

      caixa.movimentos.forEach(mov => {
        const div = document.createElement("div");
        div.className = "admin-item";

        div.innerHTML = `
          <header>
            <strong>${mov.tipo === "sangria" ? "Sangria" : "Reforço"}</strong>
            <strong>${money(mov.valor)}</strong>
          </header>
          <div>${mov.descricao || ""}</div>
          <small>${mov.criado_em}</small>
        `;

        movementsList.appendChild(div);
      });
    }
  }

  await renderCashHistory();
  await refreshTopCashStatus();
}

async function renderCashHistory() {
  const caixas = await apiGet("/api/caixa/historico");
  const list = document.getElementById("cashHistoryList");

  if (caixas.length === 0) {
    list.innerHTML = `<div class="hint">Nenhum caixa registrado.</div>`;
    return;
  }

  list.innerHTML = "";

  caixas.forEach(caixa => {
    const div = document.createElement("div");
    div.className = "order-item";

    const statusLabel = caixa.status === "aberto" ? "Aberto" : "Fechado";
    const finalInfo = caixa.status === "fechado"
      ? `<br>Valor sistema: ${money(caixa.valor_sistema)} • Valor informado: ${money(caixa.valor_final_informado)}`
      : "";

    const imprimirFechamento = caixa.status === "fechado"
      ? `<button class="btn secondary" onclick="openCashPrintWindow(${caixa.id})">Imprimir fechamento</button>`
      : "";

    div.innerHTML = `
      <header>
        <strong>Caixa #${caixa.id} - ${statusLabel}</strong>
        <strong>${money(caixa.vendas_total)}</strong>
      </header>

      <div class="order-meta">
        Aberto em: ${caixa.aberto_em}
        ${caixa.fechado_em ? `<br>Fechado em: ${caixa.fechado_em}` : ""}
        <br>Vendas: ${caixa.vendas_qtd}
        ${finalInfo}
      </div>

      <div class="admin-actions">
        ${imprimirFechamento}
      </div>
    `;

    list.appendChild(div);
  });
}

async function openCash() {
  try {
    const valor = Number(document.getElementById("cashInitialValue").value || 0);
    const observacao = document.getElementById("cashOpenObs").value.trim();

    await apiPost("/api/caixa/abrir", {
      valor_inicial: valor,
      observacao
    });

    document.getElementById("cashInitialValue").value = "";
    document.getElementById("cashOpenObs").value = "";

    showToast("Caixa aberto.");
    await renderCashPage();
  } catch (error) {
    console.error(error);
  }
}

async function addCashMovement() {
  try {
    const tipo = document.getElementById("cashMovementType").value;
    const valor = Number(document.getElementById("cashMovementValue").value || 0);
    const descricao = document.getElementById("cashMovementDesc").value.trim();

    if (valor <= 0) {
      showToast("Informe um valor maior que zero.");
      return;
    }

    await apiPost("/api/caixa/movimento", {
      tipo,
      valor,
      descricao
    });

    document.getElementById("cashMovementValue").value = "";
    document.getElementById("cashMovementDesc").value = "";

    showToast("Movimento registrado.");
    await renderCashPage();
  } catch (error) {
    console.error(error);
  }
}

async function closeCash() {
  try {
    const valor = Number(document.getElementById("cashCloseValue").value || 0);
    const observacao = document.getElementById("cashCloseObs").value.trim();

    const ok = await showConfirm("Deseja fechar o caixa atual e imprimir o fechamento?");
    if (!ok) return;

    const result = await apiPost("/api/caixa/fechar", {
      valor_final_informado: valor,
      observacao
    });

    document.getElementById("cashCloseValue").value = "";
    document.getElementById("cashCloseObs").value = "";

    showToast(`Caixa fechado. Diferença: ${money(result.diferenca)}. Abrindo impressão.`);

    openCashPrintWindow(result.caixa_id);

    await renderCashPage();
  } catch (error) {
    console.error(error);
  }
}

async function renderReport() {
  const data = await apiGet("/api/relatorio");

  document.getElementById("statSales").textContent = data.total_vendas;
  document.getElementById("statRevenue").textContent = money(data.faturamento);
  document.getElementById("statTabs").textContent = data.comandas_abertas;

  document.getElementById("statSalesGeneral").textContent = data.total_vendas_geral;
  document.getElementById("statRevenueGeneral").textContent = money(data.faturamento_geral);

  document.getElementById("statOpenCash").textContent = data.caixa_aberto
    ? money(data.caixa_aberto.valor_sistema)
    : "Fechado";

  const list = document.getElementById("reportByType");
  list.innerHTML = "";

  if (data.por_tipo.length === 0) {
    list.innerHTML = `<div class="hint">Nenhuma venda registrada hoje.</div>`;
  } else {
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

  const paymentList = document.getElementById("reportByPayment");
  paymentList.innerHTML = "";

  if (!data.por_pagamento || data.por_pagamento.length === 0) {
    paymentList.innerHTML = `<div class="hint">Nenhum pagamento registrado hoje.</div>`;
  } else {
    data.por_pagamento.forEach(item => {
      const div = document.createElement("div");
      div.className = "report-item";
      div.innerHTML = `
        <strong>${item.pagamento || "Não informado"}</strong>
        <span>${money(item.total)}</span>
      `;
      paymentList.appendChild(div);
    });
  }

  await refreshTopCashStatus();
}

async function createBackup() {
  try {
    const result = await apiPost("/api/backup");

    if (result.ok) {
      showToast(`Backup criado: ${result.arquivo}`);
    } else {
      showToast("Erro ao criar backup.");
    }
  } catch (error) {
    console.error(error);
  }
}

function downloadDb() {
  window.location.href = "/api/backup/download";
}

async function resetSystem() {
  try {
    const ok = await showConfirm("Tem certeza que deseja apagar tudo e recriar o sistema padrão?");
    if (!ok) return;

    await apiPost("/api/sistema/zerar");

    cart = [];
    currentMode = null;

    await loadCatalog();
    renderSelectors();
    renderCart();
    renderAdminLists();
    await renderOrders();
    await renderReport();
    await refreshTopCashStatus();

    showToast("Sistema zerado.");
  } catch (error) {
    console.error(error);
  }
}

function setupEvents() {
  document.getElementById("flavorCount").addEventListener("change", updateSecondFlavorVisibility);

  document.getElementById("addPizza").addEventListener("click", addPizzaToCart);
  document.getElementById("addProduct").addEventListener("click", addProductToCart);
  document.getElementById("clearCart").addEventListener("click", clearCart);
  document.getElementById("finishOrder").addEventListener("click", finishOrder);

  document.getElementById("savePizza").addEventListener("click", savePizzaFromForm);
  document.getElementById("saveProduct").addEventListener("click", saveProductFromForm);

  document.getElementById("openCash").addEventListener("click", openCash);
  document.getElementById("addCashMovement").addEventListener("click", addCashMovement);
  document.getElementById("closeCash").addEventListener("click", closeCash);

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

  await refreshTopCashStatus();
  await renderReport();
}

init();