"""
skin_tracker.py - 美容サロン 肌変化プログレストラッカー
お客様の肌の変化を写真と共に記録・AIで分析・可視化するサロン専用ツール
"""
import streamlit as st
import pandas as pd
import numpy as np
import json, os, base64, uuid, io, re
from datetime import datetime
from PIL import Image, ImageFilter, ImageEnhance

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

# ─── 定数 ───────────────────────────────────────────────────────────────
DATA_DIR   = "skin_data"
CUST_FILE  = os.path.join(DATA_DIR, "customers.json")
PHOTOS_DIR = os.path.join(DATA_DIR, "photos")

CONCERNS   = ["シミ・くすみ", "シワ・たるみ", "ほうれい線", "毛穴・ニキビ", "乾燥肌", "敏感肌", "その他"]
SKIN_TYPES = ["普通肌", "乾燥肌", "脂性肌", "混合肌", "敏感肌"]
SCORE_KEYS = ["シミ", "シワ", "ほうれい線", "肌トーン", "毛穴", "総合"]

# ─── データ管理 ──────────────────────────────────────────────────────────
def _ensure():
    os.makedirs(PHOTOS_DIR, exist_ok=True)
    if not os.path.exists(CUST_FILE):
        _write_json([])

def _write_json(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CUST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_all():
    _ensure()
    with open(CUST_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_customer(cid):
    return next((c for c in load_all() if c["id"] == cid), None)

def upsert_customer(c):
    data = load_all()
    idx = next((i for i, x in enumerate(data) if x["id"] == c["id"]), None)
    if idx is None:
        data.append(c)
    else:
        data[idx] = c
    _write_json(data)

def delete_customer(cid):
    _write_json([c for c in load_all() if c["id"] != cid])

# ─── 写真 I/O ────────────────────────────────────────────────────────────
def save_photo(cid: str, visit_num: int, raw: bytes) -> str:
    path = os.path.join(PHOTOS_DIR, f"{cid}_v{visit_num}.jpg")
    img = Image.open(io.BytesIO(raw))
    if max(img.size) > 1200:
        r = 1200 / max(img.size)
        img = img.resize((int(img.size[0]*r), int(img.size[1]*r)), Image.LANCZOS)
    img.convert("RGB").save(path, "JPEG", quality=85)
    return path

def load_photo(path: str) -> Image.Image | None:
    return Image.open(path) if path and os.path.exists(path) else None

def img_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG")
    return base64.b64encode(buf.getvalue()).decode()

# ─── 改善シミュレーション ────────────────────────────────────────────────
def simulate_improvement(img: Image.Image, level: int) -> Image.Image:
    """
    level 1 = 初回（原本）、level 2〜5 = 段階的改善シミュレーション
    シミ・くすみを局所的に明るくし、スキンスムージングで肌質改善を表現
    """
    if level <= 1:
        return img.copy().convert("RGB")

    strength = (level - 1) / 4.0  # 0.25 〜 1.0

    arr = np.array(img.convert("RGB")).astype(np.float64)

    # ── シミ低減：暗い点を周辺の明るさに近づける ──
    blurred = np.array(
        img.convert("RGB").filter(ImageFilter.GaussianBlur(radius=12))
    ).astype(np.float64)
    diff = blurred - arr
    mask = diff > 18  # 局所的に暗い部分（シミ候補）
    arr[mask] += diff[mask] * min(strength * 0.8, 0.85)

    result = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

    # ── 全体トーン調整 ──
    result = ImageEnhance.Brightness(result).enhance(1.0 + strength * 0.05)
    result = ImageEnhance.Color(result).enhance(1.0 + strength * 0.06)
    result = ImageEnhance.Sharpness(result).enhance(1.0 - strength * 0.15)

    # ── スキンスムージング ──
    for _ in range(int(strength * 2)):
        result = result.filter(ImageFilter.SMOOTH)

    return result

# ─── AI 肌分析（Claude Vision） ──────────────────────────────────────────
def analyze_skin(img: Image.Image, visit_num: int, prev_analysis: str | None = None) -> dict:
    if not HAS_ANTHROPIC:
        return {"error": "anthropicライブラリが未インストールです（pip install anthropic）"}

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        try:
            api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
        except Exception:
            pass
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY が設定されていません"}

    client = anthropic.Anthropic(api_key=api_key)
    b64 = img_to_b64(img)
    prev_block = f"\n\n【前回（第{visit_num-1}回）の分析結果】\n{prev_analysis}" if prev_analysis else ""

    prompt = f"""あなたは美容皮膚科・エステサロン専門の肌状態分析AIです。
この写真は第{visit_num}回目の施術記録です。

以下の項目を「改善度スコア（1=課題多い ／ 10=非常に良い状態）」で評価し、
お客様にお渡しできる丁寧な文章で説明してください。{prev_block}

【評価項目】
1. シミ（数・大きさ・色の濃さ）
2. シワ（額・目尻・口周り）
3. ほうれい線（深さと広がり）
4. 肌トーン（くすみ・透明感・明るさ）
5. 毛穴（開き・詰まり）
6. 総合スコア

{'【重要】前回の分析と比較して、改善した点と今後の課題を具体的に記述してください。' if prev_analysis else ''}

説明文の最後に、必ず以下の形式でスコアをJSON出力してください：
SCORES: {{"シミ": 数値, "シワ": 数値, "ほうれい線": 数値, "肌トーン": 数値, "毛穴": 数値, "総合": 数値}}"""

    try:
        msg = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=1800,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
                    {"type": "text", "text": prompt}
                ]
            }]
        )
        text = msg.content[0].text
        scores = {}
        m = re.search(r'SCORES:\s*(\{[^}]+\})', text)
        if m:
            try:
                scores = json.loads(m.group(1))
                text = text[:m.start()].strip()
            except Exception:
                pass
        return {"analysis": text, "scores": scores}
    except Exception as e:
        return {"error": str(e)}

