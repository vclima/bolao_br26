# Bolão Brasileirão 2025 - Projeto Completo

## 🎯 Resumo do Projeto
Sistema automatizado para acompanhar o bolão do Brasileirão 2025, comparando palpites com a classificação real e calculando pontuações.

## 📁 Arquivos do Projeto

### 1. `scrape_brasileirao_simple.py`
- **Função**: Script principal que faz scraping da classificação atual
- **Recursos**:
  - Scraping de ESPN Brasil (principal) e GE Globo (backup)
  - Normalização de nomes de times
  - Comparação com palpites em `bolao.json`
  - Cálculo de pontuações
  - **Detecção de mudanças** - só atualiza README se a classificação mudou
  - Salva classificação atual em `last_standings.json` para comparação
  - Atualização automática do README
  - Saída em português

### 2. `bolao.json`
- **Função**: Armazena os palpites de cada participante
- **Formato**: JSON com times e posições previstas
- **Participantes atuais**: Victor, Julio, Luca

### 3. `README.md`
- **Função**: Documentação e resultados atualizados automaticamente
- **Recursos**:
  - Tabela de resultados no topo
  - Ranking final por pontuação
  - Timestamp da última atualização
  - Documentação completa em português

### 4. `update_bolao.bat`
- **Função**: Automação para Windows
- **Recursos**:
  - Executa o script Python
  - Verifica configuração do Git
  - Adiciona arquivos alterados
  - Faz commit com timestamp
  - Push automático para GitHub
  - Tratamento de erros

### 5. `requirements.txt`
- **Função**: Lista de dependências (opcional, usa apenas bibliotecas padrão)

### 6. `SETUP_GITHUB.md`
- **Função**: Instruções para configurar repositório GitHub

## 🚀 Como Usar

### Primeira Vez:
1. Configure o Git:
   ```cmd
   git config --global user.name "Seu Nome"
   git config --global user.email "seu@email.com"
   ```

2. Crie o repositório GitHub:
   - Vá para https://github.com
   - Crie novo repositório público: `bolao_br25`
   - Não adicione README/LICENSE (já temos)

3. Conecte o repositório local:
   ```cmd
   git remote add origin https://github.com/SEU_USUARIO/bolao_br25.git
   git branch -M main
   git push -u origin main
   ```

### Uso Regular:
- Execute `update_bolao.bat` para atualizar tudo automaticamente
- Ou execute manualmente: `python scrape_brasileirao_simple.py`

## 🏆 Sistema de Pontuação
- **Acerto exato**: 20 pontos
- **Diferença de 1 posição**: 19 pontos
- **Diferença de 2 posições**: 18 pontos
- **E assim por diante** (mínimo 1 ponto)

## 📊 Fontes de Dados
1. **ESPN Brasil** (principal): https://www.espn.com.br/futebol/classificacao/_/liga/bra.1
2. **GE Globo** (backup): https://ge.globo.com/futebol/brasileirao/

## 🔧 Personalização
- Edite `bolao.json` para adicionar/remover participantes
- Modifique a função `calculate_score()` para alterar sistema de pontuação
- Ajuste `update_readme()` para mudar formato de saída

## 📅 Automação
- Configure execução diária no Agendador de Tarefas do Windows
- O script atualiza automaticamente o README com resultados
- Push automático mantém o GitHub sempre atualizado

## 🔍 Troubleshooting
- **Erro de scraping**: Verifica automaticamente fontes alternativas
- **Erro de Git**: Batch file verifica configuração
- **Nomes não encontrados**: Sistema de normalização robusto

## 📈 Funcionalidades Futuras
- [ ] Histórico de classificações
- [ ] Gráficos de evolução
- [ ] Notificações por email
- [ ] API para consultas externas

---
**Projeto criado em:** 2025-07-17  
**Última atualização:** 2025-07-17 21:05:43  
**Status:** ✅ Funcionando completamente
