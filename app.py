# app.py
# SBレスキュー（URL読み込み／単一ファイル 完成版）
# - 入力：自店URL + 競合URL（最大20）
# - 取得：requests + BeautifulSoup(html.parser) ＊lxml不要
# - 判定：競合がジャンル下限を下回った時のみアラート
# - 優先：フェイシャル > 痩身 > ブライダル > 脱毛 > その他
# - 提案：下限と競合の中間（100円単位丸め）
# - 履歴：90日保持（CSV）、状態：未対応/対応済み/スヌーズ

import os, re
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import streamlit as st

# ====== 定数 ======
JST = timezone(timedelta(hours=9))
GENRE_MASTER = [
    "フェイシャル","痩身","脱毛","ブライダル",
    "バストケア","シェービング","ヨガ・ピラティス・加圧","その他"
]
PRIORITY_ORDER = {
    "フェイシャル":0,"痩身":1,"ブライダル":2,"脱毛":3,
    "その他":4,"バストケア":4,"シェービング":4,"ヨガ・ピラティス・加圧":4
}
HISTORY_FILE = "alert_history.csv"
HISTORY_COLS = [
    "date","salon_name","genre","coupon_name","price",
    "lower_limit","diff","suggested_price","url","state"
]

# ====== ページ設定 / スタイル（リスくん：打合せ版） ======
st.set_page_config(page_title="SBレスキュー", page_icon="💬", layout="wide")
st.markdown("""
<style>
:root{
  --nut:#8B5E3C; --nut-light:#C49A6C; --border:#E7D8C9;
  --ok:#EFFFF6; --warn:#FFF6E6; --err:#FFECEC; --txt:#2b2b2b;
}
.block-container{padding-top:10px;padding-bottom:24px}
.ris-wrap{position:fixed; right:18px; bottom:18px; z-index:9999;}
.ris-icon{
  width:48px;height:48px;border-radius:50%;
  background: radial-gradient(circle, var(--nut) 0%, var(--nut-light) 85%);
  display:flex;align-items:center;justify-content:center;color:#fff;font-size:22px;
  box-shadow:0 8px 20px rgba(139,94,60,.35); animation:breath 3s ease-in-out infinite;
}
@keyframes breath{0%{transform:scale(1)}50%{transform:scale(1.04)}100%{transform:scale(1)}}
.ris-bubble{
  max-width:520px; background:#fff; border:1px solid var(--border); border-radius:16px;
  box-shadow:0 10px 30px rgba(0,0,0,.08);
  margin-top:8px; padding:10px 14px; color:var(--txt); animation:fade .25s ease;
}
.ris-bubble.ok{background:var(--ok)} .ris-bubble.warn{background:var(--warn)} .ris-bubble.err{background:var(--err)}
@keyframes fade{from{opacity:0; transform:translateY(6px)} to{opacity:1; transform:translateY(0)}}
.kpi{background:#fff;border:1px solid var(--border);border-radius:12px;padding:14px 16px;text-align:center;
 box-shadow:0 3px 10px rgba(0,0,0,.08)}
.kpi h3{margin:.2rem 0 .4rem 0}
.badge{display:inline-block;padding:.1rem .5rem;border-radius:999px;border:1px solid var(--border);background:#fff}
hr{border:none;border-top:1px solid var(--border);margin:12px 0}
</style>
<div class="ris-wrap" id="ris-root"></div>
""", unsafe_allow_html=True)

RIS_ICON_HTML = "🐿️"
def ris_says(msg: str, tone: str=""):
    tone_cls = {"ok":" ok", "warn":" warn", "err":" err"}.get(tone, "")
    st.markdown(f"""
    <div class="ris-wrap">
      <div class="ris-icon">{RIS_ICON_HTML}</div>
      <div class="ris-bubble{tone_cls}">{msg}</div>
    </div>
    """, unsafe_allow_html=True)

# ====== URL取得・解析 ======
import requests
from bs4 import BeautifulSoup

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_html(url: str) -> str:
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (SB-Rescue/1.0)"}, timeout=15)
        r.raise_for_status()
        return r.text
    except Exception:
        return ""

