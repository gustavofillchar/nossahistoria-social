# Esteira do @nossahistoria.a2

Página romântica de casal no Instagram. Posts só quando o dono pedir (sem agendamento).

## Formatos
- **Post de imagem/carrossel:** `kit/template.html` + `kit/render_posts.py` (1080x1350).
- **Reel com vídeo único:** `kit/reels/render_reel.py` (máscara, grão, frase em 2 tempos).
- **Reel em motion (o preferido):** `kit/reels/render_motion.py`. Cenas `textura` (papel creme ou `"theme":"dark"` vinho, granulado),
  `video` e `foto`, com a frase aparecendo palavra por palavra. Alternar: alguns reels só com texturas (`"grain": 12-16` para bem granulado),
  outros com vídeos/fotos intercalados. Mínimo ~15 s.
- **Música:** baixinha de fundo (`"music": {"src": ..., "volume": 0.2}`; sem voz, use ~0.6-0.8). Uns 2 s de música antes do primeiro texto
  e uns 2-3 s no fim.
- **Voz (pausado):** `scripts/gerar_voz.py` + Action "Gerar voz" (ElevenLabs). Voz escolhida `oJebhZNaPllxk6W0LSBA` precisa de plano pago.
  Não usar enquanto o dono não pedir.

## Textos
Banco em `frases/banco.md` (ler antes de escrever; marcar `[usada AAAA-MM-DD]` ao postar; acrescentar frases boas que encontrar).
Frases românticas conhecidas no Brasil (pesquisar em portais brasileiros) ou originais no mesmo estilo. Nunca tradução literal do inglês,
nunca letra de música nem trecho de poeta com direitos (Vinicius, Quintana, Neruda etc.). Nada sexual explícito.

## Mídia
- Pasta local do dono: `~/Movies/nossahistoria-midia/` (`videos/`, `musicas/`, `prontos/`). Ler pelo computador vinculado.
- **Vídeo usado = renomear com prefixo `usado-`** (ex.: `usado-6319577-...mp4`). Preferir vídeos sem o prefixo.
- Fotos do Unsplash (chave de desenvolvedor, limite de 50 requisições/hora contando buscas e downloads): **usar primeiro as fotos
  que já estão em `fotos/`**; só pedir novas quando faltar o tema, no máximo 2-3 buscas por vez e `n` até 5. Nada de varrer o acervo.
  Foto usada: anotar em `fotos/usadas.json` (`{"casal-idoso-6": "AAAA-MM-DD"}`). Para pedir: adicione `{"nome": {"query": "...", "orientation": "portrait", "n": 4}}` em `fotos/pedidos.json` e dê push;
  a Action "Fotos do Unsplash" baixa em `fotos/<nome>-N.jpg` (créditos em `fotos/creditos.json`).
- Reel finalizado: copiar para `prontos/` na pasta do dono e mandar o vídeo na conversa.

## Publicar (só com pedido explícito)
Reel: `posts/<slug>/<slug>.mp4` + `posts/<slug>.json` (`caption`, `alt`, `thumb_offset` em ms). Imagens: `posts/<slug>/<slug>-NN.png`.
Depois `posts/gatilho.json` = `{"slug": "<slug>", "dry_run": false}` e push: a Action "Publicar no Instagram" publica e registra em
`posts/publicados.json`. Acompanhar com `gh run list/view` e devolver o link.
