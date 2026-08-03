import React, { useState, useEffect } from 'react';
import { Trash2, CheckCircle, XCircle, Package } from 'lucide-react'; // Instale caso não tenha: npm install lucide-react

export default function GestaoDTF() {
  const [vendas, setVendas] = useState([]);
  const [buscaCliente, setBuscaCliente] = useState('');
  const [filtroStatus, setFiltroStatus] = useState('Todos');

  // Formular Novo Lançamento
  const [novoLancamento, setNovoLancamento] = useState({
    cliente: '',
    produto: '',
    valor: '',
    dtfPronto: false,
    statusPagamento: 'Não Pago'
  });

  // Função para salvar nova venda (Simulação da API conectada ao Neon via GitHub)
  const handleSalvarVenda = async (e) => {
    e.preventDefault();
    if (!novoLancamento.cliente || !novoLancamento.produto || !novoLancamento.valor) return;

    const novaVenda = {
      id: Date.now(), // No Neon será o SERIAL ID
      data: new Date().toLocaleDateString('pt-BR'),
      ...novoLancamento,
      valor: parseFloat(novoLancamento.valor)
    };

    setVendas([novaVenda, ...vendas]);
    // Resetar campos essenciais mantendo o cliente se quiser lançar vários itens
    setNovoLancamento({ ...novoLancamento, produto: '', valor: '', dtfPronto: false, statusPagamento: 'Não Pago' });
  };

  // Função para Deletar Registro (Ação da Lixeira)
  const handleExcluir = async (id) => {
    if (window.confirm("Tem certeza que deseja excluir este registro?")) {
      setVendas(vendas.filter(venda => venda.id !== id));
      // Aqui você adicionará o fetch('/api/vendas/' + id, { method: 'DELETE' })
    }
  };

  // Alternar Status de Pagamento com um clique
  const alternarPagamento = (id) => {
    setVendas(vendas.map(v => v.id === id ? { ...v, statusPagamento: v.statusPagamento === 'Pago' ? 'Não Pago' : 'Pago' } : v));
  };

  // Alternar Status de Retirada/Pronto com um clique
  const alternarRetirada = (id) => {
    setVendas(vendas.map(v => v.id === id ? { ...v, dtfPronto: !v.dtfPronto } : v));
  };

  // Filtragem Dinâmica de Clientes e Status
  const vendasFiltradas = vendas.filter(venda => {
    const bateCliente = venda.cliente.toLowerCase().includes(buscaCliente.toLowerCase());
    const bateStatus = filtroStatus === 'Todos' || venda.statusPagamento === filtroStatus;
    return bateCliente && bateStatus;
  });

  // Cálculos de Caixa do Filtro Atual
  const totalDevido = vendasFiltradas.filter(v => v.statusPagamento === 'Não Pago').reduce((acc, v) => acc + v.valor, 0);
  const totalFaturadoDia = vendas.filter(v => v.data === new Date().toLocaleDateString('pt-BR')).reduce((acc, v) => acc + v.valor, 0);

  return (
    <div className="p-6 bg-gray-50 min-h-screen font-sans">
      {/* 📊 Cabeçalho de Indicadores */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <p className="text-gray-500 text-xs font-bold uppercase">Faturamento Diário (Hoje)</p>
          <p className="text-2xl font-bold text-green-600">R$ {totalFaturadoDia.toFixed(2)}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border">
          <p className="text-gray-500 text-xs font-bold uppercase">Extrato Mensal</p>
          <button className="mt-1 px-4 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 transition">
            Ver Relatório Mensal
          </button>
        </div>
      </div>

      {/* 📝 Formulário de Novo Lançamento de Venda */}
      <div className="bg-white p-6 rounded-lg shadow-sm border mb-6">
        <h2 className="text-lg font-bold mb-4 text-gray-700">Novo Lançamento de Venda</h2>
        <form onSubmit={handleSalvarVenda} className="grid grid-cols-1 md:grid-cols-5 gap-4 items-end">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Cliente *</label>
            <input 
              type="text" 
              placeholder="Nome do cliente"
              className="w-full p-2 border rounded text-sm"
              value={novoLancamento.cliente}
              onChange={e => setNovoLancamento({...novoLancamento, cliente: e.target.value})}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Produto / Tabela DTF *</label>
            <select 
              className="w-full p-2 border rounded text-sm"
              value={novoLancamento.produto}
              onChange={e => setNovoLancamento({...novoLancamento, produto: e.target.value})}
            >
              <option value="">Selecione o DTF</option>
              <option value="DTF Metro Linear - Tabela A">DTF Metro Linear - Tabela A</option>
              <option value="DTF Metro Linear - Tabela B">DTF Metro Linear - Tabela B</option>
              <option value="DTF Imagem Avulsa">DTF Imagem Avulsa</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Valor (R$) *</label>
            <input 
              type="number" 
              step="0.01"
              placeholder="0,00"
              className="w-full p-2 border rounded text-sm"
              value={novoLancamento.valor}
              onChange={e => setNovoLancamento({...novoLancamento, valor: e.target.value})}
            />
          </div>
          <div className="flex gap-4 mb-2">
            <label className="flex items-center text-sm gap-1.5 cursor-pointer">
              <input 
                type="checkbox" 
                checked={novoLancamento.dtfPronto} 
                onChange={e => setNovoLancamento({...novoLancamento, dtfPronto: e.target.checked})}
              />
              DTF Pronto/Retirado
            </label>
          </div>
          <button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-700 text-white p-2 rounded font-medium text-sm transition">
            + Adicionar Item
          </button>
        </form>
      </div>

      {/* 🔍 Área de Busca e Fila de Pedidos */}
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <h2 className="text-lg font-bold mb-4 text-gray-700">Fila de Pedidos e Histórico</h2>
        
        {/* Filtros */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Procurar por Cliente</label>
            <input 
              type="text" 
              placeholder="Digite o nome do cliente para ver tudo..."
              className="w-full p-2 border rounded text-sm"
              value={buscaCliente}
              onChange={e => setBuscaCliente(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Filtrar Status Financeiro</label>
            <select 
              className="w-full p-2 border rounded text-sm"
              value={filtroStatus}
              onChange={e => setFiltroStatus(e.target.value)}
            >
              <option value="Todos">Todos os Pedidos (Pagos e Não Pagos)</option>
              <option value="Não Pago">Apenas Não Pagos (Em aberto)</option>
              <option value="Pago">Apenas Pagos</option>
            </select>
          </div>
          {/* Card Dinâmico de Dívida do Cliente */}
          {buscaCliente && (
            <div className="bg-red-50 border border-red-200 p-2.5 rounded flex flex-col justify-center">
              <span className="text-xs text-red-700 font-bold uppercase">Total Devido por {buscaCliente}:</span>
              <span className="text-xl font-black text-red-600">R$ {totalDevido.toFixed(2)}</span>
            </div>
          )}
        </div>

        {/* 📋 Tabela de Resultados */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="bg-gray-100 text-gray-700 uppercase text-xs border-b">
                <th className="p-3">Data</th>
                <th className="p-3">Cliente</th>
                <th className="p-3">Produto/Tabela DTF</th>
                <th className="p-3">Valor</th>
                <th className="p-3 text-center">Entrega/Retirada</th>
                <th className="p-3 text-center">Status Financeiro</th>
                <th className="p-3 text-center">Ações</th>
              </tr>
            </thead>
            <tbody>
              {vendasFiltradas.length === 0 ? (
                <tr>
                  <td colSpan="7" className="p-4 text-center text-gray-400">Nenhum registro encontrado.</td>
                </tr>
              ) : (
                vendasFiltradas.map((venda) => (
                  <tr key={venda.id} className="border-b hover:bg-gray-50 transition">
                    <td className="p-3 text-gray-500">{venda.data}</td>
                    <td className="p-3 font-semibold text-gray-800">{venda.cliente}</td>
                    <td className="p-3 text-gray-600">{venda.produto}</td>
                    <td className="p-3 font-medium text-gray-900">R$ {venda.valor.toFixed(2)}</td>
                    
                    {/* Botão de Retirada Rápida */}
                    <td className="p-3 text-center">
                      <button 
                        onClick={() => alternarRetirada(venda.id)}
                        className={`px-3 py-1 rounded-full text-xs font-bold transition flex items-center gap-1 mx-auto ${
                          venda.dtfPronto ? 'bg-blue-100 text-blue-700' : 'bg-amber-100 text-amber-700'
                        }`}
                      >
                        <Package size={14} />
                        {venda.dtfPronto ? 'Retirado' : 'Pronto p/ Retirar'}
                      </button>
                    </td>

                    {/* Botão de Status Financeiro Rápido */}
                    <td className="p-3 text-center">
                      <button 
