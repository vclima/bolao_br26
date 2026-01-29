# Instruções para criar repositório GitHub

## 1. Criar repositório no GitHub:
1. Vá para https://github.com
2. Clique em "New repository"
3. Nome do repositório: `bolao_br25`
4. Marque como "Public"
5. NÃO adicione README, .gitignore ou LICENSE (já temos os arquivos)
6. Clique em "Create repository"

## 2. Conectar repositório local ao GitHub:
```cmd
git remote add origin https://github.com/SEU_USUARIO/bolao_br25.git
git branch -M main
git push -u origin main
```

## 3. Executar atualizações automáticas:
- Execute o arquivo `update_bolao.bat` para atualizar o bolão e fazer push automático
- O script irá:
  1. Executar o scraper
  2. Verificar alterações
  3. Adicionar arquivos
  4. Fazer commit com timestamp
  5. Fazer push para o GitHub

## 4. Configurar execução automática (opcional):
- Adicione o `update_bolao.bat` ao Agendador de Tarefas do Windows
- Configure para executar diariamente ou em horários específicos

## Arquivos do projeto:
- `scrape_brasileirao_simple.py` - Script principal
- `bolao.json` - Suas previsões
- `README.md` - Resultados e documentação (atualizado automaticamente)
- `requirements.txt` - Dependências (opcional)
- `update_bolao.bat` - Automação para GitHub