KEYWORDS_BY_GENRE = {
    "フェイシャル": ["フェイシャル","小顔","毛穴","美肌","顔"],
    "痩身": ["痩身","スリム","リンパ","デトックス","ボディ"],
    "脱毛": ["脱毛"],
    "ブライダル": ["ブライダル","花嫁"],
    "バストケア": ["バスト","胸"],
    "シェービング": ["シェービング","顔そり","ブライダルシェーブ"],
    "ヨガ・ピラティス・加圧": ["ヨガ","ピラティス","加圧"],
    "その他": []
}
def normalize_genre(text: str) -> str:
    t = str(text)
    for g, kws in KEYWORDS_BY_GENRE.items():
        if any(kw in t for kw in kws):
            return g
    return "その他"

# --- 価格パーサ（誤検出を抑制） ---
PRICE_RE = re.compile(r"(?:¥|￥)?\s*([1-9]\d{2,5})\s*円")  # 3〜6桁
MIN_PRICE, MAX_PRICE = 800, 100000
NG_NEAR = ["割引","引き","OFF","オフ","+","追加","延長","オプション","学割","回数券","ポイント","g","Ｇ","ｇ"]
COUPON_KEYWORDS = ["クーポン","メニュー","コース","予約","特別","新規","再来","限定"]

def _is_couponish_block(text: str) -> bool:
    return any(k in text[:800] for k in COUPON_KEYWORDS)

def _valid_price_candidates(text: str):
    cand = []
    for m in PRICE_RE.finditer(text):
        price = int(m.group(1))
        if not (MIN_PRICE <= price <= MAX_PRICE):
            continue
        s = max(0, m.start()-18); e = min(len(text), m.end()+18)
        around = text[s:e]
        if any(ng in around for ng in NG_NEAR):
            continue
        cand.append(price)
    return cand

def parse_coupons_from_html(html: str):
    """HTMLから (coupon_name, price, genre) を抽出。"""
    out = []
    if not html: return out
    soup = BeautifulSoup(html, "html.parser")
    blocks = soup.find_all(["article","section","li","div"])
    for b in blocks:
        text = " ".join(b.stripped_strings)
        if not _is_couponish_block(text):
            continue
        prices = _valid_price_candidates(text)
        if not prices:
            continue
        price = min(prices)  # 最安値を代表値とする
        title = b.find(["h1","h2","h3","h4","strong","a"])
        name = (title.get_text(strip=True) if title else text[:60]).strip()
        genre = normalize_genre(text)
        out.append((name[:60], price, genre))
    return out

def build_df_from_urls(self_name: str, self_url: str, comp_urls: list, genre_limits: dict) -> pd.DataFrame:
    rows = []
    # 自店
    if str(self_url).strip():
        html = fetch_html(self_url)
        for (name, price, genre) in parse_coupons_from_html(html):
            rows.append({
                "salon_name": self_name or "自店",
                "genre": genre, "coupon_name": name, "price": price,
                "lower_limit": genre_limits.get(genre) if genre_limits.get(genre) else np.nan,
                "url": self_url, "is_self": 1
            })
    # 競合
    for url in comp_urls:
        if not str(url).strip(): continue
        html = fetch_html(url)
        coupons = parse_coupons_from_html(html)
        salon = "競合"
        try:
            t = BeautifulSoup(html, "html.parser").title
            if t and t.text: salon = t.text.strip()[:40]
        except: pass
        for (name, price, genre) in coupons:
            rows.append({
                "salon_name": salon,
                "genre": genre, "coupon_name": name, "price": price,
                "lower_limit": genre_limits.get(genre) if genre_limits.get(genre) else np.nan,
                "url": url, "is_self": 0
            })
    df = pd.DataFrame(rows, columns=["salon_name","genre","coupon_name","price","lower_limit","url","is_self"])
    if not df.empty:
        df = (df.sort_values("price").groupby(["salon_name","genre"], as_index=False).first())
    return df

# ====== 下限設定 ======
if "limits" not in st.session_state:
    st.session_state["limits"] = {g: None for g in GENRE_MASTER}

def apply_limits_to_df(df: pd.DataFrame):
    for g, v in st.session_state["limits"].items():
        if v is None: continue
        mask = (df["genre"]==g) & (df["lower_limit"].isna())
        df.loc[mask, "lower_limit"] = v
    return df

# ====== 判定・提案 ======
def suggested_price(lower, comp):
    raw = (float(lower) + float(comp)) / 2.0
    return int(round(raw/100.0) * 100)

