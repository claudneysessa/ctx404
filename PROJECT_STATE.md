# Estado atual — CTX404

Última revisão: 2026-08-15.

## Identidade

- Repositório: `claudneysessa/ctx404`
- Demonstração: https://claudneysessa.github.io/ctx404/
- Branch: `main`
- Versão: `v0.4.0-beta.3`

## Estado validado

- Skill pública para Claude Code, licenciada sob MIT.
- Instaladores para PowerShell e shells Unix-like documentados.
- Bootstrap para repositórios novos e adoção não destrutiva de repositórios existentes.
- Na adoção, o contexto começa na instalação; não há reconstrução automática do passado.
- Contexto local, indexado e versionável; auxilia delegação sem prometer economia automática.
- Landing page pública, documentação bilíngue, 35 testes determinísticos e dois laboratórios reais disponíveis.
- `/init` e recap são apenas orientações manuais após instalar; nunca fazem parte do fluxo automático.
- Adoção detecta autoridades existentes e exige escolha explícita entre índice, exclusivo ou cancelamento antes de escrever.
- O CLAUDE.md do usuário recebe só um stub de dois imports; o protocolo mora em `.claude/ctx404-instructions.md` e o detalhe de escrita numa regra com escopo de caminho.
- Tópicos são gravados pelo `context_tool.py topic-write`, não por ferramenta de edição; funciona em sessão não interativa, onde o gate de caminho sensível bloqueia Write em `.claude/`.
- O `settings.json` instalado permite só o helper do CTX404; a regra passa a valer depois que o usuário aceita o diálogo de confiança do workspace, que a skill agora orienta explicitamente.
- O upgrade atualiza os arquivos gerenciados de implementação junto com o protocolo, para o helper instalado não ficar atrás da regra que ele deve seguir.
- Migração encadeada 0.2.0 → 0.3.0 → 0.4.0-beta.1 → beta.2 → beta.3 remove o bloco antigo do CLAUDE.md e preserva a definição editada. Versão publicada nunca sai da cadeia: `pending_hops` recusa versão instalada que não reconhece.
- Escrever contexto virou hook, não pedido: `context_gate.py` (Stop) bloqueia uma vez a sessão que deliberou sem registrar, e `context_tool.py review` lê a deliberação de volta por seção, consulta ou tópico.
- `prepare` recusa instalar quando o Git ignora `.claude/context/`, nomeando a regra exata e a receita de substituição; não existe "instalar mesmo assim".
- Instalação tem recibo dentro do diretório Git e fase `revert` que desfaz exatamente o que criou.
- Instalar e atualizar só valem na sessão seguinte. O relatório termina com banner de asteriscos exigindo reinício, porque a linha discreta anterior já custou horas de trabalho não registrado num projeto real.
- Incluído no portfólio pessoal nas categorias `Skills de IA` e `Open Source`.

## Como validar

```text
python -m unittest discover -s tests -v
python -m compileall -q scripts assets/templates/.claude
```

## Último marco

- Entrega: `v0.4.0-beta.3`, banner de reinício nos relatórios de install e upgrade, com hop revisado a partir da beta.2 verificado ponta a ponta.
- Entrega anterior: protocolo fora do CLAUDE.md (7.895 → 559 chars num upgrade real) e carga sempre-ativa de ~1.900 para ~990 tokens por sessão.
- Verificado em sessões `claude -p` isoladas nos três laboratórios reconstruídos do zero: imports carregam sem ferramenta, a regra com escopo só entra ao tocar `.claude/context/`, e tópicos são gravados em sessão não interativa.

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
