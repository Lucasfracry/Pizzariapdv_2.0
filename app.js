import { getData, setData } from './js/db.js';
import { addItem, getCarrinho, limpar, getTotal, removerItem } from './js/carrinho.js';
import { salvarPedido } from './js/pedidoService.js';
import { salvar as salvarNoDB, listarPizzas } from './js/produtoService.js';
import { registrarVenda } from './js/caixaService.js';

// -------------------------------------------------------
// INICIALIZAÇÃO — um único window.onload, sem conflito
// -------------------------------------------------------
window.addEventListener("DOMContentLoaded", () => {
    renderizarProdutos();
    renderizarCarrinho();
    configurarBusca();
    injetarModal();
});

// -------------------------------------------------------
// MODAL MEIO A MEIO — injetado uma única vez via CSS class
// -------------------------------------------------------
function injetarModal() {
    if (document.getElementById("modalMeio")) return;
    const modalHTML = `
    <div id="modalMeio" class="modal-overlay" style="display:none;">
        <div class="modal-box">
            <h2 class="modal-titulo">🍕 Montar Meio a Meio</h2>
            <label>Sabor 1:</label>
            <select id="selSabor1" class="modal-select"></select>
            <label>Sabor 2:</label>
            <select id="selSabor2" class="modal-select"></select>
            <p id="erroMeio" class="modal-erro" style="display:none;">Escolha sabores diferentes!</p>
            <button onclick="confirmarMeioMeio()" class="btn-confirmar-meio">ADICIONAR AO PEDIDO</button>
            <button onclick="fecharModalMeio()" class="btn-cancelar-meio">Cancelar</button>
        </div>
    </div>`;
    document.body.insertAdjacentHTML('beforeend', modalHTML);
}

// -------------------------------------------------------
// NAVEGAÇÃO
// -------------------------------------------------------
window.mostrarTela = function(id) {
    document.querySelectorAll('.tela').forEach(t => t.classList.remove('ativa'));
    document.getElementById(id).classList.add('ativa');
};

// -------------------------------------------------------
// BUSCA POR NÚMERO — campo conectado ao carrinho
// -------------------------------------------------------
function configurarBusca() {
    const input = document.getElementById("buscaNumero");
    if (!input) return;

    input.addEventListener("keydown", (e) => {
        if (e.key !== "Enter") return;
        const num = input.value.trim();
        if (!num) return;

        const produtos = getData("produtos");
        const produto = produtos.find(p => String(p.numero) === num);

        if (produto) {
            escolherTamanho(produto);
            input.value = "";
        } else {
            input.style.borderColor = "#e74c3c";
            setTimeout(() => input.style.borderColor = "", 1000);
        }
    });
}

// -------------------------------------------------------
// ESCOLHER TAMANHO ao adicionar produto
// -------------------------------------------------------
function escolherTamanho(produto) {
    if (produto.precoBroto && produto.precoBroto > 0) {
        const tamanho = confirm(
            `${produto.nome}\n\nGrande: R$ ${Number(produto.precoGrande).toFixed(2)}\nBroto: R$ ${Number(produto.precoBroto).toFixed(2)}\n\nOK = Grande | Cancelar = Broto`
        );
        const preco = tamanho ? produto.precoGrande : produto.precoBroto;
        const label = tamanho ? "G" : "B";
        adicionarAoCarrinho(`${produto.nome} (${label})`, preco);
    } else {
        adicionarAoCarrinho(produto.nome, produto.precoGrande);
    }
}

// -------------------------------------------------------
// RENDERIZAÇÃO DOS PRODUTOS
// -------------------------------------------------------
window.renderizarProdutos = function() {
    const gridPDV = document.getElementById("produtos");
    const gridCadastro = document.getElementById("listaProdutos");
    const produtos = getData("produtos");

    if (gridPDV) {
        gridPDV.innerHTML = "";
        produtos.forEach(p => {
            const card = document.createElement("div");
            card.className = "item-card";
            card.innerHTML = `
                <strong class="item-numero">${p.numero ? p.numero + ' - ' : ''}${p.nome.toUpperCase()}</strong>
                <small>G: R$ ${Number(p.precoGrande).toFixed(2)} | B: R$ ${Number(p.precoBroto || 0).toFixed(2)}</small>
            `;
            card.addEventListener("click", () => escolherTamanho(p));
            gridPDV.appendChild(card);
        });
    }

    if (gridCadastro) {
        gridCadastro.innerHTML = "";
        produtos.forEach((p, i) => {
            gridCadastro.innerHTML += `
                <div class="item">
                    ${p.nome} — R$ ${Number(p.precoGrande).toFixed(2)}
                    <button onclick="excluirProduto(${i})" style="float:right; background:transparent; border:none; color:#e74c3c; cursor:pointer; font-size:16px;">✕</button>
                </div>`;
        });
    }
};

// -------------------------------------------------------
// EXCLUIR PRODUTO DO CADASTRO
// -------------------------------------------------------
window.excluirProduto = function(index) {
    if (!confirm("Remover este produto?")) return;
    const produtos = getData("produtos");
    produtos.splice(index, 1);
    setData("produtos", produtos);
    renderizarProdutos();
};

