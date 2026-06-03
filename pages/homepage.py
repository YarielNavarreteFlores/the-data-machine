import streamlit as st
import pandas as pd
import math
import random

from src.styles import BASE_CSS

st.set_page_config(page_title="The Data Machine", page_icon="🎮", layout="wide")

if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("Inicia sesión para ver el catálogo.")
    st.stop()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(BASE_CSS + """
<style>
/* ── Hero ── */
.tdm-hero { position: relative; z-index: 1; text-align: center; margin-bottom: 5rem; }
.tdm-hero-eyebrow {
    font-size: 11px; letter-spacing: 4px; text-transform: uppercase;
    color: #7c6af5; margin-bottom: 4px;
    animation: glitchEyebrow 3s ease-in-out infinite;
}
@keyframes glitchEyebrow {
    0%, 90%, 100% { text-shadow: 0 0 0 transparent; }
    92% { text-shadow: -2px 0 #f06292, 2px 0 #26c6da; }
    94% { text-shadow: 2px 0 #f06292, -2px 0 #26c6da; }
    96% { text-shadow: -1px 0 #f06292, 1px 0 #26c6da; }
}
.tdm-hero-title {
    font-family: 'Rajdhani', sans-serif; font-size: 52px; font-weight: 700;
    line-height: 1.05; margin-bottom: 6px; opacity: 0;
    animation: fadeInUp 0.8s ease forwards;
    text-shadow: 0 2px 20px rgba(0,0,0,0.5);
}
.tdm-hero-grad {
    background: linear-gradient(90deg, #f06292, #7c6af5, #26c6da);
    background-size: 200% auto;
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    animation: gradienteLogo 5s ease-in-out infinite alternate;
}
.tdm-hero-sub {
    font-size: 16px; color: #e8eaf6; opacity: 0;
    animation: fadeInUp 0.8s ease 0.15s forwards;
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ── Entry animations ── */
.tdm-stats { opacity: 0; animation: fadeInUp 0.8s ease 0.3s forwards; }
.info-card { opacity: 0; transform: translateY(30px); }
.carousel-track .game-card { opacity: 0; transform: translateY(30px); }

/* ── Scroll indicator ── */
.tdm-scroll {
    text-align: center; margin-top: 1.5rem; opacity: 0;
    animation: fadeIn 1s ease 0.6s forwards;
}
.tdm-scroll-arrow {
    display: inline-block; font-size: 14px; color: #e8eaf6;
    animation: bounceArrow 2s ease-in-out infinite;
}
@keyframes bounceArrow {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(8px); }
}
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

/* ── Featured game ── */
.tdm-featured {
    position: relative; z-index: 1; border-radius: 16px; overflow: hidden;
    margin-bottom: 4rem; height: 320px; cursor: pointer;
}
.tdm-featured img {
    width: 100%; height: 100%; object-fit: cover; display: block;
}
.tdm-featured-overlay {
    position: absolute; inset: 0;
    background: linear-gradient(90deg, rgba(11,14,26,0.85) 0%, transparent 50%, rgba(11,14,26,0.85) 100%);
}
.tdm-featured-body {
    position: absolute; inset: 0; display: flex; flex-direction: column;
    justify-content: center; padding: 2rem 3rem;
}
.tdm-featured-label {
    font-family: 'Orbitron', monospace; font-size: 10px; letter-spacing: 3px;
    color: #e8eaf6; text-transform: uppercase;
}
.tdm-featured-title {
    font-family: 'Rajdhani', sans-serif; font-size: 36px; font-weight: 700;
    color: #f0f2ff; text-shadow: 0 2px 16px rgba(0,0,0,0.5); margin: 4px 0;
}
.tdm-featured-btn {
    display: inline-block; margin-top: 0.8rem; padding: 8px 24px;
    border-radius: 8px; border: 1px solid rgba(124,106,245,0.4);
    background: rgba(124,106,245,0.15); color: #c7c0f0;
    font-family: 'Rajdhani', sans-serif; font-size: 14px; font-weight: 700;
    cursor: pointer; transition: all 0.2s; width: fit-content;
}
.tdm-featured-btn:hover {
    background: rgba(124,106,245,0.3); border-color: #7c6af5;
    box-shadow: 0 0 20px rgba(124,106,245,0.3); color: #f0f2ff;
}
.tdm-featured:hover .tdm-featured-btn {
    background: rgba(124,106,245,0.3); border-color: #7c6af5;
}

/* ── Tech stack ── */
.tdm-tech {
    position: relative; z-index: 1; text-align: center;
    padding: 1rem 0; margin-bottom: 1.5rem;
}
.tdm-tech-label {
    font-family: 'Orbitron', monospace; font-size: 9px; letter-spacing: 2px;
    color: #e8eaf6; text-transform: uppercase; margin-bottom: 0.8rem;
}
.tdm-tech-badge {
    display: inline-block; margin: 4px 5px; padding: 4px 12px;
    border-radius: 6px; font-size: 11px; font-family: 'Inter', sans-serif;
    font-weight: 500; border: 1px solid rgba(255,255,255,0.06);
    background: rgba(255,255,255,0.02); color: #e8eaf6;
}
</style>
""", unsafe_allow_html=True)


