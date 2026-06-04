BASE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;700&family=Inter:wght@400;500&family=Orbitron:wght@700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #0b0e1a; color: #e8eaf6; overflow-x: hidden; }

.stApp::before {
    content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background-image:
        radial-gradient(1px 1px at 10% 20%, rgba(124,106,245,0.4), transparent),
        radial-gradient(1px 1px at 30% 60%, rgba(240,98,146,0.3), transparent),
        radial-gradient(1.5px 1.5px at 50% 10%, rgba(38,198,218,0.4), transparent),
        radial-gradient(1px 1px at 70% 40%, rgba(124,106,245,0.3), transparent),
        radial-gradient(1.5px 1.5px at 90% 80%, rgba(240,98,146,0.3), transparent),
        radial-gradient(1px 1px at 20% 90%, rgba(38,198,218,0.3), transparent),
        radial-gradient(1px 1px at 80% 15%, rgba(124,106,245,0.25), transparent),
        radial-gradient(1.5px 1.5px at 45% 75%, rgba(240,98,146,0.25), transparent),
        radial-gradient(1px 1px at 15% 45%, rgba(38,198,218,0.35), transparent),
        radial-gradient(1px 1px at 65% 55%, rgba(124,106,245,0.3), transparent),
        radial-gradient(1.5px 1.5px at 88% 35%, rgba(240,98,146,0.25), transparent),
        radial-gradient(1px 1px at 5% 70%, rgba(38,198,218,0.3), transparent),
        radial-gradient(1px 1px at 55% 88%, rgba(124,106,245,0.25), transparent),
        radial-gradient(1.5px 1.5px at 75% 5%, rgba(240,98,146,0.3), transparent),
        radial-gradient(1px 1px at 35% 30%, rgba(38,198,218,0.3), transparent);
    background-size: 200% 200%;
    animation: driftParticles 20s ease-in-out infinite alternate;
}
@keyframes driftParticles {
    0%   { background-position: 0% 0%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 100%; }
}
.stApp::after {
    content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.025) 2px, rgba(0,0,0,0.025) 4px);
}
#MainMenu, footer, header { visibility: hidden; }

