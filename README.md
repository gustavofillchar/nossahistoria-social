# nossahistoria-social

Esteira de conteúdo do Instagram **@nossahistoria.a2** (frases, declarações e humor de casal).
As artes em `posts/` são públicas de propósito: a API do Instagram baixa as imagens por URL.

## Como funciona
1. No Claude, peça um post ("cria e publica um post de frase", "faz um carrossel manda isso pra ele").
2. O Claude escreve `posts/<slug>.json`, renderiza `posts/<slug>/<slug>-NN.png`, atualiza `posts/gatilho.json` e dá push.
3. O push no `gatilho.json` dispara a Action **Publicar no Instagram**, que publica na hora. Não há agendamento.

- 1 arte = post de imagem única; 2 a 10 = carrossel. Formato 1080x1350 (4:5).
- `posts/publicados.json` guarda o que já saiu (nunca publica o mesmo slug duas vezes).
- Teste sem publicar: aba Actions → Publicar no Instagram → Run workflow, com "dry run" marcado.

## Kit
- `kit/template.html`: identidade visual (creme, vinho e rosé; Lora + Poppins). Tipos de slide: `frase`, `conversa`, `capa`, `item`, `mensagem`, `fim`.
- `kit/render_posts.py`: `python3 -I kit/render_posts.py kit posts/<slug>.json posts/` (Playwright + Chromium). Reduz a fonte sozinho se o texto estourar.
- `kit/fonts/`: Lora e Poppins (SIL Open Font License).
- `exemplos/exemplo.json`: um post de cada tipo.

## Secrets do repositório (Settings → Secrets and variables → Actions)
- `IG_TOKEN`: token de longa duração da API do Instagram (começa com `IG...` no login do Instagram, ou `EAA...` no login do Facebook).
- `IG_USER_ID`: id da conta profissional do @nossahistoria.a2.