# ─── スタイル ────────────────────────────────────────────────────────────
st.set_page_config(page_title="肌変化プログレストラッカー", page_icon="💆", layout="wide")
st.markdown("""
<style>
:root{--rose:#e84393;--pink:#f8a5c2;--cream:#fff9f5;--border:#f0dde8;--text:#3a3a3a;}
.block-container{padding:1.5rem 2rem;max-width:1300px;}
.section-hd{font-size:1.05rem;font-weight:bold;color:var(--rose);
  border-left:4px solid var(--rose);padding-left:.6rem;margin:1rem 0 .7rem;}
.score-chip{display:inline-block;padding:2px 10px;border-radius:999px;font-size:.8rem;
  font-weight:bold;background:#fce4ec;color:var(--rose);margin:2px;}
.sim-label{text-align:center;font-size:.78rem;color:#888;margin-top:4px;}
</style>
""", unsafe_allow_html=True)

# ─── セッション初期化 ─────────────────────────────────────────────────────
for k, v in [("page", "home"), ("sel_cid", None), ("confirm_del", False)]:
    if k not in st.session_state:
        st.session_state[k] = v

def go(page: str, cid: str | None = None):
    st.session_state.page = page
    if cid is not None:
        st.session_state.sel_cid = cid
    st.session_state.confirm_del = False
    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# ページ：ホーム（顧客一覧）
# ═══════════════════════════════════════════════════════════════════════════
def page_home():
    st.markdown("## 💆 肌変化プログレストラッカー")
    st.caption("お客様の肌の変化を記録・AIで分析・可視化するサロン専用ツール")

    col_add, col_srch = st.columns([1, 4])
    with col_add:
        if st.button("＋ お客様を追加", type="primary", use_container_width=True):
            go("add")
    with col_srch:
        keyword = st.text_input("🔍 名前で検索", placeholder="お客様名...", label_visibility="collapsed")

    customers = load_all()
    if keyword:
        customers = [c for c in customers if keyword in c.get("name", "")]

    if not customers:
        st.info("まだ顧客登録がありません。「＋ お客様を追加」からご登録ください。")
        return

    st.markdown(f"<div class='section-hd'>登録顧客 {len(customers)} 名</div>", unsafe_allow_html=True)

    cols = st.columns(4)
    for i, c in enumerate(customers):
        visits = c.get("visits", [])
        with cols[i % 4]:
            with st.container(border=True):
                # 最新写真サムネイル
                latest_photo = None
                for v in reversed(visits):
                    img = load_photo(v.get("photo_path"))
                    if img:
                        latest_photo = img
                        break
                if latest_photo:
                    st.image(latest_photo, use_container_width=True)
                else:
                    st.markdown("🙎 写真なし", unsafe_allow_html=False)

                st.markdown(f"**{c['name']}** さん")
                last = visits[-1]["date"] if visits else "施術前"
                st.caption(f"施術 {len(visits)} 回 ／ 最終: {last}")
                if c.get("concerns"):
                    st.caption("お悩み: " + "・".join(c["concerns"]))

                if st.button("詳細を見る →", key=f"v_{c['id']}", use_container_width=True):
                    go("detail", c["id"])

