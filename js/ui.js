import { getData, setData } from './db.js'
import { add, get, limpar, total } from './carrinho.js'

let modoMeio = false
let primeiraPizza = null

/* ================= TELA ================= */
export function mostrarTela(tela) {
  document.querySelectorAll('.tela').forEach(t => t.classList.remove('ativa'))
  document.getElementById(tela).classList.add('ativa')

  if (tela === "cadastro") {
    carregarListaProdutos()
    atualizarFormulario()
  }
}

/* ================= MEIO A MEIO ================= */
export function addMeioMeio() {
  modoMeio = true
  primeiraPizza = null

  alert("Selecione o PRIMEIRO sabor")
}

/* ================= PRODUTOS ================= */
function carregarProdutos() {
  const produtos = getData("produtos")
  const c = document.getElementById("produtos")
  c.innerHTML = ""

  produtos.forEach(p => {
    if (p.tipo === "pizza") {
      c.innerHTML += `
        <div class="item" onclick='addProduto(${JSON.stringify(p)})'>
          <div class="numero">${p.numero}</div>
          <div>${p.nome}</div>
        </div>
      `
    }
  })
}

/* ================= CLIQUE PRODUTO ================= */
export function addProduto(p) {

  // MODO MEIO A MEIO
  if (modoMeio) {

    if (!primeiraPizza) {
      primeiraPizza = p
      alert("Agora selecione o SEGUNDO sabor")
      return
    }

    // segunda pizza
    const preco = Math.max(
      primeiraPizza.precoGrande,
      p.precoGrande
    )

    add({
      meio: true,
      sabores: [primeiraPizza, p],
      preco
    })

    modoMeio = false
    primeiraPizza = null

    render()
    return
  }

  // NORMAL
  const preco = p.precoGrande || p.preco
  add({ ...p, preco })
  render()
}

/* ================= DIGITAR NUMERO ================= */
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("buscaNumero").addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      const num = e.target.value
      const p = getData("produtos").find(x => x.numero == num)
      if (p) addProduto(p)
      e.target.value = ""
    }
  })
})

/* ================= RENDER ================= */
function render() {
  const lista = document.getElementById("lista")
  lista.innerHTML = ""

  get().forEach(i => {
    let nome = i.meio
      ? `1/2 ${i.sabores[0].nome} / 1/2 ${i.sabores[1].nome}`
      : `${i.numero || ""} ${i.nome}`

    lista.innerHTML += `<div>${nome} - R$${i.preco}</div>`
  })

  document.getElementById("total").innerText =
    "R$ " + total().toFixed(2)
}

/* ================= PEDIDO ================= */
export function finalizarPedido() {
  window.print()
  limpar()
  render()
}

export function limparCarrinho() {
  limpar()
  render()
}

/* ================= CADASTRO ================= */
function atualizarFormulario() {
  const tipo = document.getElementById("tipo").value

  const numero = document.getElementById("numero")
  const precoGrande = document.getElementById("precoGrande")
  const precoBroto = document.getElementById("precoBroto")
  const preco = document.getElementById("preco")

  if (tipo === "pizza") {
    numero.style.display = "block"
    precoGrande.style.display = "block"
    precoBroto.style.display = "block"
    preco.style.display = "none"
  } else {
    numero.style.display = "none"
    precoGrande.style.display = "none"
    precoBroto.style.display = "none"
    preco.style.display = "block"
  }
}

export function salvarProduto() {
  const produtos = getData("produtos")
  const tipo = document.getElementById("tipo").value

  let produto

  if (tipo === "pizza") {
    produto = {
      tipo,
      numero: document.getElementById("numero").value,
      nome: document.getElementById("nome").value,
      precoGrande: Number(document.getElementById("precoGrande").value),
      precoBroto: Number(document.getElementById("precoBroto").value)
    }
  } else {
    produto = {
      tipo,
      nome: document.getElementById("nome").value,
      preco: Number(document.getElementById("preco").value)
    }
  }

  produtos.push(produto)
  setData("produtos", produtos)

  carregarListaProdutos()
  carregarProdutos()
}

function carregarListaProdutos() {
  const lista = document.getElementById("listaProdutos")
  const produtos = getData("produtos")

  lista.innerHTML = ""

  produtos.forEach(p => {
    lista.innerHTML += `
      <div class="item">
        ${p.numero ? p.numero + " - " : ""}${p.nome}
      </div>
    `
  })
}

/* INIT */
window.onload = carregarProdutos