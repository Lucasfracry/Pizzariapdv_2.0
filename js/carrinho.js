let carrinho=[]

export function add(i){ carrinho.push(i) }
export function get(){ return carrinho }
export function limpar(){ carrinho=[] }
export function total(){ return carrinho.reduce((t,i)=>t+i.preco,0) }