# ═══════════════════════════════════════════════════════════════════════════
# ページ：顧客追加
# ═══════════════════════════════════════════════════════════════════════════
def page_add():
    st.markdown("## ＋ 新規お客様登録")

    with st.form("add_form", clear_on_submit=True):
        name = st.text_input("お名前 *", placeholder="山田 花子")
        c1, c2 = st.columns(2)
        with c1:
            age = st.number_input("年齢", 15, 100, 35)
        with c2:
            skin_type = st.selectbox("肌タイプ", SKIN_TYPES)
        concerns = st.multiselect("お悩み（複数可）", CONCERNS)
        memo = st.text_area("メモ・特記事項", placeholder="アレルギー、注意事項など")

        c_sub, c_can = st.columns([1, 5])
        with c_sub:
            submitted = st.form_submit_button("登録", type="primary")
        with c_can:
            if st.form_submit_button("キャンセル"):
                go("home")

    if submitted:
        if not name.strip():
            st.error("お名前を入力してください")
            return
        new_c = {
            "id": str(uuid.uuid4()),
            "name": name.strip(),
            "age": int(age),
            "skin_type": skin_type,
            "concerns": concerns,
            "memo": memo,
            "created_at": datetime.now().strftime("%Y-%m-%d"),
            "visits": []
        }
        upsert_customer(new_c)
        st.success(f"{name} さんを登録しました！")
        go("detail", new_c["id"])

