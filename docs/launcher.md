# Launcher do Citric

O launcher GTK 4 inicia Roblox Studio com scripts/run-studio.sh. Ele também pode preparar o runtime quando o checkout ainda não tem bin/rosemary.

## Abrir

Execute ./scripts/citric para abrir a interface ou python3 -m citric_launcher na raiz do repositório.

A janela permite iniciar o Studio ou uma place .rbxl/.rbxlx, compilar o Rosemary a partir da série de patches, escolher prefixo, executável Rosemary, bundle do Studio e driver SDL, salvar preferências XDG, instalar o atalho de menu e abrir a pasta de logs.

Na primeira instalação, clique em Baixar patches e compilar Rosemary. Isso busca a base fixada, aplica patches/series, compila e grava bin/rosemary. O bundle proprietário ainda precisa estar disponível em app/ ou ser selecionado manualmente.

## CLI

    ./scripts/citric build
    ./scripts/citric build --check-only
    ./scripts/citric build --build-only
    ./scripts/citric launch
    ./scripts/citric launch "/caminho/para/place.rbxl"
    ./scripts/citric launch --dry-run
    ./scripts/citric diagnose
    ./scripts/citric install-desktop
    ./scripts/citric uninstall-desktop

build --check-only valida a revisão-base e os patches sem compilar. diagnose verifica caminhos locais sem iniciar o Studio. launch --dry-run mostra os argumentos e as variáveis que seriam passados ao wrapper.

## Preferências e arquivos locais

As preferências ficam em $XDG_CONFIG_HOME/citric/launcher.json, ou em ~/.config/citric/launcher.json. Os logs ficam em logs/ no checkout. O source temporário e o target Cargo ficam em $XDG_CACHE_HOME/citric ou ~/.cache/citric. O executável gerado em bin/rosemary, app/full/RobloxStudio.app e downloads/darwin-cache estão excluídos do Git.

## Dependências

A interface precisa de Python 3, PyGObject e GTK 4. O build do Rosemary precisa de Git, Rust/Cargo e as dependências upstream exigidas pela revisão fixada. O script chama Cargo no source preparado e mantém toda a configuração de runtime em scripts/run-studio.sh.
