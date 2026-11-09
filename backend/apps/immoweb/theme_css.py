"""OMNIA themes — CSS blocks (MOVE-ONLY from theme_render)."""
from __future__ import annotations

from typing import Any, Dict

def _theme_css(cfg: Dict[str, Any]) -> str:
    """Generate the shared CSS-vars block + theme-specific overrides."""
    pal = cfg["palette"]
    typ = cfg["typography"]
    theme_id = cfg["theme_id"]

    base = f"""
    :root {{
      --o-primary: {pal['primary']};
      --o-accent: {pal['accent']};
      --o-dark: {pal['neutral_dark']};
      --o-light: {pal['neutral_light']};
      --o-font-headings: {typ['headings']};
      --o-font-body: {typ['body']};
    }}
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:var(--o-font-body);color:var(--o-dark);background:var(--o-light);line-height:1.55}}
    a{{color:var(--o-primary);text-decoration:none}}
    a:hover{{opacity:.85}}
    h1,h2,h3{{font-family:var(--o-font-headings);font-weight:600;letter-spacing:-.01em}}
    .container{{max-width:1180px;margin:0 auto;padding:24px}}
    footer{{margin-top:3rem;padding:24px;text-align:center;color:#78716c;font-size:.85rem;border-top:1px solid rgba(0,0,0,.08)}}
    img{{max-width:100%;display:block}}
    """

    if theme_id == "minimal":
        return base + """
        header{background:transparent;padding:32px 0 16px}
        header .container{display:flex;align-items:center;gap:16px}
        .brand-logo{height:36px;width:auto}
        .brand-name{font-family:var(--o-font-headings);font-size:1.25rem;color:var(--o-dark)}
        h1{font-size:2.6rem;line-height:1.1;margin:2rem 0 .8rem}
        h2{font-size:1.4rem;margin:2rem 0 1rem}
        .price{font-size:2rem;font-weight:600;color:var(--o-accent)}
        .meta{color:#78716c;font-size:.9rem;margin-bottom:1.2rem}
        .listings{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;margin-top:1.5rem}
        .listings a{background:#fff;border:1px solid rgba(0,0,0,.08);border-radius:4px;overflow:hidden;transition:border .2s}
        .listings a:hover{border-color:var(--o-primary)}
        .listings img{height:200px;width:100%;object-fit:cover}
        .listings .body{padding:14px}
        .listings .body h3{font-size:1.05rem;margin-bottom:.3rem}
        .listings .body p{color:#78716c;font-size:.85rem;margin-bottom:.4rem;font-family:var(--o-font-body)}
        .listings .body strong{color:var(--o-accent)}
        .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:1.5rem 0}
        .grid>div{background:#fff;border:1px solid rgba(0,0,0,.08);border-radius:4px;padding:12px}
        .grid label{display:block;font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:#78716c;margin-bottom:.3rem;font-family:var(--o-font-body)}
        .grid strong{font-size:1.05rem;color:var(--o-dark);font-family:var(--o-font-body)}
        .photos{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:8px;margin:1.5rem 0}
        .photos img{height:240px;object-fit:cover;border-radius:4px}
        .description{background:#fff;border:1px solid rgba(0,0,0,.08);border-radius:4px;padding:1.5rem;white-space:pre-wrap;margin:1.5rem 0}
        .features{display:flex;flex-wrap:wrap;gap:8px;margin:1rem 0}
        .features span{background:#fff;border:1px solid rgba(0,0,0,.12);border-radius:999px;padding:5px 13px;font-size:.85rem;color:var(--o-dark)}
        .card{background:#fff;border:1px solid rgba(0,0,0,.08);border-radius:4px;padding:20px;margin:1.5rem 0}
        """

    if theme_id == "classic":
        return base + """
        header{background:var(--o-primary);color:#fff;padding:18px 0;border-bottom:3px solid var(--o-accent)}
        header .container{display:flex;align-items:center;gap:16px}
        .brand-logo{height:42px;width:auto;filter:brightness(0) invert(1)}
        .brand-name{font-family:var(--o-font-headings);font-size:1.35rem;color:#fff}
        h1{font-size:2.4rem;line-height:1.15;margin:1.8rem 0 .6rem;color:var(--o-primary)}
        h2{font-size:1.3rem;color:var(--o-primary);margin:1.8rem 0 1rem;border-bottom:2px solid var(--o-accent);padding-bottom:.4rem;display:inline-block}
        .price{font-size:2.2rem;font-weight:700;color:var(--o-accent);font-family:var(--o-font-headings)}
        .meta{color:#666;font-size:.92rem;margin-bottom:1.2rem;font-style:italic}
        .listings{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:24px;margin-top:1.5rem}
        .listings a{background:#fff;border-radius:6px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.08);transition:transform .2s,box-shadow .2s}
        .listings a:hover{transform:translateY(-2px);box-shadow:0 6px 22px rgba(0,0,0,.12)}
        .listings img{height:210px;width:100%;object-fit:cover}
        .listings .body{padding:18px}
        .listings .body h3{font-size:1.15rem;color:var(--o-primary);margin-bottom:.4rem}
        .listings .body p{color:#666;font-size:.88rem;margin-bottom:.6rem;font-family:var(--o-font-body)}
        .listings .body strong{color:var(--o-accent);font-size:1.1rem}
        .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin:1.5rem 0}
        .grid>div{background:#fff;border-radius:4px;padding:14px;box-shadow:0 1px 4px rgba(0,0,0,.06)}
        .grid label{display:block;font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:#999;margin-bottom:.3rem;font-family:var(--o-font-body)}
        .grid strong{font-size:1.05rem;color:var(--o-primary);font-family:var(--o-font-body)}
        .photos{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:10px;margin:1.5rem 0}
        .photos img{height:260px;object-fit:cover;border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,.1)}
        .description{background:#fff;border-radius:6px;padding:1.8rem;white-space:pre-wrap;margin:1.5rem 0;box-shadow:0 1px 4px rgba(0,0,0,.06)}
        .features{display:flex;flex-wrap:wrap;gap:8px;margin:1rem 0}
        .features span{background:var(--o-primary);color:#fff;border-radius:4px;padding:6px 14px;font-size:.85rem}
        .card{background:#fff;border-radius:6px;padding:22px;margin:1.5rem 0;box-shadow:0 2px 12px rgba(0,0,0,.08)}
        """

    if theme_id == "bold":
        return base + """
        body{background:var(--o-light)}
        header{background:#fff;border-bottom:4px solid var(--o-primary);padding:20px 0}
        header .container{display:flex;align-items:center;gap:16px}
        .brand-logo{height:40px;width:auto}
        .brand-name{font-family:var(--o-font-headings);font-size:1.4rem;font-weight:800;color:var(--o-dark);text-transform:uppercase;letter-spacing:-.02em}
        h1{font-size:3.2rem;font-weight:800;line-height:1;margin:1.8rem 0 .6rem;text-transform:uppercase;letter-spacing:-.03em}
        h2{font-size:1.6rem;font-weight:800;margin:2rem 0 1rem;text-transform:uppercase;letter-spacing:-.02em}
        .price{font-size:2.6rem;font-weight:800;color:var(--o-primary);letter-spacing:-.02em}
        .meta{color:#666;font-size:.9rem;margin-bottom:1.2rem;text-transform:uppercase;letter-spacing:.05em;font-weight:600}
        .listings{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:6px;margin-top:1.5rem}
        .listings a{background:#fff;overflow:hidden;border:none;transition:transform .25s}
        .listings a:hover{transform:scale(.98)}
        .listings img{height:340px;width:100%;object-fit:cover}
        .listings .body{padding:18px;background:var(--o-dark);color:#fff}
        .listings .body h3{font-size:1.2rem;color:#fff;margin-bottom:.4rem;text-transform:uppercase;letter-spacing:-.01em}
        .listings .body p{color:#aaa;font-size:.82rem;margin-bottom:.6rem;text-transform:uppercase;letter-spacing:.04em;font-family:var(--o-font-body)}
        .listings .body strong{color:var(--o-primary);font-size:1.2rem;font-weight:800}
        .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:1px;margin:1.5rem 0;background:rgba(0,0,0,.08)}
        .grid>div{background:#fff;padding:18px}
        .grid label{display:block;font-size:.65rem;text-transform:uppercase;letter-spacing:.12em;color:#999;margin-bottom:.4rem;font-family:var(--o-font-body);font-weight:700}
        .grid strong{font-size:1.15rem;color:var(--o-dark);font-family:var(--o-font-body);font-weight:700}
        .photos{display:grid;grid-template-columns:repeat(auto-fit,minmax(400px,1fr));gap:4px;margin:1.5rem 0}
        .photos img{height:320px;object-fit:cover}
        .description{background:var(--o-dark);color:#fff;padding:2.2rem;white-space:pre-wrap;margin:1.5rem 0;font-size:1.05rem;line-height:1.7}
        .features{display:flex;flex-wrap:wrap;gap:4px;margin:1rem 0}
        .features span{background:var(--o-primary);color:#fff;padding:6px 14px;font-size:.78rem;text-transform:uppercase;letter-spacing:.06em;font-weight:700}
        .card{background:var(--o-dark);color:#fff;padding:24px;margin:1.5rem 0}
        .card strong{color:var(--o-primary);font-size:1.2rem}
        """

    # luxury
    return base + """
    body{background:var(--o-light)}
    header{background:transparent;padding:40px 0;border-bottom:1px solid rgba(0,0,0,.06)}
    header .container{display:flex;align-items:center;justify-content:center;gap:16px;text-align:center;flex-direction:column}
    .brand-logo{height:54px;width:auto}
    .brand-name{font-family:var(--o-font-headings);font-size:1.8rem;font-weight:400;color:var(--o-dark);letter-spacing:.04em}
    .brand-tagline{font-size:.7rem;letter-spacing:.5em;text-transform:uppercase;color:var(--o-accent);margin-top:6px;font-family:var(--o-font-body)}
    h1{font-size:2.8rem;line-height:1.15;margin:2.5rem 0 .8rem;font-weight:400;letter-spacing:.01em}
    h2{font-size:1.3rem;margin:2.5rem 0 1.2rem;font-weight:400;letter-spacing:.04em;color:var(--o-accent);text-transform:uppercase;font-size:.95rem}
    .price{font-size:2.4rem;font-weight:300;color:var(--o-accent);letter-spacing:.01em}
    .meta{color:#888;font-size:.78rem;text-transform:uppercase;letter-spacing:.2em;margin-bottom:1.4rem}
    .listings{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:32px;margin-top:2rem}
    .listings a{background:transparent;overflow:hidden;transition:opacity .25s}
    .listings a:hover{opacity:.85}
    .listings img{height:300px;width:100%;object-fit:cover}
    .listings .body{padding:18px 0;text-align:center}
    .listings .body h3{font-size:1.2rem;color:var(--o-dark);margin-bottom:.4rem;font-weight:400}
    .listings .body p{color:#888;font-size:.72rem;margin-bottom:.6rem;text-transform:uppercase;letter-spacing:.18em;font-family:var(--o-font-body)}
    .listings .body strong{color:var(--o-accent);font-size:1.05rem;font-weight:400}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin:2rem 0}
    .grid>div{background:transparent;border-top:1px solid var(--o-accent);padding:14px 4px}
    .grid label{display:block;font-size:.62rem;text-transform:uppercase;letter-spacing:.2em;color:#999;margin-bottom:.4rem;font-family:var(--o-font-body)}
    .grid strong{font-size:1rem;color:var(--o-dark);font-family:var(--o-font-body);font-weight:400}
    .photos{display:grid;grid-template-columns:repeat(auto-fit,minmax(440px,1fr));gap:12px;margin:2rem 0}
    .photos img{height:380px;object-fit:cover}
    .description{background:transparent;padding:2rem 0;white-space:pre-wrap;margin:1.5rem 0;font-size:1.05rem;line-height:1.85;color:#444;text-align:center;max-width:720px;margin-left:auto;margin-right:auto}
    .features{display:flex;flex-wrap:wrap;gap:8px;margin:1rem 0;justify-content:center}
    .features span{background:transparent;border:1px solid var(--o-accent);color:var(--o-accent);padding:6px 16px;font-size:.72rem;letter-spacing:.15em;text-transform:uppercase}
    .card{background:transparent;border-top:1px solid var(--o-accent);border-bottom:1px solid var(--o-accent);padding:32px 0;margin:2rem 0;text-align:center}
    .card strong{color:var(--o-dark);font-family:var(--o-font-headings);font-size:1.5rem;font-weight:400;display:block;margin-bottom:.4rem}
    """