# ── Datos ─────────────────────────────────────────────────────────────────────
@st.cache_data
def load_catalog(path: str = "data/processed/dataset_limpio.csv") -> pd.DataFrame:
    try:
        df = pd.read_csv(path)
        _ = df["name"]
    except (FileNotFoundError, KeyError):
        df = pd.DataFrame({
            "name": ["Hollow Knight", "Elden Ring", "Stardew Valley", "Cyberpunk 2077", "Subnautica", "Hades", "Deep Rock Galactic", "Terraria", "Portal 2", "Celeste"],
            "header_image": [
                "https://cdn.cloudflare.steamstatic.com/steam/apps/367520/header.jpg",
                "https://cdn.cloudflare.steamstatic.com/steam/apps/1245620/header.jpg",
                "https://cdn.cloudflare.steamstatic.com/steam/apps/413150/header.jpg",
                "https://cdn.cloudflare.steamstatic.com/steam/apps/1091500/header.jpg",
                "https://cdn.cloudflare.steamstatic.com/steam/apps/264710/header.jpg",
                "https://cdn.cloudflare.steamstatic.com/steam/apps/1145360/header.jpg",
                "https://cdn.cloudflare.steamstatic.com/steam/apps/548430/header.jpg",
                "https://cdn.cloudflare.steamstatic.com/steam/apps/105600/header.jpg",
                "https://cdn.cloudflare.steamstatic.com/steam/apps/620/header.jpg",
                "https://cdn.cloudflare.steamstatic.com/steam/apps/504230/header.jpg",
            ],
            "price": [14.99, 59.99, 14.99, 29.99, 0.0, 24.99, 29.99, 9.99, 9.99, 19.99],
            "pct_pos_total": [92, 96, 98, 76, 94, 97, 98, 97, 99, 99],
            "tags": ["Metroidvania,Indie,Difficult", "Souls-like,Action RPG,Dark Fantasy", "Farming Sim,Relaxing,RPG", "Open World,Cyberpunk,Action", "Survival,Exploration,Underwater", "Roguelike,Action,Mythology", "Co-op,Shooter,Space", "Sandbox,Adventure,2D", "Puzzle,Co-op,Sci-fi", "Platformer,Indie,Difficult"],
            "metacritic_score": [87, 96, 89, 76, 87, 93, 85, 83, 95, 94],
            "estimated_owners": ["2M-5M", "5M-10M", "10M-20M", "10M-20M", "5M-10M", "5M-10M", "5M-10M", "30M-50M", "10M-20M", "2M-5M"],
        })
    return df


def sentiment_label(pct):
    if pct >= 85: return '<span class="rating-pill r-pos">Muy positivo</span>'
    elif pct >= 65: return '<span class="rating-pill r-mix">Mixto</span>'
    return '<span class="rating-pill r-neg">Negativo</span>'