# ═══════════════════════════════════════════════════════════════════════════
# ページ：顧客詳細
# ═══════════════════════════════════════════════════════════════════════════
def page_detail():
    cid = st.session_state.sel_cid
    c = get_customer(cid)
    if not c:
        go("home")
        return

    # ── ヘッダー ──
    hcol1, hcol2, hcol3 = st.columns([1, 7, 1])
    with hcol1:
        if st.button("← 一覧"):
            go("home")
    with hcol2:
        st.markdown(f"## 💆 {c['name']} さんの記録")
    with hcol3:
        if st.button("✏️ 編集"):
            go("edit", cid)

    # ── 基本情報 ──
    with st.expander("👤 基本情報", expanded=False):
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("年齢", f"{c.get('age','-')} 歳")
        mc2.metric("肌タイプ", c.get("skin_type", "-"))
        mc3.metric("施術回数", f"{len(c.get('visits',[]))} 回")
        mc4.metric("登録日", c.get("created_at", "-"))
        if c.get("concerns"):
            st.write("お悩み:", "・".join(c["concerns"]))
        if c.get("memo"):
            st.info(c["memo"])

    visits = c.get("visits", [])
    tab_tl, tab_ba, tab_sim, tab_up = st.tabs(
        ["📅 タイムライン", "🔁 ビフォーアフター", "✨ 改善シミュレーション", "📷 写真を追加"]
    )

    # ────────────────────────────────────────────────────────────────────
    # タブ①：タイムライン
    # ────────────────────────────────────────────────────────────────────
    with tab_tl:
        if not visits:
            st.info("まだ記録がありません。「写真を追加」タブから登録してください。")
        else:
            # スコア推移グラフ
            score_rows = []
            for v in visits:
                s = v.get("scores", {})
                if s:
                    score_rows.append({"回数": f"第{v['visit_num']}回", **{k: s.get(k) for k in SCORE_KEYS if k in s}})
            if score_rows:
                st.markdown("<div class='section-hd'>スコア推移（↑ 改善）</div>", unsafe_allow_html=True)
                df = pd.DataFrame(score_rows).set_index("回数")
                st.line_chart(df, height=220)

            # 写真グリッド
            st.markdown("<div class='section-hd'>施術記録</div>", unsafe_allow_html=True)
            n = len(visits)
            grid_cols = st.columns(min(n, 5))
            for i, v in enumerate(visits):
                with grid_cols[i % 5]:
                    img = load_photo(v.get("photo_path"))
                    label = f"第{v['visit_num']}回\n{v['date']}"
                    if img:
                        st.image(img, caption=label, use_container_width=True)
                    else:
                        st.markdown(f"**{label}**")
                    sc = v.get("scores", {}).get("総合")
                    if sc:
                        st.caption(f"総合スコア: {sc}/10")
                    with st.expander("AI分析"):
                        if v.get("analysis"):
                            st.write(v["analysis"])
                        else:
                            st.caption("分析データなし")

    # ────────────────────────────────────────────────────────────────────
    # タブ②：ビフォーアフター
    # ────────────────────────────────────────────────────────────────────
    with tab_ba:
        if len(visits) < 2:
            st.info("ビフォーアフター比較には 2 回以上の記録が必要です。")
        else:
            visit_labels = [f"第{v['visit_num']}回（{v['date']}）" for v in visits]
            bc1, bc2 = st.columns(2)

            with bc1:
                st.markdown("**比較元（ビフォー）**")
                b_idx = st.selectbox("", range(len(visits)), format_func=lambda x: visit_labels[x], key="b_sel", label_visibility="collapsed")
                b_img = load_photo(visits[b_idx].get("photo_path"))
                if b_img:
                    st.image(b_img, use_container_width=True)
                b_sc = visits[b_idx].get("scores", {})
                if b_sc:
                    for k, val in b_sc.items():
                        st.markdown(f"<span class='score-chip'>{k}: {val}</span>", unsafe_allow_html=True)

            with bc2:
                st.markdown("**比較先（アフター）**")
                a_idx = st.selectbox("", range(len(visits)), index=len(visits)-1, format_func=lambda x: visit_labels[x], key="a_sel", label_visibility="collapsed")
                a_img = load_photo(visits[a_idx].get("photo_path"))
                if a_img:
                    st.image(a_img, use_container_width=True)
                a_sc = visits[a_idx].get("scores", {})
                if a_sc:
                    for k, val in a_sc.items():
                        st.markdown(f"<span class='score-chip'>{k}: {val}</span>", unsafe_allow_html=True)

            # スコア変化メトリクス
            if b_sc and a_sc:
                st.markdown("<div class='section-hd'>スコア変化</div>", unsafe_allow_html=True)
                common = [k for k in SCORE_KEYS if k in b_sc and k in a_sc]
                if common:
                    met_cols = st.columns(len(common))
                    for ci, key in enumerate(common):
                        delta = a_sc[key] - b_sc[key]
                        met_cols[ci].metric(key, f"{a_sc[key]}/10", f"{delta:+}", delta_color="normal")

    # ────────────────────────────────────────────────────────────────────
    # タブ③：改善シミュレーション
    # ────────────────────────────────────────────────────────────────────
    with tab_sim:
        st.markdown("### ✨ 施術改善シミュレーション")
        st.caption("初回写真をベースに、施術回数に応じた肌改善をシミュレーションします。あくまで参考イメージです。")

        sim_base = None
        if visits:
            for v in visits:
                img = load_photo(v.get("photo_path"))
                if img:
                    sim_base = img
                    break

        if sim_base is None:
            st.info("シミュレーションには写真が 1 枚以上必要です。")
        else:
            sim_labels = ["初回（現在）", "2回目イメージ", "3回目イメージ", "4回目イメージ", "5回目イメージ"]
            sim_cols = st.columns(5)
            for lvl, (col, lbl) in enumerate(zip(sim_cols, sim_labels), start=1):
                with col:
                    st.image(simulate_improvement(sim_base, lvl), use_container_width=True)
                    st.markdown(f"<div class='sim-label'>{lbl}</div>", unsafe_allow_html=True)

            st.warning("⚠️ シミュレーション画像は参考イメージです。実際の効果は施術内容・個人差により異なります。")

    # ────────────────────────────────────────────────────────────────────
    # タブ④：写真アップロード
    # ────────────────────────────────────────────────────────────────────
    with tab_up:
        next_num = len(visits) + 1
        st.markdown(f"### 📷 第 {next_num} 回目の記録を追加")

        with st.form("upload_form"):
            visit_date = st.date_input("施術日", value=datetime.today())
            treatment  = st.text_input("施術内容", placeholder="フォトフェイシャル、シミ取りレーザーなど")
            notes      = st.text_area("メモ・所見", placeholder="お客様のコメント、スタッフ所見など")
            uploaded   = st.file_uploader("写真をアップロード *", type=["jpg", "jpeg", "png"])
            run_ai     = st.checkbox(
                "🤖 AI で肌状態を分析する（ANTHROPIC_API_KEY が必要）",
                value=HAS_ANTHROPIC and bool(os.environ.get("ANTHROPIC_API_KEY"))
            )
            submit_btn = st.form_submit_button(f"第 {next_num} 回を記録する", type="primary")

        if submit_btn:
            if not uploaded:
                st.error("写真をアップロードしてください")
            else:
                with st.spinner("保存・分析中..."):
                    photo_path = save_photo(cid, next_num, uploaded.read())
                    img = load_photo(photo_path)

                    entry = {
                        "visit_num":  next_num,
                        "date":       visit_date.strftime("%Y-%m-%d"),
                        "treatment":  treatment,
                        "notes":      notes,
                        "photo_path": photo_path,
                        "analysis":   None,
                        "scores":     {}
                    }

                    if run_ai and img:
                        prev = visits[-1].get("analysis") if visits else None
                        result = analyze_skin(img, next_num, prev)
                        if "error" in result:
                            st.warning(f"AI分析をスキップしました: {result['error']}")
                        else:
                            entry["analysis"] = result.get("analysis", "")
                            entry["scores"]   = result.get("scores", {})

                    c["visits"].append(entry)
                    upsert_customer(c)

                st.success(f"✅ 第 {next_num} 回目の記録を保存しました！")

                if img:
                    st.image(img, caption=f"第 {next_num} 回 / {visit_date}", width=350)

                if entry.get("analysis"):
                    st.markdown("#### AI 肌分析レポート")
                    st.write(entry["analysis"])
                    if entry.get("scores"):
                        sc_cols = st.columns(len(entry["scores"]))
                        for ci, (k, val) in enumerate(entry["scores"].items()):
                            sc_cols[ci].metric(k, f"{val}/10")

