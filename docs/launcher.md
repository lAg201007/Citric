# Launcher do Citric

O launcher GTK 4 inicia o Roblox Studio usando o wrapper existente `scripts/run-studio.sh`. Ele não baixa nem atualiza o Studio, o runtime Rosemary ou places. O bundle proprietário continua fora do Git.

## Abrir

Execute `./scripts/citric` para abrir a interface, ou `python3 -m citric_launcher` a partir da raiz do repositório.

A janela permite:

- iniciar o Studio ou abrir diretamente um arquivo `.rbxl` / `.rbxlx`;
- escolher prefixo, executável Rosemary, bundle do Studio e driver SDL;
- salvar as preferências no XDG config;
- adicionar ou remover a entrada do menu de aplicativos;
- abrir a pasta local de logs.

O padrão do driver SDL continua sendo X11, como no wrapper de testes atual.

## CLI

```sh
./scripts/citric launch
./scripts/citric launch "/caminho/para/place.rbxl"
./scripts/citric launch --dry-run
./scripts/citric diagnose
./scripts/citric install-desktop
./scripts/citric uninstall-desktop
```

`diagnose` verifica os caminhos necessários sem iniciar o Studio. O modo `--dry-run` imprime os argumentos e variáveis que seriam passados ao wrapper.

## Preferências

O arquivo fica em `$XDG_CONFIG_HOME/citric/launcher.json`, ou em `~/.config/citric/launcher.json` quando `XDG_CONFIG_HOME` não estiver definido. O launcher cria esse arquivo com permissão 0600. Os logs continuam em `logs/` no checkout para manter o comportamento documentado do wrapper.

## Dependências

A interface precisa de Python 3, PyGObject e GTK 4. A entrada .desktop é instalada no diretório `applications` sob `$XDG_DATA_HOME`, ou em `~/.local/share/applications` por padrão.

O launcher apenas chama o wrapper do projeto. A configuração do prefixo, o patch do diálogo de cor, a escolha do Rosemary e a gravação dos logs permanecem centralizados em `scripts/run-studio.sh`.