def price_display(price):
    if price == 0: return '<span class="game-price price-free">Gratis</span>'
    mxn = price * 20
    return f'<span class="game-price">MX${mxn:,.0f}</span>'


df = load_catalog()

st.markdown('<div class="tdm-page">', unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
user = st.session_state.get("username", "usuario")
st.markdown(f"""
<div class="tdm-topbar">
  <div class="tdm-logo">⬡ THE DATA MACHINE</div>
  <div class="tdm-actions">
    <span class="tdm-music-btn" id="tdmMusicBtn">🎵</span>
    <span class="tdm-user">◆ {user}</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="tdm-hero">
  <div class="tdm-hero-eyebrow">⟡ La Máquina de Datos</div>
  <div class="tdm-hero-title">
    Millones de reseñas.<br>
    <span class="tdm-hero-grad">Una máquina para entenderlas todas.</span>
  </div>
  <div class="tdm-hero-sub">+21M reseñas · VADER · TF-IDF · Dashboard interactivo · Descarga CSV/PNG</div>
  <div class="tdm-scroll"><span class="tdm-scroll-arrow">⟡</span></div>
</div>
""", unsafe_allow_html=True)


# ── Stats ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="tdm-stats">
  <div class="tdm-stat-item">
    <div class="tdm-stat-num" data-count="{len(df)}">{len(df)}</div>
    <div class="tdm-stat-lbl">Juegos analizados</div>
  </div>
  <div class="tdm-stat-item">
    <div class="tdm-stat-num" data-count="21000000">21M+</div>
    <div class="tdm-stat-lbl">Reseñas procesadas</div>
  </div>
  <div class="tdm-stat-item">
    <div class="tdm-stat-num">VADER</div>
    <div class="tdm-stat-lbl">Modelo NLP</div>
  </div>
  <div class="tdm-stat-item">
    <div class="tdm-stat-num">TF-IDF</div>
    <div class="tdm-stat-lbl">Extracción temas</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── ¿Qué es? ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="tdm-section-title">▸ ¿Qué es The Data Machine?</div>
<div class="tdm-section-sub">Procesamos millones de reseñas de Steam con NLP. Sentimiento, temas y métricas de un vistazo.</div>
""", unsafe_allow_html=True)

info_cols = st.columns(3)
for col, (letter, grad, title, desc) in zip(info_cols, [
    ("S", "linear-gradient(135deg,#f06292,#7c6af5)", "Análisis de Sentimiento", "Clasificamos cada reseña como positiva, neutral o negativa usando VADER (NLTK). Una gráfica clara de lo que opina la comunidad."),
    ("T", "linear-gradient(135deg,#7c6af5,#a99cf5)", "Extracción de Temas", "TF-IDF detecta palabras y conceptos más repetidos. Bugs, historia, precio, multijugador — sin leer ni una línea."),
    ("D", "linear-gradient(135deg,#26c6da,#7c6af5)", "Dashboard Interactivo", "Gráficas Plotly, nubes de palabras y tablas. Descarga el análisis en CSV o exporta las gráficas en PNG."),
]):
    with col:
        st.markdown(f"""
<div class="info-card">
  <div class="info-card-inner">
    <span class="info-card-letter" style="background:{grad};-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">{letter}</span>
    <div class="info-card-title">{title}</div>
    <div class="info-card-desc">{desc}</div>
  </div>
</div>""", unsafe_allow_html=True)

# ── Featured game ──────────────────────────────────────────────────────────────
featured = df.sample(1).iloc[0]
ftags = "".join(f'<span class="game-tag">{t.strip()}</span>' for t in str(featured.get("tags", "")).split(",")[:3])
st.markdown(f"""
<div class="tdm-featured" data-game="{featured['name']}">
  <img src="{featured['header_image']}" onerror="this.src='https://via.placeholder.com/600x320/0b0e1a/7c6af5?text=⟡'" alt="">
  <div class="tdm-featured-overlay"></div>
  <div class="tdm-featured-body">
    <div class="tdm-featured-label">⟡ JUEGO DESTACADO</div>
    <div class="tdm-featured-title">{featured['name']}</div>
    <div style="display:flex;gap:6px;margin:4px 0;">{ftags}</div>
    <div style="color:#e8eaf6;font-size:13px;text-shadow:0 1px 8px rgba(0,0,0,0.4);">★ {featured['pct_pos_total']}% positivo · {price_display(featured['price'])}</div>
    <span class="tdm-featured-btn">Ver análisis →</span>
  </div>
</div>""", unsafe_allow_html=True)


st.markdown('<div class="tdm-divider"></div>', unsafe_allow_html=True)

# ── Catálogo ──────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="position:relative;z-index:1;display:flex;align-items:center;gap:12px;margin-bottom:0.5rem;">
  <span class="tdm-section-title" style="margin-bottom:0;">▸ Catálogo de Juegos</span>
  <span style="font-size:11px;color:#e8eaf6;font-family:'Orbitron',monospace;">{len(df)} TÍTULOS</span>
</div>
""", unsafe_allow_html=True)

