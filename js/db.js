export function getData(key) {
    try {
        return JSON.parse(localStorage.getItem(key)) || [];
    } catch (e) {
        console.error("Erro ao ler localStorage:", e);
        return [];
    }
}

export function setData(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
    } catch (e) {
        console.error("Erro ao salvar localStorage:", e);
    }
}
