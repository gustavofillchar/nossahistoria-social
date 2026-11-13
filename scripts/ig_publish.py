"""Publica um post do @nossahistoria.a2 no Instagram pela API oficial.

Sem agendamento: publica o post indicado em posts/gatilho.json (ou passado em --slug),
na hora em que o workflow roda.

Uso:
  python scripts/ig_publish.py prepare [--slug SLUG]
  python scripts/ig_publish.py publish [--slug SLUG] [--dry-run]

posts/gatilho.json: {"slug": "AAAA-MM-DD-tema", "dry_run": false}
Variáveis de ambiente (GitHub Secrets): IG_TOKEN, IG_USER_ID.
1 arte = post de imagem única; 2 a 10 artes = carrossel.
Já publicados ficam em posts/publicados.json, para nunca publicar duas vezes.
"""
import argparse, glob, json, os, sys, time, urllib.error, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.environ.get("GITHUB_REPOSITORY", "gustavofillchar/nossahistoria-social")
RAW = f"https://raw.githubusercontent.com/{REPO}/main/"
LOG = os.path.join(ROOT, "posts", "publicados.json")
TRIGGER = os.path.join(ROOT, "posts", "gatilho.json")
API_VERSION = "v23.0"


def load_post(slug):
    f = os.path.join(ROOT, "posts", f"{slug}.json")
    if not os.path.exists(f):
        sys.exit(f"posts/{slug}.json não encontrado")
    data = json.load(open(f, encoding="utf-8"))
    post = next((p for p in data if p.get("slug") == slug), None) if isinstance(data, list) else None
    if not post:
        sys.exit(f"posts/{slug}.json não tem um post com slug {slug}")
    return post


def slides(slug):
    return sorted(glob.glob(os.path.join(ROOT, "posts", slug, f"{slug}-[0-9][0-9].png")))


def prepare(post):
    from PIL import Image
    out = []
    for png in slides(post["slug"]):
        jpg = png[:-4] + ".jpg"
        if not os.path.exists(jpg):
            Image.open(png).convert("RGB").save(jpg, "JPEG", quality=92, optimize=True)
        out.append(jpg)
    if not out:
        sys.exit(f"Nenhuma arte encontrada em posts/{post['slug']}/")
    print(f"{len(out)} JPEGs prontos para {post['slug']}")


def api(method, path, **params):
    token = os.environ["IG_TOKEN"]
    host = "graph.instagram.com" if token.startswith("IG") else "graph.facebook.com"
    params["access_token"] = token
    url = f"https://{host}/{API_VERSION}/{path}"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url + ("?" + data.decode() if method == "GET" else ""),
                                 data=None if method == "GET" else data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Erro da API do Instagram em {path}: {e.read().decode(errors='replace')}")


def wait_ready(cid):
    for _ in range(30):
        st = api("GET", cid, fields="status_code").get("status_code")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            sys.exit(f"Container {cid} com status {st}: {api('GET', cid, fields='status')}")
        time.sleep(10)
    sys.exit(f"Container {cid} não ficou pronto a tempo")


def publish(post, dry_run):
    log = json.load(open(LOG)) if os.path.exists(LOG) else {}
    if post["slug"] in log:
        print(f"{post['slug']} já foi publicado ({log[post['slug']]['permalink']}). Nada a fazer.")
        return
    uid = os.environ["IG_USER_ID"]
    urls = [RAW + os.path.relpath(p[:-4] + ".jpg", ROOT) for p in slides(post["slug"])]
    if not 1 <= len(urls) <= 10:
        sys.exit(f"O post precisa de 1 a 10 imagens; {post['slug']} tem {len(urls)}")
    caption = post.get("caption", "")
    if len(urls) == 1:
        params = {"image_url": urls[0], "caption": caption}
        if post.get("alt"):
            params["alt_text"] = post["alt"]
        container = api("POST", f"{uid}/media", **params)["id"]
    else:
        children = []
        for k, u in enumerate(urls):
            params = {"image_url": u, "is_carousel_item": "true"}
            if k == 0 and post.get("alt"):
                params["alt_text"] = post["alt"]
            children.append(api("POST", f"{uid}/media", **params)["id"])
        for c in children:
            wait_ready(c)
        container = api("POST", f"{uid}/media", media_type="CAROUSEL",
                        children=",".join(children), caption=caption)["id"]
    wait_ready(container)
    if dry_run:
        print(f"Teste ok: {len(urls)} imagem(ns) aceitas pelo Instagram, mas NÃO publicado (dry run).")
        return
    media_id = api("POST", f"{uid}/media_publish", creation_id=container)["id"]
    link = api("GET", media_id, fields="permalink").get("permalink", "")
    log[post["slug"]] = {"media_id": media_id, "permalink": link,
                         "published_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    json.dump(log, open(LOG, "w"), indent=1, ensure_ascii=False)
    print(f"Publicado: {link}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["prepare", "publish"])
    ap.add_argument("--slug", default="")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    trig = json.load(open(TRIGGER)) if os.path.exists(TRIGGER) else {}
    slug = a.slug or trig.get("slug", "")
    if not slug:
        sys.exit("Nenhum post indicado (posts/gatilho.json vazio e sem --slug).")
    dry = a.dry_run or (not a.slug and bool(trig.get("dry_run")))
    post = load_post(slug)
    prepare(post) if a.step == "prepare" else publish(post, dry)
