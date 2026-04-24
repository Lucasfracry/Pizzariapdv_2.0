export function registrarVenda(valor,metodo){
  let caixa=JSON.parse(localStorage.getItem("caixaAtual"))
  if(!caixa) return
  caixa.entradas.push({valor,metodo})
  localStorage.setItem("caixaAtual",JSON.stringify(caixa))
}