carousel_games = df.sample(n=30)
carousel_html = '<div class="carousel-container"><div class="carousel-arrow carousel-arrow-left" id="carouselPrev">‹</div><div class="carousel-track" id="carouselTrack">'

for _, game in carousel_games.iterrows():
    tags_html = "".join(f'<span class="game-tag">{t.strip()}</span>' for t in str(game.get("tags", "")).split(",")[:3])
    carousel_html += f"""
<div class="game-card" data-game="{game['name']}">
  <div class="game-card-inner">
    <img class="game-card-img" src="{game['header_image']}" onerror="this.src='https://via.placeholder.com/300x200/0b0e1a/7c6af5?text=🎮'" alt="{game['name']}"/>
    <div class="game-card-body">
      <div class="game-tags">{tags_html}</div>
      <div class="game-card-title">{game['name']}</div>
      <div class="game-meta">{sentiment_label(game['pct_pos_total'])} {price_display(game['price'])}</div>
      <div style="font-size:10px;color:#e8eaf6;margin-top:5px;font-family:'Orbitron',monospace;">⭐ {game['pct_pos_total']}% · METACORE {game.get('metacritic_score','—')}</div>
    </div>
  </div>
</div>"""

num_pages = max(1, math.ceil(len(carousel_games) / 3))
dots_html = '<div class="carousel-dots" id="carouselDots">'
for i in range(num_pages):
    dots_html += f'<span class="carousel-dot { "active" if i == 0 else "" }" data-index="{i}"></span>'
dots_html += '</div>'

carousel_html += '</div><div class="carousel-arrow carousel-arrow-right" id="carouselNext">›</div></div>' + dots_html
st.markdown(carousel_html, unsafe_allow_html=True)

# ── Tech stack ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="tdm-tech">
  <div class="tdm-tech-label">⟡ STACK TECNOLÓGICO</div>
  <div>
    <span class="tdm-tech-badge">Python</span>
    <span class="tdm-tech-badge">Streamlit</span>
    <span class="tdm-tech-badge">VADER</span>
    <span class="tdm-tech-badge">TF-IDF</span>
    <span class="tdm-tech-badge">Pandas</span>
    <span class="tdm-tech-badge">Plotly</span>
    <span class="tdm-tech-badge">NLTK</span>
    <span class="tdm-tech-badge">BeautifulSoup</span>
    <span class="tdm-tech-badge">NumPy</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="tdm-footer">
  <div class="tdm-footer-line">© 2026 <span class="tdm-footer-grad">The Data Machine</span> · IPN ESCOM · Semestre IV</div>
  <div class="tdm-footer-line">Hecho con ⟡ por el equipo La Máquina de Datos</div>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ── JS ────────────────────────────────────────────────────────────────────────