/* ── Header ── */
.tdm-topbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.5rem 0 0.8rem 0; margin-bottom: 3rem; position: relative; z-index: 2;
}
.tdm-logo {
    font-family: 'Rajdhani', sans-serif; font-size: 20px; font-weight: 700; letter-spacing: 2px;
    background: linear-gradient(90deg, #f06292, #7c6af5, #26c6da);
    background-size: 200% auto;
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    animation: gradienteLogo 4s ease-in-out infinite alternate;
}
@keyframes gradienteLogo {
    0%   { background-position: 0% center; }
    100% { background-position: 200% center; }
}
.tdm-actions { display: flex; align-items: center; gap: 10px; }
.tdm-music-btn {
    font-size: 15px; width: 32px; height: 32px;
    display: flex; align-items: center; justify-content: center;
    border-radius: 50%; cursor: pointer; user-select: none;
    border: 1px solid rgba(124,106,245,0.3);
    background: rgba(124,106,245,0.08);
    color: #a99cf5; transition: all 0.2s ease;
}
.tdm-music-btn:hover {
    background: rgba(124,106,245,0.2);
    border-color: rgba(124,106,245,0.6);
    box-shadow: 0 0 16px rgba(124,106,245,0.25);
}
.tdm-music-btn.playing { border-color: #26c6da; box-shadow: 0 0 16px rgba(38,198,218,0.3); }
.tdm-user {
    font-size: 12px; color: #e8eaf6;
    padding: 3px 12px; border: 1px solid rgba(255,255,255,0.1); border-radius: 20px;
}

/* ── Page container ── */
.tdm-page {
    max-width: 1200px; margin: 0 auto; position: relative; z-index: 1;
    background: #0b0e1a;
    padding: 0 0 2rem 0;
}

/* ── Stats ── */
.tdm-stats {
    position: relative; z-index: 1;
    display: flex; gap: 1.5rem;
    padding: 1rem 1.2rem;
    background: #0b0e1a;
    border: 1px solid rgba(124,106,245,0.35);
    border-radius: 12px; margin-bottom: 4rem;
    box-shadow: 0 4px 16px rgba(0,0,0,0.4);
}
.tdm-stat-item { flex: 1; text-align: center; transition: transform 0.3s ease; }
.tdm-stat-item:hover { transform: scale(1.08); }
.tdm-stat-num {
    font-family: 'Rajdhani', sans-serif; font-size: 22px; font-weight: 700;
    background: linear-gradient(135deg, #f06292, #7c6af5);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.tdm-stat-lbl {
    font-size: 11px; text-transform: uppercase; letter-spacing: 1px;
    color: #e8eaf6; margin-top: 2px;
}

/* ── Section titles ── */
.tdm-section-title {
    font-family: 'Rajdhani', sans-serif; font-size: 24px; font-weight: 700;
    margin: 3rem 0 0.3rem 0; position: relative; z-index: 1;
}
.tdm-section-sub {
    font-size: 14px; color: #e8eaf6;
    margin-bottom: 1.2rem; position: relative; z-index: 1;
}

/* ── Info cards ── */
.info-card {
    perspective: 800px; margin-bottom: 1.5rem;
    position: relative; z-index: 1;
}
.info-card-inner {
    position: relative; z-index: 1;
    background: #0b0e1a;
    border: 1px solid rgba(124,106,245,0.35);
    border-radius: 12px; padding: 1.2rem 1rem;
    height: 100%; text-align: center;
    box-shadow: 0 4px 16px rgba(0,0,0,0.4);
    transition: transform 0.2s ease, box-shadow 0.3s ease;
    transform-style: preserve-3d; will-change: transform;
}
.info-card-inner::before {
    content: ""; position: absolute; inset: -1px; border-radius: 12px;
    opacity: 0; transition: opacity 0.3s ease; pointer-events: none;
}
.info-card:nth-child(1) .info-card-inner::before { background: linear-gradient(135deg, rgba(240,98,146,0.15), transparent); }
.info-card:nth-child(2) .info-card-inner::before { background: linear-gradient(135deg, rgba(124,106,245,0.15), transparent); }
.info-card:nth-child(3) .info-card-inner::before { background: linear-gradient(135deg, rgba(38,198,218,0.15), transparent); }
.info-card:hover .info-card-inner { transform: translateY(-4px); }
.info-card:hover .info-card-inner::before { opacity: 1; }
.info-card:nth-child(1):hover .info-card-inner { box-shadow: 0 8px 24px rgba(240,98,146,0.15); }
.info-card:nth-child(2):hover .info-card-inner { box-shadow: 0 8px 24px rgba(124,106,245,0.15); }
.info-card:nth-child(3):hover .info-card-inner { box-shadow: 0 8px 24px rgba(38,198,218,0.15); }
.info-card-letter {
    display: inline-block;
    font-family: 'Rajdhani', sans-serif;
    font-size: 34px; font-weight: 700; line-height: 1;
    margin-bottom: 8px;
}
.info-card-title {
    font-family: 'Rajdhani', sans-serif; font-size: 18px; font-weight: 700;
    color: #f0f2ff; margin-bottom: 4px;
    text-shadow: 0 1px 10px rgba(0,0,0,0.4);
}
.info-card-desc { font-size: 13px; color: #e8eaf6; line-height: 1.5; text-shadow: 0 1px 8px rgba(0,0,0,0.3); }

/* ── Separador ── */
.tdm-divider {
    position: relative; z-index: 1;
    height: 1px; margin: 1.2rem 0 1.5rem 0;
    background: linear-gradient(90deg, transparent, rgba(124,106,245,0.2), rgba(124,106,245,0.4), rgba(124,106,245,0.2), transparent);
}

/* ── Carrusel ── */
.carousel-container {
    position: relative; z-index: 1; margin: 2rem 0 4rem 0;
}
.carousel-track {
    display: flex; gap: 20px;
    overflow-x: hidden;
    scroll-behavior: smooth;
    padding: 8px 2px;
    -ms-overflow-style: none; scrollbar-width: none;
}
.carousel-track::-webkit-scrollbar { display: none; }
.carousel-track .game-card {
    flex: 0 0 calc(33.333% - 14px);
    min-width: 260px;
    margin-bottom: 0;
}
.carousel-arrow {
    position: absolute; top: 50%; transform: translateY(-50%);
    width: 40px; height: 40px;
    display: flex; align-items: center; justify-content: center;
    border-radius: 50%;
    background: rgba(11,14,26,0.85);
    border: 1px solid rgba(124,106,245,0.3);
    color: #e8eaf6; font-size: 24px; font-family: 'Rajdhani', sans-serif;
    cursor: pointer; z-index: 10;
    transition: all 0.2s ease; user-select: none;
}
.carousel-arrow:hover {
    background: rgba(124,106,245,0.2);
    border-color: rgba(124,106,245,0.6);
    box-shadow: 0 0 20px rgba(124,106,245,0.3);
    color: #f0f2ff;
}
.carousel-arrow-left { left: -16px; }
.carousel-arrow-right { right: -16px; }
.carousel-dots {
    display: flex; justify-content: center; gap: 8px; margin-top: 6px;
}
.carousel-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: rgba(124,106,245,0.15);
    border: 1px solid rgba(124,106,245,0.1);
    cursor: pointer; transition: all 0.3s ease;
}
.carousel-dot.active {
    background: #7c6af5; border-color: #7c6af5;
    box-shadow: 0 0 10px rgba(124,106,245,0.6);
    width: 22px; border-radius: 4px;
}

/* ── Game cards ── */
.game-card { perspective: 800px; position: relative; z-index: 1; cursor: pointer; }
.game-card-inner {
    position: relative; z-index: 1;
    background: #0b0e1a;
    border: 1px solid rgba(124,106,245,0.35);
    border-radius: 12px; overflow: visible;
    box-shadow: 0 4px 16px rgba(0,0,0,0.4);
    transition: transform 0.15s ease, box-shadow 0.3s ease, border-color 0.3s ease;
    transform-style: preserve-3d; will-change: transform;
}
.game-card-inner::before {
    content: ""; position: absolute; inset: -2px; border-radius: 14px;
    background: linear-gradient(135deg, transparent 0%, rgba(240,98,146,0.15) 25%, rgba(124,106,245,0.20) 50%, rgba(38,198,218,0.15) 75%, transparent 100%);
    background-size: 300% 300%; opacity: 0; transition: opacity 0.3s ease;
    pointer-events: none; z-index: 0;
}
.game-card:hover .game-card-inner {
    border-color: #7c6af5;
    box-shadow: 0 8px 32px rgba(124,106,245,0.35), 0 4px 16px rgba(0,0,0,0.4);
}
.game-card:hover .game-card-inner::before { opacity: 1; animation: shimmer 2.5s ease-in-out infinite; }
.game-card:active .game-card-inner { transform: scale(0.95) !important; }
@keyframes shimmer {
    0%   { background-position: 0% 0%; }
    50%  { background-position: 100% 100%; }
    100% { background-position: 0% 0%; }
}
.game-card-img {
    width: 100%; height: 200px; object-fit: cover; display: block;
    border-radius: 12px 12px 0 0; position: relative; z-index: 1;
}
.game-card-body { padding: 12px; position: relative; z-index: 1; }
.game-card-title {
    font-family: 'Rajdhani', sans-serif; font-size: 17px; font-weight: 700;
    color: #f0f2ff; margin-bottom: 4px; line-height: 1.2;
    text-shadow: 0 1px 10px rgba(0,0,0,0.4);
}
.game-tags { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 8px; }
.game-tag {
    font-size: 10px; padding: 2px 7px; border-radius: 4px;
    background: rgba(124,106,245,0.12); color: #e8eaf6;
    border: 1px solid rgba(124,106,245,0.2); text-transform: uppercase;
}
.game-meta { display: flex; align-items: center; justify-content: space-between; margin-top: 6px; }
.rating-pill { font-size: 10px; padding: 2px 8px; border-radius: 4px; }
.r-pos { background: rgba(38,198,218,0.1); color: #26c6da; border: 1px solid rgba(38,198,218,0.25); }
.r-mix { background: rgba(255,183,77,0.1); color: #ffb74d; border: 1px solid rgba(255,183,77,0.25); }
.r-neg { background: rgba(239,83,80,0.1); color: #ef5350; border: 1px solid rgba(239,83,80,0.25); }
.game-price {
    font-family: 'Rajdhani', sans-serif; font-size: 14px; font-weight: 700; color: #f0f2ff;
}
.price-free { color: #26c6da !important; }

/* ── Footer ── */
.tdm-footer {
    position: relative; z-index: 1;
    margin-top: 3rem; padding: 1.5rem 0;
    text-align: center; font-size: 11px; color: #e8eaf6;
    border-top: 1px solid rgba(255,255,255,0.03);
}
.tdm-footer-line { margin: 2px 0; }
.tdm-footer-grad { color: rgba(124,106,245,0.7); }

/* ── Sidebar ── */
section[data-testid="stSidebar"] { background: #0b0e1a; }

/* ── Filter section ── */
.tdm-filter-bar { position: relative; z-index: 1; margin: 1.5rem 0; }
.tdm-filter-bar .stTextInput>div>div>input,
.tdm-filter-bar .stSelectbox>div>div>div,
.tdm-filter-bar .stMultiSelect>div>div>div,
.tdm-filter-bar .stSlider>div>div>div {
    background: rgba(255,255,255,0.03) !important;
    border-color: rgba(255,255,255,0.1) !important;
    color: #e8eaf6 !important;
}
.tdm-filter-bar label { color: #e8eaf6 !important; font-size: 12px !important; }
.tdm-filter-bar .stSlider label { color: #e8eaf6 !important; }

/* ── Category rows (Netflix-style) ── */
.cat-row { position: relative; z-index: 1; margin-bottom: 2.5rem; }
.cat-title {
    font-family: 'Rajdhani', sans-serif; font-size: 20px; font-weight: 700;
    color: #f0f2ff; margin-bottom: 0.5rem; padding-left: 2px;
    text-shadow: 0 1px 10px rgba(0,0,0,0.4);
}
.cat-wrapper {
    position: relative; display: flex; align-items: center;
}
.cat-track {
    display: flex; gap: 16px; overflow-x: auto;
    scroll-behavior: smooth; padding: 8px 2px; flex: 1;
    -ms-overflow-style: none; scrollbar-width: none;
}
.cat-track::-webkit-scrollbar { display: none; }
.cat-track .game-card {
    flex: 0 0 calc(20% - 14px); min-width: 240px;
    margin-bottom: 0;
}
@media (max-width: 1100px) {
    .cat-track .game-card { flex: 0 0 calc(25% - 14px); min-width: 210px; }
}
@media (max-width: 800px) {
    .cat-track .game-card { flex: 0 0 calc(33.333% - 12px); min-width: 180px; }
}
.cat-arrow {
    width: 36px; height: 36px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    border-radius: 50%;
    background: rgba(11,14,26,0.85);
    border: 1px solid rgba(124,106,245,0.3);
    color: #e8eaf6; font-size: 22px; font-family: 'Rajdhani', sans-serif;
    cursor: pointer; z-index: 10;
    transition: all 0.2s ease; user-select: none;
}
.cat-arrow:hover {
    background: rgba(124,106,245,0.2);
    border-color: rgba(124,106,245,0.6);
    box-shadow: 0 0 20px rgba(124,106,245,0.3);
    color: #f0f2ff;
}
</style>
"""
