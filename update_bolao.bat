@echo off
chcp 65001 > nul
echo ===============================================
echo        Bolao Brasileirao 2025 - Auto Update
echo ===============================================
echo.

echo Mudando para o diretorio do projeto...
cd /d "D:\Documentos\Pyhton Scripts\bolao_br26"
echo PWD atual: %cd%

echo [0/5] Configurando ambiente Python...

REM Primeira tentativa: usar conda do condabin (mais robusto)
where conda >nul 2>&1
if %errorlevel% equ 0 (
    echo Conda encontrado no PATH do sistema
    echo Ativando ambiente 'base'...
    call conda activate
    if %errorlevel% equ 0 (
        echo ✅ Ambiente conda 'base' ativado com sucesso!
        goto :python_ready
    ) else (
        echo ⚠️ Ambiente 'base' nao encontrado
        goto :python_ready
    )
)

REM Segunda tentativa: tentar diferentes caminhos para o conda
echo Conda nao encontrado no PATH, procurando em caminhos padrao...
set "CONDA_PATH="
if exist "%USERPROFILE%\anaconda3\Scripts\activate.bat" (
    set "CONDA_PATH=%USERPROFILE%\anaconda3\Scripts\activate.bat"
    set "CONDA_BASE=%USERPROFILE%\anaconda3"
) else if exist "%USERPROFILE%\miniconda3\Scripts\activate.bat" (
    set "CONDA_PATH=%USERPROFILE%\miniconda3\Scripts\activate.bat"
    set "CONDA_BASE=%USERPROFILE%\miniconda3"
) else if exist "C:\anaconda3\Scripts\activate.bat" (
    set "CONDA_PATH=C:\anaconda3\Scripts\activate.bat"
    set "CONDA_BASE=C:\anaconda3"
)

if not "%CONDA_PATH%"=="" (
    echo Inicializando conda de: %CONDA_PATH%
    call "%CONDA_PATH%" "%CONDA_BASE%"
    call conda activate 2>nul
    if %errorlevel% equ 0 (
        echo ✅ Ambiente conda 'base' ativado!
    )
    goto :python_ready
)

REM Terceira tentativa: usar Python do sistema
echo Conda nao encontrado, verificando Python do sistema...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Python do sistema encontrado
    goto :python_ready
) else (
    echo ❌ ERRO: Nem conda nem Python foram encontrados!
    echo.
    echo Para corrigir:
    echo 1. Instale Anaconda/Miniconda OU
    echo 2. Instale Python e adicione ao PATH OU
    echo 3. Execute este script de dentro do ambiente conda
    pause
    exit /b 1
)

:python_ready
echo.

echo [1/5] Executando script do bolao...
echo Mudando para o diretorio do projeto...

REM Se o primeiro argumento for -f, força atualização ignorando checagem
if "%1"=="-f" (
    python "D:\Documentos\Pyhton Scripts\bolao_br26\scrape_brasileirao_simple.py" force
) else (
    python "D:\Documentos\Pyhton Scripts\bolao_br26\scrape_brasileirao_simple.py"
)
if %errorlevel% neq 0 (
    echo ❌ ERRO: Falha ao executar o script Python
    popd
    pause
    exit /b 1
)
popd

echo.
echo [2/5] Verificando se Git esta configurado...
git config --global user.name > nul 2>&1
if %errorlevel% neq 0 (
    echo AVISO: Configure o Git primeiro:
    echo git config --global user.name "Seu Nome"
    echo git config --global user.email "seu@email.com"
    pause
    exit /b 1
)

echo.
echo [3/5] Verificando alteracoes no Git...
git status

echo.
echo [4/5] Adicionando arquivos alterados...
git add .

echo.
echo [5/5] Fazendo commit e push...
git diff --cached --quiet
if errorlevel 1 (
    echo Alteracoes detectadas. Fazendo commit...
    git commit -m "Atualizacao automatica - %date% %time%"
    if errorlevel 1 (
        echo ERRO: Falha ao fazer commit
        pause
        exit /b 1
    )
    echo Fazendo push para o repositorio remoto...
    git push origin main
    if errorlevel 1 (
        echo ERRO: Falha ao fazer push. Verifique se o repositorio remoto esta configurado.
        echo Execute: git remote add origin https://github.com/vclima/bolao_br26.git
        pause
        exit /b 1
    )
    echo Push realizado com sucesso!
) else (
    echo Nenhuma alteracao detectada. Nada para commitar.
)

echo.
echo ===============================================
echo        Atualizacao concluida!
echo ===============================================
echo.
pause