st.components.v1.html("""
<script>
(function() {
  try {
    var doc = window.parent.document;
    var win = window.parent;

    // ══════════════════════════════════════════════════════════════════════
    // NEBULA BACKGROUND — Canvas incrustado en body, fixed
    // ══════════════════════════════════════════════════════════════════════
    var canvas = doc.createElement('canvas');
    canvas.style.cssText = 'position:fixed;inset:0;z-index:0;pointer-events:none;width:100%;height:100%';
    doc.body.appendChild(canvas);
    var ctx = canvas.getContext('2d');
    var W, H, CX, CY;

    function resize() {
      var dpr = 2;
      W = win.innerWidth * dpr;
      H = win.innerHeight * dpr;
      canvas.width = W; canvas.height = H;
      canvas.style.width = win.innerWidth + 'px';
      canvas.style.height = win.innerHeight + 'px';
      CX = W / 2; CY = H / 2;
      initParticles();
      initStars();
    }

    var particles = [];
    var mouse = { x: -1000, y: -1000 };
    var shockwave = { active: false, x: 0, y: 0, radius: 0, maxRadius: 0 };

    function spawnParticle() {
      var angle = Math.random() * Math.PI * 2;
      var dist = 30 + Math.random() * Math.min(W, H) * 0.45;
      var orbitSpeed = (0.3 + Math.random() * 1.2) * (Math.random() > 0.5 ? 1 : -1);
      var size = 2 + Math.random() * 4;
      var colors = ['#f06292', '#7c6af5', '#26c6da', '#a99cf5', '#e8eaf6'];
      var col = colors[Math.floor(Math.random() * colors.length)];
      return {
        angle: angle, dist: dist, orbitSpeed: orbitSpeed,
        size: size, color: col,
        baseY: (Math.random() - 0.5) * 60,
        trail: []
      };
    }

    function initParticles() {
      particles = [];
      for (var i = 0; i < 500; i++) particles.push(spawnParticle());
    }

    var stars = [];
    function initStars() {
      stars = [];
      for (var i = 0; i < 100; i++) {
        stars.push({
          x: Math.random() * W, y: Math.random() * H,
          r: 0.5 + Math.random() * 1.5,
          speed: 0.3 + Math.random() * 0.8,
          phase: Math.random() * Math.PI * 2
        });
      }
    }

    doc.addEventListener('mousemove', function(e) {
      mouse.x = e.clientX * 2;
      mouse.y = e.clientY * 2;
    });

    doc.addEventListener('click', function(e) {
      shockwave.active = true;
      shockwave.x = e.clientX * 2;
      shockwave.y = e.clientY * 2;
      shockwave.radius = 0;
      shockwave.maxRadius = Math.min(W, H) * 0.7;
    });

    function draw() {
      var bg = ctx.createRadialGradient(CX, CY * 0.7, 0, CX, CY * 0.7, Math.max(W, H) * 0.6);
      bg.addColorStop(0, '#0f1225');
      bg.addColorStop(0.5, '#0b0e1a');
      bg.addColorStop(1, '#060810');
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, W, H);

      var t = Date.now() / 1000;
      for (var i = 0; i < stars.length; i++) {
        var s = stars[i];
        var a = 0.2 + 0.8 * (0.5 + 0.5 * Math.sin(t * s.speed + s.phase));
        ctx.fillStyle = 'rgba(255,255,255,' + a + ')';
        ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2); ctx.fill();
      }

      var glow = ctx.createRadialGradient(CX, CY, 0, CX, CY, Math.min(W, H) * 0.5);
      glow.addColorStop(0, 'rgba(124,106,245,0.08)');
      glow.addColorStop(1, 'transparent');
      ctx.fillStyle = glow;
      ctx.fillRect(0, 0, W, H);

      if (shockwave.active) {
        shockwave.radius += 12;
        if (shockwave.radius > shockwave.maxRadius) shockwave.active = false;
        var swAlpha = 1 - (shockwave.radius / shockwave.maxRadius);
        ctx.strokeStyle = 'rgba(124,106,245,' + swAlpha * 0.6 + ')';
        ctx.lineWidth = 3 * swAlpha;
        ctx.beginPath();
        ctx.arc(shockwave.x, shockwave.y, shockwave.radius, 0, Math.PI * 2);
        ctx.stroke();
        var swGlow = ctx.createRadialGradient(shockwave.x, shockwave.y, 0, shockwave.x, shockwave.y, shockwave.radius);
        swGlow.addColorStop(0, 'rgba(38,198,218,' + swAlpha * 0.1 + ')');
        swGlow.addColorStop(1, 'transparent');
        ctx.fillStyle = swGlow;
        ctx.beginPath(); ctx.arc(shockwave.x, shockwave.y, shockwave.radius, 0, Math.PI * 2);
        ctx.fill();
      }

      for (var i = 0; i < particles.length; i++) {
        var p = particles[i];
        p.angle += p.orbitSpeed * 0.008;

        var dx = mouse.x - (CX + Math.cos(p.angle) * p.dist);
        var dy = mouse.y - (CY + Math.sin(p.angle) * p.dist * 0.5 + p.baseY);
        var dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 200) {
          var force = (200 - dist) / 200 * 3;
          p.angle -= (dx / dist) * force * 0.003;
          p.dist += force * (dist < 100 ? 0.5 : -0.3);
          p.dist = Math.max(20, Math.min(Math.min(W, H) * 0.45, p.dist));
        }

        var px = CX + Math.cos(p.angle) * p.dist;
        var py = CY + Math.sin(p.angle) * p.dist * 0.5 + p.baseY;

        p.trail.push({ x: px, y: py });
        if (p.trail.length > 8) p.trail.shift();

        for (var j = 0; j < p.trail.length; j++) {
          var a = (j / p.trail.length) * 0.25;
          ctx.fillStyle = p.color.replace(')', ',' + a + ')').replace('rgb', 'rgba');
          ctx.beginPath();
          ctx.arc(p.trail[j].x, p.trail[j].y, p.size * (j / p.trail.length) * 0.5, 0, Math.PI * 2);
          ctx.fill();
        }

        ctx.shadowBlur = 12;
        ctx.shadowColor = p.color;
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(px, py, p.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
      }
    }

    function update() {
      draw();
      requestAnimationFrame(update);
    }

    resize();
    win.addEventListener('resize', resize);
    update();

    // ══════════════════════════════════════════════════════════════════════
    // MÚSICA SYNTHWAVE
    // ══════════════════════════════════════════════════════════════════════
    var audioCtx = null, playing = false, loopTimers = [];

    function kick(time) {
      var osc = audioCtx.createOscillator(), g = audioCtx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(150, time);
      osc.frequency.exponentialRampToValueAtTime(40, time + 0.08);
      g.gain.setValueAtTime(0.3, time);
      g.gain.exponentialRampToValueAtTime(0.001, time + 0.1);
      osc.connect(g); g.connect(audioCtx.destination);
      osc.start(time); osc.stop(time + 0.1);
    }
    function snare(time) {
      var len = audioCtx.sampleRate * 0.1, buf = audioCtx.createBuffer(1, len, audioCtx.sampleRate);
      var d = buf.getChannelData(0);
      for (var i = 0; i < len; i++) d[i] = (Math.random()*2-1) * Math.pow(1-i/len, 3);
      var src = audioCtx.createBufferSource(); src.buffer = buf;
      var g = audioCtx.createGain();
      g.gain.setValueAtTime(0.15, time);
      g.gain.exponentialRampToValueAtTime(0.001, time + 0.1);
      src.connect(g); g.connect(audioCtx.destination);
      src.start(time); src.stop(time + 0.1);
    }
    function arp(time, f) {
      var notes = [f, f*1.25, f*1.5, f*2, f*1.5, f*1.25];
      for (var i = 0; i < notes.length; i++) {
        var osc = audioCtx.createOscillator(), g = audioCtx.createGain();
        osc.type = 'square'; osc.frequency.value = notes[i];
        g.gain.setValueAtTime(0.04, time + i*0.06);
        g.gain.exponentialRampToValueAtTime(0.001, time + i*0.06 + 0.05);
        osc.connect(g); g.connect(audioCtx.destination);
        osc.start(time + i*0.06); osc.stop(time + i*0.06 + 0.05);
      }
    }
    function pad(time, f) {
      var osc = audioCtx.createOscillator(), g = audioCtx.createGain();
      osc.type = 'sawtooth'; osc.frequency.value = f;
      g.gain.setValueAtTime(0.02, time);
      g.gain.linearRampToValueAtTime(0.04, time + 0.3);
      g.gain.linearRampToValueAtTime(0.02, time + 1.8);
      g.gain.linearRampToValueAtTime(0.001, time + 2);
      osc.connect(g); g.connect(audioCtx.destination);
      osc.start(time); osc.stop(time + 2);
    }
    function scheduleSynthwave() {
      var t = audioCtx.currentTime + 0.05, beat = 0.5;
      var chords = [
        { arp: 261.63, pad: 130.81 }, { arp: 329.63, pad: 164.81 },
        { arp: 293.66, pad: 146.83 }, { arp: 349.23, pad: 174.61 },
        { arp: 329.63, pad: 164.81 }, { arp: 392.00, pad: 196.00 },
        { arp: 261.63, pad: 130.81 }, { arp: 293.66, pad: 146.83 },
      ];
      for (var bar = 0; bar < 8; bar++) {
        var ch = chords[bar];
        for (var b = 0; b < 4; b++) {
          var bt = t + (bar * 4 + b) * beat;
          if (b === 0 || b === 2) kick(bt);
          if (b === 1 || b === 3) snare(bt);
          if (b === 0 || b === 2) arp(bt + 0.02, ch.arp);
        }
        pad(t + bar * 4 * beat, ch.pad);
      }
    }
    function loopSynthwave() { if (!playing) return; scheduleSynthwave(); loopTimers.push(setTimeout(loopSynthwave, 16000)); }

    var btn = doc.getElementById('tdmMusicBtn');
    if (btn) {
      btn.addEventListener('click', function() {
        if (!audioCtx) audioCtx = new (win.AudioContext || win.webkitAudioContext)();
        if (playing) {
          playing = false; loopTimers.forEach(function(t) { clearTimeout(t); }); loopTimers = [];
          btn.textContent = '🎵'; btn.classList.remove('playing');
        } else {
          playing = true; btn.textContent = '⏸'; btn.classList.add('playing');
          scheduleSynthwave(); loopTimers.push(setTimeout(loopSynthwave, 16000));
        }
      });
    }

    // ══════════════════════════════════════════════════════════════════════
    // CARRUSEL
    // ══════════════════════════════════════════════════════════════════════
    var track = doc.getElementById('carouselTrack');
    var prevBtn = doc.getElementById('carouselPrev');
    var nextBtn = doc.getElementById('carouselNext');
    var dotsContainer = doc.getElementById('carouselDots');

    if (track) {
      var autoInterval, hovering = false;
      var visibleCount = 3;

      function updateDots() {
        if (!dotsContainer) return;
        var scrollLeft = track.scrollLeft;
        var totalWidth = track.scrollWidth - track.clientWidth;
        var dots = dotsContainer.querySelectorAll('.carousel-dot');
        if (dots.length <= 1) return;
        var pageSize = totalWidth / (dots.length - 1);
        var activeIdx = Math.round(scrollLeft / pageSize);
        activeIdx = Math.max(0, Math.min(dots.length - 1, activeIdx));
        dots.forEach(function(d, i) {
          d.classList.toggle('active', i === activeIdx);
        });
      }

      function startAutoPlay() {
        if (autoInterval) clearInterval(autoInterval);
        autoInterval = setInterval(function() {
          if (hovering) return;
          var maxScroll = track.scrollWidth - track.clientWidth;
          var cardEl = track.querySelector('.game-card');
          var cw = cardEl ? cardEl.offsetWidth + 20 : 300;
          var nextPos = track.scrollLeft + cw * visibleCount;
          if (nextPos >= maxScroll - 5) nextPos = 0;
          track.scrollLeft = nextPos;
          updateDots();
        }, 4000);
      }

      track.addEventListener('mouseenter', function() { hovering = true; });
      track.addEventListener('mouseleave', function() { hovering = false; });

      if (prevBtn) prevBtn.addEventListener('click', function() {
        var cw = track.querySelector('.game-card');
        var w = cw ? cw.offsetWidth + 20 : 300;
        track.scrollLeft -= w * visibleCount; updateDots();
      });
      if (nextBtn) nextBtn.addEventListener('click', function() {
        var cw = track.querySelector('.game-card');
        var w = cw ? cw.offsetWidth + 20 : 300;
        track.scrollLeft += w * visibleCount; updateDots();
      });

      track.addEventListener('scroll', updateDots);

      if (dotsContainer) {
        dotsContainer.addEventListener('click', function(e) {
          var dot = e.target;
          if (!dot.classList.contains('carousel-dot')) return;
          var idx = parseInt(dot.getAttribute('data-index'), 10);
          if (isNaN(idx)) return;
          var totalWidth = track.scrollWidth - track.clientWidth;
          var dots = dotsContainer.querySelectorAll('.carousel-dot');
          var pageSize = totalWidth / (dots.length - 1);
          track.scrollLeft = idx * pageSize;
          updateDots();
        });
      }

      setTimeout(startAutoPlay, 2000);
    }

    // ══════════════════════════════════════════════════════════════════════
    // STAGGER ENTRY + TILT 3D + CLICK + COUNTERS
    // ══════════════════════════════════════════════════════════════════════
    doc.querySelectorAll('.game-card, .info-card').forEach(function(card, i) {
      card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      setTimeout(function() {
        card.style.opacity = '1';
        card.style.transform = 'translateY(0)';
      }, 400 + i * 60);
    });

    doc.querySelectorAll('.game-card, .info-card').forEach(function(card) {
      var inner = card.querySelector('.game-card-inner') || card.querySelector('.info-card-inner');
      if (!inner) return;
      card.addEventListener('mousemove', function(e) {
        var rect = card.getBoundingClientRect();
        var x = e.clientX - rect.left, y = e.clientY - rect.top;
        var cx = rect.width/2, cy = rect.height/2;
        inner.style.transform = 'rotateX(' + ((y-cy)/cy*-8) + 'deg) rotateY(' + ((x-cx)/cx*8) + 'deg)';
      });
      card.addEventListener('mouseleave', function() {
        inner.style.transform = 'rotateX(0deg) rotateY(0deg)';
      });
    });

    doc.querySelectorAll('.game-card').forEach(function(card) {
      card.addEventListener('click', function() {
        var g = card.getAttribute('data-game');
        if (!g) return;
        win.location.href = win.location.origin + win.location.pathname + '?game=' + encodeURIComponent(g);
      });
    });

    doc.querySelectorAll('.tdm-featured').forEach(function(card) {
      card.addEventListener('click', function() {
        var g = card.getAttribute('data-game');
        if (!g) return;
        win.location.href = win.location.origin + win.location.pathname + '?game=' + encodeURIComponent(g);
      });
    });

    doc.querySelectorAll('.tdm-stat-num[data-count]').forEach(function(el) {
      var target = parseInt(el.getAttribute('data-count'), 10);
      if (isNaN(target)) return;
      var start = performance.now();
      function step(now) {
        var p = Math.min((now - start) / 1000, 1);
        var cur = Math.round(p * target);
        el.textContent = target >= 1000000 ? (cur/1000000).toFixed(1) + 'M+' : cur;
        if (p < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    });
  } catch(e) {}
})();
</script>
""", height=0)
