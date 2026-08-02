# Estado atual — CTX404

Última revisão: 2026-08-02.

## Identidade

- Pasta: `E:\GitHub\projects\ctx404`
- Repositório: `claudneysessa/ctx404`
- Demonstração: https://claudneysessa.github.io/ctx404/
- Branch: `main`
- Versão: `v0.3.0-beta.1`

## Estado validado

- Skill pública para Claude Code, licenciada sob MIT.
- Instaladores para PowerShell e shells Unix-like documentados.
- Bootstrap para repositórios novos e adoção não destrutiva de repositórios existentes.
- Na adoção, o contexto começa na instalação; não há reconstrução automática do passado.
- Contexto local, indexado e versionável; auxilia delegação sem prometer economia automática.
- Landing page pública, documentação bilíngue, 13 testes determinísticos e dois laboratórios reais disponíveis.
- `/init` e recap são apenas orientações manuais após instalar; nunca fazem parte do fluxo automático.
- Adoção detecta autoridades existentes e exige escolha explícita entre índice, exclusivo ou cancelamento antes de escrever.
- Incluído no portfólio pessoal nas categorias `Skills de IA` e `Open Source`.

## Como validar

```text
python -m unittest discover -s tests -v
python -m compileall -q scripts assets/templates/.claude
```

## Último marco

- Commits: `d7f9327` e `0a99787`
- Entrega: adoção segura de projetos existentes e instalação direta sem `/init` automático.

## Próximo passo recomendado

- Reunir feedback de projetos reais por Issues e Pull Requests antes de estabilizar a interface para v1.0.

## Pendências

- Ampliar a matriz de ambientes testados.
- Medir resultados de continuidade e uso de contexto sem transformar observações em promessa de economia.

## Decisões abertas

- Critérios e compatibilidade necessários para sair do beta público.

## Não refazer

- Não apresentar delegação, redução de tokens ou qualidade como garantias.
- Não restaurar o nome anterior; a identidade pública é CTX404.
