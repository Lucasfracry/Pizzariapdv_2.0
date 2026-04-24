import { getData, setData } from './js/db.js';

// --- INJEÇÃO DO MODAL (Para Meio a Meio profissional) ---
if (!document.getElementById("modalMeio")) {
    const modalHTML = `
    <div id="modalMeio" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:9999; justify-content:center; align-items:center; font-family:sans-serif;">
        <div style="background:#1e1e1e; padding:30px; border-radius:12px; border:2px solid #ffc107; width:400px; color:white;">
            <h2 style="margin-top:0; color:#ffc107; text-align:center;">🍕 Montar Meio a Meio</h2>
            <label>Sabor 1:</label>
            <select id="selSabor1" style="width:100%; padding:15px; margin:10px 0; background:#333; color:white; font-size:18px; border-radius:5px;"></select>
            <label>Sabor 2:</label>
            <select id="selSabor2" style="width:100%; padding:15px; margin:10px 0; background:#333; color:white; font-size:18px; border-radius:5px;"></select>
            <button onclick="confirmarMeioMeio()" style="width:100%; background:#28a745; color:white; padding:20px; border:none; border-radius:8px; font-weight:bold; cursor:pointer; font-size:18px; margin-top:15px;">ADICIONAR AO PEDIDO</button>
            <button onclick="fecharModalMeio()" style="width:100%; background:transparent; color:#ff4444; border:none; margin-top:10px; cursor:pointer; width:100%;">Cancelar</button>
        </div>
    </div>`;
    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

// --- FUNÇÃO PARA ADICIONAR PIZZA INTEIRA (O que estava faltando!) ---
window.adicionarPizzaInteira = function(nome, preco) {
    const carrinho = getData("carrinho") || [];
    carrinho.push({ nome: nome, preco: Number(preco) });
    setData("carrinho", carrinho);
    renderizarCarrinho();
};

// --- NAVEGAÇÃO ---
window.mostrarTela = function(id) {
    document.querySelectorAll('.tela').forEach(t => t.classList.remove('ativa'));
    document.getElementById(id).classList.add('ativa');
};

// --- RENDERIZAÇÃO DOS PRODUTOS ---
window.renderizarProdutos = function() {
    const gridPDV = document.getElementById("produtos");
    const gridCadastro = document.getElementById("listaProdutos");
    const produtos = getData("produtos") || [];

    if (gridPDV) gridPDV.innerHTML = "";
    if (gridCadastro) gridCadastro.innerHTML = "";

    produtos.forEach(p => {
        // Card para o PDV (com clique para adicionar)
        const cardPDV = `
            <div class="item-card" onclick="adicionarPizzaInteira('${p.nome}', ${p.precoGrande})" style="cursor:pointer; padding:15px; background:#333; color:white; border-radius:8px; border-left:5px solid #ffc107; transition: 0.2s;">
                <strong style="color:#ffc107; font-size:18px;">${p.numero ? p.numero + ' - ' : ''}${p.nome.toUpperCase()}</strong><br>
                <small>G: R$ ${Number(p.precoGrande).toFixed(2)} | B: R$ ${Number(p.precoBroto).toFixed(2)}</small>
            </div>
        `;
        if (gridPDV) gridPDV.innerHTML += cardPDV;

        // Card para a tela de Cadastro (apenas visualização)
        if (gridCadastro) {
            gridCadastro.innerHTML += `<div class="item">${p.nome} - R$ ${p.precoGrande}</div>`;
        }
    });
};

// --- LÓGICA MEIO A MEIO ---
window.addMeioMeio = function() {
    const produtos = getData("produtos") || [];
    const pizzas = produtos.filter(p => p.tipo === "pizza");
    if (pizzas.length < 2) return alert("Cadastre 2 pizzas!");

    const s1 = document.getElementById("selSabor1");
    const s2 = document.getElementById("selSabor2");
    const options = pizzas.map(p => `<option value="${p.nome}" data-preco="${p.precoGrande}">${p.nome}</option>`).join("");
    
    s1.innerHTML = options;
    s2.innerHTML = options;
    document.getElementById("modalMeio").style.display = "flex";
};

window.fecharModalMeio = () => document.getElementById("modalMeio").style.display = "none";

window.confirmarMeioMeio = function() {
    const s1 = document.getElementById("selSabor1");
    const s2 = document.getElementById("selSabor2");
    
    const p1Nome = s1.value;
    const p1Preco = Number(s1.options[s1.selectedIndex].dataset.preco);
    const p2Nome = s2.value;
    const p2Preco = Number(s2.options[s2.selectedIndex].dataset.preco);

    const precoFinal = Math.max(p1Preco, p2Preco);
    
    const carrinho = getData("carrinho") || [];
    carrinho.push({ nome: `1/2 ${p1Nome} + 1/2 ${p2Nome}`, preco: precoFinal });
    setData("carrinho", carrinho);
    
    renderizarCarrinho();
    fecharModalMeio();
};

// --- CARRINHO ---
function renderizarCarrinho() {
    const lista = document.getElementById("lista");
    const totalEl = document.getElementById("total");
    const carrinho = getData("carrinho") || [];
    
    if (!lista) return;
    lista.innerHTML = carrinho.map(i => `<div style="padding:5px; border-bottom:1px solid #444;">${i.nome} - R$ ${i.preco.toFixed(2)}</div>`).join("");
    
    const total = carrinho.reduce((acc, i) => acc + i.preco, 0);
    totalEl.innerText = `R$ ${total.toFixed(2)}`;
}

window.limparCarrinho = function() {
    setData("carrinho", []);
    renderizarCarrinho();
};

// --- CADASTRO ---
window.salvarProduto = function() {
    const nome = document.getElementById("nome").value;
    const pG = document.getElementById("precoGrande").value;
    const pB = document.getElementById("precoBroto").value;
    const num = document.getElementById("numero").value;

    if (!nome || !pG) return alert("Preencha Nome e Preço Grande!");

    const produtos = getData("produtos") || [];
    produtos.push({ 
        nome, 
        precoGrande: Number(pG), 
        precoBroto: Number(pB), 
        numero: num, 
        tipo: "pizza" 
    });
    
    setData("produtos", produtos);
    renderizarProdutos();
};

// --- INICIALIZAÇÃO ---
window.onload = () => {
    renderizarProdutos();
    renderizarCarrinho();
};