def detect_alerts(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return pd.DataFrame()
    x = df.copy()
    x = x[(x["is_self"]!=1) & (~x["lower_limit"].isna())]
    x = x[x["price"] < x["lower_limit"]]
    if x.empty: return pd.DataFrame()
    x["diff"] = x["lower_limit"] - x["price"]
    x["diff_rate"] = x["diff"] / x["lower_limit"]
    x["prio"] = x["genre"].map(PRIORITY_ORDER).fillna(4)
    x["score"] = (x["diff_rate"]*60) + ((4 - x["prio"])/4*40)
    x["suggested_price"] = x.apply(lambda r: suggested_price(r["lower_limit"], r["price"]), axis=1)
    x = x.sort_values(by=["score","diff"], ascending=[False, False]).reset_index(drop=True)
    return x

# ====== 履歴 ======
def load_history():
    if not os.path.exists(HISTORY_FILE):
        return pd.DataFrame(columns=HISTORY_COLS)
    try:
        df = pd.read_csv(HISTORY_FILE)
        for c in ["price","lower_limit","diff","suggested_price"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        return df
    except:
        return pd.DataFrame(columns=HISTORY_COLS)

def save_history(rows: pd.DataFrame):
    hist = load_history()
    if rows.empty: return hist
    rows = rows.drop_duplicates(subset=["date","salon_name","coupon_name","genre","price"])
    hist = pd.concat([hist, rows], ignore_index=True)
    try:
        hist["date_dt"] = pd.to_datetime(hist["date"])
        cutoff = datetime.now(JST).date() - timedelta(days=90)
        hist = hist[hist["date_dt"].dt.date >= cutoff].drop(columns=["date_dt"])
    except: pass
    hist.to_csv(HISTORY_FILE, index=False)
    return hist

# ====== ヘッダー ======
st.markdown("## 🩵 SBレスキュー（単一版 / URL読み込み）")
st.caption("価格チェックを自動化。競合が設定下限を下回ったときだけ提案を表示します。")

# ====== サイドバー：設定 ======
with st.sidebar:
    st.markdown("### ⚙️ 設定（ジャンル下限）")
    st.caption("未入力ジャンルは判定対象外。500円単位推奨。")
    for g in GENRE_MASTER:
        v = st.number_input(f"{g} 下限（円）", min_value=0, max_value=100000, step=500,
                            value=st.session_state["limits"][g] if st.session_state["limits"][g] else 0)
        st.session_state["limits"][g] = None if v==0 else v
    st.markdown("---")
    st.caption("※ 自店単体のアラートは出しません。競合が下限未満のときのみ通知します。")

# ====== タブ ======
tab_scan, tab_suggest, tab_hist, tab_summary, tab_guide = st.tabs(
    ["🔍 スキャン（URL）","💡 提案","🗂 履歴","📈 サマリー","📘 使い方"]
)

# ====== スキャン（URL） ======
with tab_scan:
    st.markdown("#### 今日のスキャン（URLから自動取得）")

    with st.expander("① 自店の情報", expanded=True):
        c1, c2 = st.columns([2,3])
        with c1:
            self_name = st.text_input("自店名", value=st.session_state.get("self_name",""))
            st.session_state["self_name"] = self_name
        with c2:
            self_url = st.text_input("自店ページURL（HPBのサロンTOPまたはクーポン一覧）", value=st.session_state.get("self_url",""))
            st.session_state["self_url"] = self_url

    with st.expander("② 競合のURL（最大20件）", expanded=True):
        if "comp_urls" not in st.session_state:
            st.session_state["comp_urls"] = [""]*5
        for i, cur in enumerate(st.session_state["comp_urls"]):
            st.session_state["comp_urls"][i] = st.text_input(f"競合URL {i+1}", value=cur, key=f"comp_{i}")
        if st.button("＋ 入力欄を5件追加"):
            st.session_state["comp_urls"].extend([""]*5)
        st.caption("※ 近隣エリアのHPBサロンTOP/クーポン一覧URLを推奨。空欄は無視します。")

    st.markdown("---")
    if st.button("🚀 スキャン開始（URLから取得）"):
        ris_says("ページを読み込み中です。少しお待ちください。")
        limits = {g: st.session_state["limits"].get(g) for g in GENRE_MASTER}
        df = build_df_from_urls(self_name, self_url, st.session_state["comp_urls"], limits)

        if df.empty:
            ris_says("有効なクーポン情報を読み取れませんでした。URLの公開状態や打ち間違いをご確認ください。", "err")
            st.stop()

        df = apply_limits_to_df(df)
        st.dataframe(df, use_container_width=True)

        alerts = detect_alerts(df)
        st.session_state["last_alerts"] = alerts

        if alerts.empty:
            ris_says("下限を下回る競合は見つかりませんでした。今日は安定しています。", "ok")
        else:
            top3 = alerts.head(3)
            ris_says("競合の一部で下限未満が見つかりました。早めの調整をおすすめします。", "warn")
            for _, r in top3.iterrows():
                ris_says(
                    f"【{r['genre']}｜{r['salon_name']}】 競合価格：{int(r['price']):,}円 / 下限：{int(r['lower_limit']):,}円（差額 -{int(r['diff']):,}円）。"
                    f"本日中に **{int(r['lower_limit']):,}→{int(r['suggested_price']):,}円** への調整をおすすめします。",
                    "warn"
                )
            if len(alerts) > 3:
                ris_says(f"他に {len(alerts)-3} 件あります。『提案』タブをご確認ください。", "warn")

            # 履歴保存
            today = datetime.now(JST).strftime("%Y-%m-%d")
            save_rows = alerts.copy()
            save_rows["date"] = today
            save_rows["state"] = "未対応"
            save_rows = save_rows[[
                "date","salon_name","genre","coupon_name","price",
                "lower_limit","diff","suggested_price","url","state"
            ]]
            _ = save_history(save_rows)
            st.success("検出結果を履歴に保存しました。")

# ====== 提案 ======
with tab_suggest:
    st.markdown("#### 今日のサジェスト（上位3件）")
    alerts = st.session_state.get("last_alerts", pd.DataFrame())
    if alerts is None or alerts.empty:
        st.info("現在、提案はありません。スキャンタブから解析してください。")
    else:
        top3 = alerts.head(3)
        for i, r in top3.iterrows():
            with st.container(border=True):
                st.markdown(
                    f"**🟥【{r['genre']}】 {r['salon_name']}** 　"
                    f"<span class='badge'>優先度:{int(r['score'])}</span>",
                    unsafe_allow_html=True
                )
                st.write(
                    f"💴 競合価格：{int(r['price']):,}円　｜　下限：{int(r['lower_limit']):,}円　｜　"
                    f"差額：-{int(r['diff']):,}円（{r['diff_rate']*100:.1f}%）"
                )
                st.write("📈 **影響**：このままでは比較段階で他店への流出が予測されます。")
                st.write(
                    f"💡 **ご提案**：本日中に、**{int(r['lower_limit']):,}円 → {int(r['suggested_price']):,}円** "
                    "への再設定をご検討ください。"
                )
                if str(r.get("url","")).strip():
                    st.write(f"🔗 参考URL：{r['url']}")
                c1, c2, _ = st.columns([1,1,5])
                with c1:
                    if st.button("対応済みにする", key=f"done_{i}"):
                        hist = load_history()
                        today = datetime.now(JST).strftime("%Y-%m-%d")
                        m = (hist["date"]==today)&(hist["salon_name"]==r["salon_name"])&(hist["coupon_name"]==r["coupon_name"])
                        hist.loc[m,"state"]="対応済み"; hist.to_csv(HISTORY_FILE, index=False)
                        st.success("対応済みにしました。")
                with c2:
                    if st.button("明日へ回す", key=f"snooze_{i}"):
                        hist = load_history()
                        today = datetime.now(JST).strftime("%Y-%m-%d")
                        m = (hist["date"]==today)&(hist["salon_name"]==r["salon_name"])&(hist["coupon_name"]==r["coupon_name"])
                        hist.loc[m,"state"]="スヌーズ"; hist.to_csv(HISTORY_FILE, index=False)
                        st.info("当日は非表示にします。翌日のスキャン時に再表示します。")

# ====== 履歴 ======
with tab_hist:
    st.markdown("#### 過去の対応履歴（90日以内）")
    hist = load_history()
    if hist.empty:
        st.info("履歴はまだありません。スキャンを実行すると保存されます。")
    else:
        c1,c2,c3 = st.columns(3)
        with c1: gsel = st.multiselect("ジャンル", GENRE_MASTER, default=GENRE_MASTER)
        with c2: ssel = st.multiselect("状態", ["未対応","対応済み","スヌーズ"], default=["未対応","対応済み","スヌーズ"])
        with c3: order = st.selectbox("並び順", ["新しい順","古い順","差額が大きい順"])
        dfh = hist.copy()
        dfh = dfh[dfh["genre"].isin(gsel) & dfh["state"].isin(ssel)]
        if order=="新しい順": dfh = dfh.sort_values("date", ascending=False)
        elif order=="古い順": dfh = dfh.sort_values("date", ascending=True)
        else: dfh = dfh.sort_values("diff", ascending=False)
        st.dataframe(dfh, use_container_width=True, hide_index=True)

# ====== サマリー ======
with tab_summary:
    st.markdown("#### 30日サマリー")
    hist = load_history()
    if hist.empty:
        st.info("サマリー表示には履歴が必要です。まずはスキャンを実行してください。")
    else:
        try:
            hist["date_dt"] = pd.to_datetime(hist["date"])
            last30 = hist[hist["date_dt"] >= (datetime.now(JST)-timedelta(days=30))]
            c1,c2,c3 = st.columns(3)
            with c1:
                st.markdown(
                    f"<div class='kpi'><h3>総アラート</h3>"
                    f"<div style='font-size:1.6rem;'>{len(last30)}</div>"
                    f"<div class='small'>過去30日</div></div>",
                    unsafe_allow_html=True
                )
            with c2:
                rate = ((last30["state"]=="対応済み").sum()/len(last30)*100) if len(last30)>0 else 0
                st.markdown(
                    f"<div class='kpi'><h3>対応済み率</h3>"
                    f"<div style='font-size:1.6rem;'>{rate:.0f}%</div>"
                    f"<div class='small'>過去30日</div></div>",
                    unsafe_allow_html=True
                )
            with c3:
                avg = int(last30["diff"].mean() if len(last30)>0 else 0)
                st.markdown(
                    f"<div class='kpi'><h3>平均差額</h3>"
                    f"<div style='font-size:1.6rem;'>{avg:,}円</div>"
                    f"<div class='small'>過去30日</div></div>",
                    unsafe_allow_html=True
                )
            st.markdown("##### ジャンル別アラート件数（過去30日）")
            agg = last30.groupby("genre")["coupon_name"].count().reset_index().rename(columns={"coupon_name":"count"})
            st.bar_chart(agg, x="genre", y="count", height=240)
        except Exception as e:
            st.warning(f"サマリー生成で一部エラー：{e}")

# ====== 使い方 ======
with tab_guide:
    st.markdown("""
### 📘 SBレスキュー 使い方ガイド

**SBレスキューは、あなたのお店の価格を自動チェックして、近くの競合が「下限価格より安いクーポン」を出したときだけ提案を表示します。**

---

#### ✅ 最初に一度だけ（設定）
1. 左の **⚙️設定** でジャンルごとの **下限価格** を入力します（未入力ジャンルは判定しません）。
2. **自店名** と **自店URL**（HPBのサロンTOPまたはクーポン一覧）を登録します。
3. **競合URL** を登録します（最大20件。近隣エリア推奨）。

---

#### 🔍 毎日の操作（3ステップ）
1. **スキャン開始** を押す（1〜2分で読み込み）。
2. **結果を見る**  
   - 緑：下限割れなし（安定）  
   - オレンジ：下限割れあり（件数と概要を表示）
3. **提案タブ** で上位3件の調整案を確認し、対応状況を記録します。  
   - 「対応済み」…今日の表示から除外  
   - 「明日へ回す」…本日は非表示、翌日に再表示

---

#### 🧠 ルール
- **自店単体のアラートは出しません。** 競合があなたの下限を**下回る**ときにのみ通知します。
- **優先度**：フェイシャル ＞ 痩身 ＞ ブライダル ＞ 脱毛 ＞ その他  
- **提案価格**：下限と競合の中間（100円単位丸め）

---

困ったときは右上「Share」からURLを送ってください。  
**今日の売上に直結する“価格の守り”は、SBレスキューにおまかせください。**
""")
