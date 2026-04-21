# Alfred — Base de Conhecimento

Este arquivo é lido pelo Alfred para orientar a análise de qualquer sistema web.
Ele define padrões de raciocínio, priorização e cobertura de testes.

---

## Tipos de Sistema e Fluxos Críticos

### Sistema de Delivery / Pedidos
- Fluxos críticos: criação de pedido, confirmação, atualização de status, cancelamento
- Perfis típicos: admin, cliente, motorista/entregador
- Riscos principais: sincronização de status entre perfis, cálculo de valores, notificações

### Admin Panel / Backoffice
- Fluxos críticos: CRUD de entidades (criar, editar, excluir), filtros, exportação
- Riscos: deleção sem confirmação, permissões entre roles, dados sensíveis expostos

### E-commerce
- Fluxos críticos: carrinho, checkout, pagamento, histórico de compras
- Riscos: estoque desatualizado, cálculo de frete/desconto, falha no pagamento

### SaaS / Plataforma
- Fluxos críticos: onboarding, configuração de conta, planos/billing, integrações
- Riscos: limites de plano, dados de outros tenants vazando, cancelamento de conta

### Portal do Funcionário / RH
- Fluxos críticos: registro de ponto, solicitações, aprovações, histórico
- Riscos: cálculo de horas, fluxo de aprovação quebrado, permissões por hierarquia

---

## Regras de Prioridade

**Alta** — use quando:
- A funcionalidade impacta fluxo de receita ou operação principal
- Falha causa perda de dados ou estado inconsistente
- Afeta autenticação, autorização ou dados sensíveis
- É o único caminho para completar uma tarefa crítica

**Média** — use quando:
- Funcionalidade importante mas com caminho alternativo
- Afeta experiência mas não bloqueia o uso
- Validações de formulário, mensagens de erro, feedback visual

**Baixa** — use quando:
- Conteúdo estático, textos, links informativos
- Funcionalidades acessórias ou de conveniência
- Formatação visual, responsividade não crítica

---

## Cobertura por Tipo de Elemento

### Formulario com campos
- Happy path com dados válidos
- Campo obrigatorio vazio (cada um separadamente se crítico)
- Formato inválido (email sem @, CPF com letras, data futura onde não cabe)
- Limite de caracteres (campo muito longo)
- Duplo clique no submit / submit com loading
- Comportamento após sucesso (redirect, mensagem, limpeza do form)
- Comportamento após erro da API (mensagem de erro visível)

### Tabela / Lista
- Exibição com dados preenchidos
- Estado vazio (zero registros)
- Filtro/busca com resultado encontrado
- Filtro/busca sem resultado
- Ordenação por coluna (se disponível)
- Ação por linha: editar redireciona corretamente
- Ação por linha: excluir abre confirmação antes de agir
- Paginação (se houver)

### Detalhe / Visualizacao
- Todos os campos exibidos corretamente
- Transições de status (se houver botoes de mudanca de estado)
- Dados de outros registros nao aparecem (isolamento)
- Navegacao de volta funciona

### Modal / Dialog
- Abre ao clicar no trigger correto
- Fecha ao clicar em cancelar / fora do modal
- Acao destrutiva exige confirmacao antes de executar
- Estado do fundo (overlay) nao bloqueia outros elementos apos fechar

### Login / Autenticacao
- Credenciais válidas -> acesso correto ao perfil
- Credenciais inválidas -> mensagem de erro sem expor detalhes
- Campo obrigatório vazio -> feedback visual
- Redirecionamento após login aponta para tela correta por perfil
- Logout limpa sessão e redireciona para login

---

## O que Nao Gerar

- Casos de teste para funcionalidades nao observadas nos elementos coletados
- CTs genéricos como "verificar se a pagina carrega" sem contexto
- Riscos vagos como "pode haver problemas de performance"
- Mais de 12 CTs por pagina (exceto telas com muitos formulários complexos)
- CTs duplicados entre paginas diferentes

---

## Formato de Saida Esperado por Pagina

```
### Resumo da Pagina
[2-3 frases: proposito, quem usa, acao principal habilitada]

### Casos de Teste

| # | Cenario | Pre-condicao | Passos | Resultado Esperado | Prioridade |
|---|---------|-------------|--------|--------------------|-----------|
| CT-01 | ... | ... | ... | ... | Alta |

### Riscos e Pontos de Atencao
- [risco concreto baseado nos elementos observados]
```

---

## Resumo do Sistema (ao final)

O resumo deve responder:
1. Que tipo de sistema e esse? Para quem? Qual problema resolve?
2. Quais perfis de usuario existem e o que cada um faz?
3. Quais sao os 3-5 fluxos mais criticos para cobrir com testes?
4. Quais sao os 3 maiores riscos de qualidade identificados?
5. Por onde comecar os testes e por que?