// -------------------------------------------------------
// ADICIONAR PRODUTO AO CARRINHO
// -------------------------------------------------------
window.adicionarPizzaInteira = function(nome, preco) {
    adicionarAoCarrinho(nome, Number(preco));
};

function adicionarAoCarrinho(nome, preco) {
    addItem({ nome, preco: Number(preco) });
    renderizarCarrinho();
}

// -------------------------------------------------------
// MEIO A MEIO
// -------------------------------------------------------
window.addMeioMeio = function() {
    const pizzas = listarPizzas();
    if (pizzas.length < 2) return alert("Cadastre pelo menos 2 pizzas!");

    const options = pizzas.map(p =>
        `<option value="${p.nome}" data-preco="${p.precoGrande}">${p.nome}</option>`
    ).join("");

    document.getElementById("selSabor1").innerHTML = options;
    document.getElementById("selSabor2").innerHTML = options;
    document.getElementById("erroMeio").style.display = "none";
    document.getElementById("modalMeio").style.display = "flex";
};

window.fecharModalMeio = () => {
    document.getElementById("modalMeio").style.display = "none";
};

window.confirmarMeioMeio = function() {
    const s1 = document.getElementById("selSabor1");
    const s2 = document.getElementById("selSabor2");

    // MELHORIA: impede dois sabores iguais
    if (s1.value === s2.value) {
        document.getElementById("erroMeio").style.display = "block";
        return;
    }

    const p1Nome = s1.value;
    const p1Preco = Number(s1.options[s1.selectedIndex].dataset.preco);
    const p2Nome = s2.value;
    const p2Preco = Number(s2.options[s2.selectedIndex].dataset.preco);
    const precoFinal = Math.max(p1Preco, p2Preco);

    adicionarAoCarrinho(`1/2 ${p1Nome} + 1/2 ${p2Nome}`, precoFinal);
    fecharModalMeio();
};

// -------------------------------------------------------
// CARRINHO
// -------------------------------------------------------
function renderizarCarrinho() {
    const lista = document.getElementById("lista");
    const totalEl = document.getElementById("total");
    if (!lista || !totalEl) return;

    const carrinho = getCarrinho();
    lista.innerHTML = carrinho.length === 0
        ? `<p style="color:#aaa; text-align:center; margin-top:20px;">Carrinho vazio</p>`
        : carrinho.map((item, i) => `
            <div class="item-carrinho">
                <span>${item.nome}</span>
                <span>R$ ${item.preco.toFixed(2)}</span>
                <button onclick="removerDoCarrinho(${i})" class="btn-remover-item">✕</button>
            </div>`
        ).join("");

    totalEl.innerText = `R$ ${getTotal().toFixed(2)}`;
}

window.removerDoCarrinho = function(index) {
    removerItem(index);
    renderizarCarrinho();
};

window.limparCarrinho = function() {
    limpar();
    renderizarCarrinho();
};

// -------------------------------------------------------
// FINALIZAR PEDIDO / IMPRIMIR — função que estava faltando
// -------------------------------------------------------
window.finalizarPedido = function() {
    const carrinho = getCarrinho();
    if (carrinho.length === 0) return alert("O carrinho está vazio!");

    const total = getTotal();
    const metodo = prompt("Forma de pagamento:\n1 - Dinheiro\n2 - Cartão\n3 - Pix");
    const metodos = { "1": "Dinheiro", "2": "Cartão", "3": "Pix" };
    const pagamento = metodos[metodo] || "Não informado";

    const pedido = { itens: [...carrinho], total, pagamento };
    const idPedido = salvarPedido(pedido);
    registrarVenda(total, pagamento);

    // Montar texto de impressão
    const linhas = carrinho.map(i => `${i.nome.padEnd(28)} R$ ${i.preco.toFixed(2)}`).join("\n");
    const recibo = `
=============================
       PDV PIZZARIA
=============================
${linhas}
-----------------------------
TOTAL: R$ ${total.toFixed(2)}
PAGAMENTO: ${pagamento}
=============================
    `;

    const win = window.open("", "_blank", "width=400,height=500");
    win.document.write(`<pre style="font-family:monospace; font-size:14px;">${recibo}</pre>`);
    win.document.close();
    win.print();

    limpar();
    renderizarCarrinho();
};

// -------------------------------------------------------
// CADASTRO DE PRODUTO
// -------------------------------------------------------
window.salvarProduto = function() {
    const nome = document.getElementById("nome").value.trim();
    const pG   = document.getElementById("precoGrande").value;
    const pB   = document.getElementById("precoBroto").value;
    const num  = document.getElementById("numero").value.trim();
    const tipo = document.getElementById("tipo").value;

    if (!nome || !pG) return alert("Preencha pelo menos Nome e Preço Grande!");

    const produto = {
        nome,
        precoGrande: Number(pG),
        precoBroto: Number(pB) || 0,
        numero: num,
        tipo
    };

    salvarNoDB(produto);

    // Limpar campos após salvar
    ["nome", "precoGrande", "precoBroto", "numero"].forEach(id => {
        document.getElementById(id).value = "";
    });

    renderizarProdutos();
};