def _render_header(cfg: Dict[str, Any], agency: Dict[str, Any]) -> str:
    name = escape(agency.get("display_name") or "")
    logo = cfg.get("logo_url")
    tagline = cfg.get("tagline")
    logo_html = f'<img src="{escape(logo)}" class="brand-logo" alt="{name}"/>' if logo else ""
    tagline_html = (
        f'<div class="brand-tagline">{escape(tagline)}</div>'
        if tagline and cfg["theme_id"] == "luxury" else ""
    )
    return f"""
    <header>
      <div class="container">
        {logo_html}
        <span class="brand-name">{name}</span>
        {tagline_html}
      </div>
    </header>"""

def _shell(cfg: Dict[str, Any], agency: Dict[str, Any],
           title: str, description: str, canonical: str, og_image: Optional[str],
           jsonld: str, body_html: str) -> str:
    og_img = f'<meta property="og:image" content="{escape(og_image)}"/>' if og_image else ""
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{escape(title)}</title>
<meta name="description" content="{escape(description)}"/>
<link rel="canonical" href="{escape(canonical)}"/>
<meta property="og:type" content="website"/>
<meta property="og:title" content="{escape(title)}"/>
<meta property="og:description" content="{escape(description)}"/>
<meta property="og:url" content="{escape(canonical)}"/>
{og_img}
<meta name="generator" content="OMNIA Real Estate Ecosystem"/>
<style>{_theme_css(cfg)}
{_share_css()}</style>
<script type="application/ld+json">{jsonld}</script>
</head>
<body data-theme="{cfg['theme_id']}">
{_render_header(cfg, agency)}
<main class="container">{body_html}</main>
<footer></footer>
</body>
</html>"""

def _public_base_url() -> str:
    """Backend-served public site origin (used to build absolute share URLs).
    Falls back to FRONTEND_URL — in this deployment the frontend host
    proxies /api/* to the backend, so /api/p/{slug} is publicly reachable there.
    """
    return (os.environ.get("FRONTEND_URL") or "").rstrip("/")

def _share_block(absolute_url: str, share_title: str, share_text: str) -> str:
    """Render 4 share buttons (WhatsApp / Facebook / Email / Copy link).
    Pure HTML + a tiny inline JS for copy-to-clipboard. No 3rd-party scripts."""
    u = quote_plus(absolute_url)
    t_text = quote_plus(share_text)
    t_title = quote_plus(share_title)
    wa = f"https://wa.me/?text={t_text}%20{u}"
    fb = f"https://www.facebook.com/sharer/sharer.php?u={u}"
    mailto = f"mailto:?subject={t_title}&body={t_text}%20{u}"
    return f"""
    <div class="share-block" data-share-url="{escape(absolute_url)}">
      <p class="share-label">Condividi questo immobile</p>
      <div class="share-row">
        <a class="share-btn share-wa" href="{wa}" target="_blank" rel="noopener" aria-label="Condividi su WhatsApp">
          <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M.057 24l1.687-6.163A11.867 11.867 0 0 1 .157 11.892C.16 5.335 5.495 0 12.05 0a11.817 11.817 0 0 1 8.413 3.488 11.824 11.824 0 0 1 3.48 8.414c-.003 6.557-5.338 11.892-11.893 11.892a11.9 11.9 0 0 1-5.688-1.448L.057 24zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884-.001 2.225.651 3.891 1.746 5.634l-.999 3.648 3.742-.981zm11.387-5.464c-.074-.124-.272-.198-.57-.347-.297-.149-1.758-.868-2.031-.967-.272-.099-.47-.149-.669.149-.198.297-.768.967-.941 1.165-.173.198-.347.223-.644.074-.297-.149-1.255-.462-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.521.151-.172.2-.296.3-.495.099-.198.05-.372-.025-.521-.075-.148-.669-1.611-.916-2.206-.242-.579-.487-.501-.669-.51l-.57-.01c-.198 0-.52.074-.792.372s-1.04 1.016-1.04 2.479c0 1.462 1.065 2.875 1.213 3.074.149.198 2.095 3.2 5.076 4.487.709.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.695.248-1.29.173-1.414z"/></svg>
          WhatsApp
        </a>
        <a class="share-btn share-fb" href="{fb}" target="_blank" rel="noopener" aria-label="Condividi su Facebook">
          <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M22.675 0H1.325C.593 0 0 .593 0 1.325v21.351C0 23.408.593 24 1.325 24H12.82v-9.294H9.692v-3.622h3.128V8.413c0-3.1 1.893-4.788 4.659-4.788 1.325 0 2.463.099 2.795.143v3.24l-1.918.001c-1.504 0-1.795.715-1.795 1.763v2.313h3.587l-.467 3.622h-3.12V24h6.116c.73 0 1.323-.592 1.323-1.324V1.325C24 .593 23.408 0 22.675 0z"/></svg>
          Facebook
        </a>
        <a class="share-btn share-em" href="{mailto}" aria-label="Condividi via Email">
          <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M0 3v18h24V3H0zm21.518 2L12 12.713 2.482 5h19.036zM2 19V6.255l10 8.105 10-8.105V19H2z"/></svg>
          Email
        </a>
        <button type="button" class="share-btn share-copy" data-action="copy" aria-label="Copia link">
          <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>
          <span class="share-copy-label">Copia link</span>
        </button>
      </div>
    </div>
    <script>(function(){{
      var b=document.currentScript.previousElementSibling.querySelector('[data-action="copy"]');
      if(!b) return;
      b.addEventListener('click',function(){{
        var url=b.closest('.share-block').getAttribute('data-share-url');
        var lbl=b.querySelector('.share-copy-label');
        var orig=lbl.textContent;
        var done=function(){{lbl.textContent='\u2713 Copiato'; setTimeout(function(){{lbl.textContent=orig;}},1800);}};
        if(navigator.clipboard){{navigator.clipboard.writeText(url).then(done,function(){{alert(url);}});}}
        else{{var ta=document.createElement('textarea');ta.value=url;document.body.appendChild(ta);ta.select();try{{document.execCommand('copy');done();}}catch(_){{}}document.body.removeChild(ta);}}
      }});
    }})();</script>"""

def _share_css() -> str:
    """Theme-agnostic styling for the share block (uses CSS variables already in scope)."""
    return """
    .share-block{margin:2rem 0;padding:1.25rem 0;border-top:1px solid rgba(0,0,0,.06)}
    .share-label{font-family:var(--o-font-body);font-size:.72rem;letter-spacing:.2em;text-transform:uppercase;color:#888;margin-bottom:.8rem}
    .share-row{display:flex;flex-wrap:wrap;gap:8px}
    .share-btn{display:inline-flex;align-items:center;gap:8px;padding:8px 14px;border-radius:999px;font-family:var(--o-font-body);font-size:.85rem;font-weight:500;cursor:pointer;border:1px solid rgba(0,0,0,.12);background:#fff;color:var(--o-dark);text-decoration:none;transition:transform .15s,box-shadow .15s,opacity .15s}
    .share-btn:hover{transform:translateY(-1px);box-shadow:0 2px 8px rgba(0,0,0,.08);text-decoration:none}
    .share-wa{background:#25D366;color:#fff;border-color:#25D366}
    .share-fb{background:#1877F2;color:#fff;border-color:#1877F2}
    .share-em{background:var(--o-primary);color:#fff;border-color:var(--o-primary)}
    .share-copy{background:#fff;color:var(--o-dark)}
    .share-wa:hover,.share-fb:hover,.share-em:hover{color:#fff;opacity:.92}
    """

def _home_css() -> str:
    """Fixed structure CSS for the public agency home (chrome uses --o-primary)."""
    return """
    body.agency-home{background:#f4f4f4;color:#222;font-family:Arial,Helvetica,sans-serif}
    body.agency-home a{color:inherit}
    .ah-wrap{max-width:1100px;margin:0 auto;padding:0 12px 40px}
    .ah-top{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:14px 0 10px;flex-wrap:wrap}
    .ah-brand{display:flex;align-items:center;gap:12px;text-decoration:none;color:#222}
    .ah-brand img{height:52px;width:auto;object-fit:contain}
    .ah-brand-name{font-size:1.15rem;font-weight:700;letter-spacing:.04em;text-transform:uppercase}
    .ah-nav{display:flex;flex-wrap:wrap;background:var(--o-primary);border-radius:2px;overflow:hidden}
    .ah-nav a{color:#fff;text-decoration:none;padding:10px 14px;font-size:.85rem;font-weight:600;border-right:1px solid rgba(255,255,255,.18)}
    .ah-nav a:last-child{border-right:0}
    .ah-nav a:hover{background:rgba(0,0,0,.12)}
    .ah-hero{margin:8px 0 16px;min-height:260px;border-radius:2px;position:relative;overflow:hidden;display:flex;align-items:flex-end;justify-content:center;background-color:var(--o-primary);background-size:cover;background-position:center center;background-repeat:no-repeat}
    .ah-hero::before{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.15) 0%,rgba(0,0,0,.45) 100%);pointer-events:none}
    .ah-hero-inner{position:relative;z-index:1;padding:28px 20px;color:#fff;text-align:center;width:100%}
    .ah-hero-inner strong{display:block;font-size:1.35rem;letter-spacing:.06em;text-transform:uppercase;text-shadow:0 1px 3px rgba(0,0,0,.35)}
    .ah-hero-dots{display:flex;gap:8px;justify-content:center;margin-top:12px}
    .ah-hero-dots span{width:10px;height:10px;border-radius:50%;background:rgba(255,255,255,.55);box-shadow:0 0 0 1px rgba(0,0,0,.15)}
    .ah-hero-dots span.on{background:#fff}
    .ah-search-row{display:grid;grid-template-columns:260px 1fr;gap:14px;margin-bottom:28px}
    .ah-search-row.solo{grid-template-columns:1fr}
    .ah-box{background:var(--o-primary);color:#fff;border-radius:2px;padding:14px 14px 12px}
    .ah-box h2{font-family:inherit;font-size:1rem;font-weight:700;margin:0 0 12px;color:#fff;letter-spacing:.02em}
    .ah-field{margin-bottom:8px}
    .ah-field label{display:block;font-size:.72rem;margin-bottom:3px;opacity:.95}
    .ah-field select,.ah-field input{width:100%;padding:7px 8px;border:0;border-radius:2px;font-size:.85rem;color:#222}
    .ah-range{display:grid;grid-template-columns:1fr 1fr;gap:6px}
    .ah-btn{display:inline-block;width:100%;margin-top:8px;padding:10px 12px;border:0;border-radius:2px;background:#4a4a4a;color:#fff;font-weight:700;font-size:.9rem;cursor:pointer;text-align:center;text-decoration:none}
    .ah-btn.black{background:#111}
    .ah-btn:hover{opacity:.92}
    .ah-powered{margin-top:10px;text-align:center;font-size:.65rem;letter-spacing:.12em;text-transform:uppercase;opacity:.9}
    .ah-agency-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px 14px}
    .ah-agency-actions{grid-column:1 / -1;display:flex;justify-content:flex-end}
    .ah-agency-actions .ah-btn{width:auto;min-width:220px}
    .ah-section{margin:8px 0 28px}
    .ah-section h2{font-family:inherit;font-size:1.25rem;font-weight:700;color:#333;margin:0 0 14px;padding-bottom:6px;border-bottom:2px solid var(--o-primary)}
    .ah-cards{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
    .ah-card{display:block;background:#fff;border:1px solid #ddd;text-decoration:none;color:#222;overflow:hidden}
    .ah-card:hover{box-shadow:0 4px 14px rgba(0,0,0,.1)}
    .ah-card-img{position:relative;aspect-ratio:4/3;background:#e8e8e8;background-size:cover;background-position:center}
    .ah-card-op{position:absolute;top:0;left:0;background:var(--o-primary);color:#fff;font-size:.72rem;font-weight:700;padding:5px 10px;text-transform:uppercase}
    .ah-card-price{position:absolute;right:8px;bottom:8px;background:rgba(255,255,255,.95);color:#111;font-weight:700;font-size:.95rem;padding:4px 8px;border-radius:2px}
    .ah-card-body{padding:10px 12px 0}
    .ah-card-city{font-size:.85rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;margin-bottom:4px}
    .ah-card-title{font-size:.92rem;line-height:1.3;min-height:2.4em}
    .ah-card-zone{font-size:.78rem;color:#777;margin:4px 0 8px}
    .ah-card-meta{display:flex;gap:0;background:#eee;border-top:1px solid #ddd;margin-top:8px}
    .ah-card-meta span{flex:1;text-align:center;padding:8px 4px;font-size:.75rem;color:#444;border-right:1px solid #ddd}
    .ah-card-meta span:last-child{border-right:0}
    .ah-empty{grid-column:1/-1;background:#fff;border:1px dashed #ccc;padding:28px;text-align:center;color:#666}
    .ah-footer{margin-top:36px;background:#ececec;border-top:1px solid #ccc;padding:28px 0}
    .ah-footer-inner{max-width:1100px;margin:0 auto;padding:0 12px;display:grid;grid-template-columns:1.2fr 1fr;gap:24px}
    .ah-footer h3{font-size:.95rem;margin:0 0 10px;color:#333}
    .ah-footer ul{list-style:none;padding:0;margin:0}
    .ah-footer li{font-size:.82rem;color:#555;margin:4px 0}
    .ah-footer li:before{content:'› ';color:var(--o-primary);font-weight:700}
    .ah-footer-contact p{font-size:.85rem;color:#444;margin:4px 0;line-height:1.45}
    @media (max-width:900px){
      .ah-search-row,.ah-search-row.solo{grid-template-columns:1fr}
      .ah-agency-grid{grid-template-columns:1fr}
      .ah-cards{grid-template-columns:1fr 1fr}
      .ah-footer-inner{grid-template-columns:1fr}
    }
    @media (max-width:560px){
      .ah-cards{grid-template-columns:1fr}
      .ah-nav{width:100%}
    }
    """