# ═══════════════════════════════════════════════════════════════════════════
# ページ：顧客編集
# ═══════════════════════════════════════════════════════════════════════════
def page_edit():
    cid = st.session_state.sel_cid
    c = get_customer(cid)
    if not c:
        go("home")
        return

    st.markdown(f"## ✏️ {c['name']} さんの情報を編集")

    with st.form("edit_form"):
        name = st.text_input("お名前", value=c.get("name", ""))
        e1, e2 = st.columns(2)
        with e1:
            age = st.number_input("年齢", 15, 100, value=c.get("age", 35))
        with e2:
            si = SKIN_TYPES.index(c.get("skin_type", SKIN_TYPES[0])) if c.get("skin_type") in SKIN_TYPES else 0
            skin_type = st.selectbox("肌タイプ", SKIN_TYPES, index=si)
        concerns = st.multiselect("お悩み", CONCERNS, default=c.get("concerns", []))
        memo = st.text_area("メモ", value=c.get("memo", ""))

        s1, s2, s3 = st.columns([1, 1, 5])
        with s1:
            saved   = st.form_submit_button("保存", type="primary")
        with s2:
            deleted = st.form_submit_button("削除", type="secondary")
        with s3:
            if st.form_submit_button("キャンセル"):
                go("detail", cid)

    if saved:
        c.update({"name": name, "age": int(age), "skin_type": skin_type, "concerns": concerns, "memo": memo})
        upsert_customer(c)
        st.success("保存しました")
        go("detail", cid)

    if deleted:
        if st.session_state.confirm_del:
            delete_customer(cid)
            st.success("削除しました")
            go("home")
        else:
            st.session_state.confirm_del = True
            st.error("⚠️ もう一度「削除」を押すと完全に削除されます。")

# ═══════════════════════════════════════════════════════════════════════════
# ルーター
# ═══════════════════════════════════════════════════════════════════════════
{
    "home":   page_home,
    "add":    page_add,
    "detail": page_detail,
    "edit":   page_edit,
}.get(st.session_state.page, page_home)()
