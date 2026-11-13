"""Renderiza os posts do @nossahistoria.a2.

Uso: python3 -I kit/render_posts.py kit posts/<slug>.json posts/
posts/<slug>.json = [{"slug": "...", "slides": [...], "caption": "...", "alt": "..."}]
Tipos de slide: veja kit/template.html (frase, conversa, capa, item, mensagem, fim).
Gera posts/<slug>/<slug>-NN.png (1080x1350, 4:5).
"""
import sys, json, pathlib
from playwright.sync_api import sync_playwright

kit = pathlib.Path(sys.argv[1]).resolve()
posts = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
out = pathlib.Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)

CHECK = """[...document.querySelectorAll('section')].filter(s=>{
  const b=s.querySelector('.body'), h=s.querySelector('.head').getBoundingClientRect(), f=s.querySelector('.foot').getBoundingClientRect();
  const kids=[...b.querySelectorAll('*')].map(e=>e.getBoundingClientRect()).filter(r=>r.height>0);
  const top=Math.min(...kids.map(r=>r.top)), bot=Math.max(...kids.map(r=>r.bottom)), right=Math.max(...kids.map(r=>r.right));
  return top < h.bottom+16 || bot > f.top-24 || right > s.getBoundingClientRect().right-60
}).map(s=>s.id)"""

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.goto((kit / "template.html").as_uri())
    for post in posts:
        pg.evaluate("p => window.build(p)", post)
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(300)
        loaded = pg.evaluate("[...document.fonts].filter(f=>f.status==='loaded').length")
        assert loaded >= 2, f"fontes não carregaram ({loaded})"
        # auto-ajuste: diminui a fonte (--fs) dos slides que estouram, até 65% do tamanho original
        for _ in range(12):
            bad = pg.evaluate(CHECK)
            if not bad:
                break
            pg.evaluate("""ids => ids.forEach(id => document.querySelectorAll('#'+id+' [style*="--fs"]').forEach(e => {
                const v = parseFloat(e.style.getPropertyValue('--fs')); e.dataset.orig = e.dataset.orig || v;
                if (v > e.dataset.orig*0.65) e.style.setProperty('--fs', (v*0.95)+'px'); }))""", bad)
            pg.wait_for_timeout(50)
        d = out / post["slug"]; d.mkdir(exist_ok=True)
        for old in d.glob(f"{post['slug']}-[0-9][0-9].*"):
            old.unlink()
        n = pg.locator("section.slide").count()
        for i in range(1, n + 1):
            pg.locator(f"#s{i}").screenshot(path=str(d / f"{post['slug']}-{i:02d}.png"))
        print(post["slug"], n, "slides", ("OVERFLOW:" + ",".join(bad)) if bad else "ok")
    b.close()
