# app.py
# SBレスキュー（単一ファイル完成版）
# 機能：CSVスキャン / データ検証 / 下限値UI / サジェスト（上位3件）/ 履歴保存(90日) / サマリー簡易可視化 / 使い方ガイド
# 依存：streamlit, pandas, numpy

import streamlit as st
import pandas as pd
import numpy as np
import re
import io
import os
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))

# ----------------------------
# ページ設定
# ----------------------------
st.set_page_config(page_title="SBレスキュー", page_icon="💬", layout="wide")

# ----------------------------
# スタイル（リスくん＋UI）
# ----------------------------
st.markdown("""
<style>
:root {
  --blue:#4A90E2; --light:#F9FBFD; --border:#D6E2F3; --text:#333; --shadow: rgba(0,0,0,.08);
  --ok:#E6FFF1; --warn:#FFF5E5; --err:#FFECEC;
}
body { background-color: var(--light); }
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
.ris-row{ display:flex; align-items:flex-end; gap:12px; margin:.25rem 0 1rem 0;}
.ris-icon{
  width:44px;height:44px;border-radius:50%;
  background: radial-gradient(circle, var(--blue) 0%, #B7D5FA 80%);
  display:flex;align-items:center;justify-content:center;color:white;font-size:20px;
  box-shadow:0 0 10px rgba(74,144,226,.5); animation:breath 3s ease-in-out infinite;
}
@keyframes breath{0%{box-shadow:0 0 6px rgba(74,144,226,.5);}50%{box-shadow:0 0 14px rgba(74,144,226,.9);}100%{box-shadow:0 0 6px rgba(74,144,226,.5);}}
.bubble{
  background:#fff;border:1px solid var(--border);border-radius:18px;padding:10px 14px;color:var(--text);
  box-shadow:0 3px 10px var(--shadow);max-width:420px;animation:fadeUp .5s ease;
}
.bubble.warn{ background:var(--warn); } .bubble.ok{ background:var(--ok);} .bubble.err{ background:var(--err);}
@keyframes fadeUp{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
.h-card{
  background:#fff;border:1px solid var(--border);border-radius:14px;padding:12px 14px;margin-bottom:10px;
  box-shadow:0 3px 10px var(--shadow);
}
.kpi{
  background:#fff;border:1px solid var(--border);border-radius:12px;padding:14px 16px;text-align:center;
  box-shadow:0 3px 10px var(--shadow);
}
.kpi h3{margin:.2rem 0 .4rem 0}
.small{opacity:.7;font-size:.9rem}
.badge{display:inline-block;padding:.1rem .5rem;border-radius:999px;border:1px solid var(--border);background:#fff}
hr{border:none;border-top:1px solid var(--border); margin:12px 0}
</style>
""", unsafe_allow_html=True)

def ris_says(msg:str, tone:str="default"):
    cls = "bubble"
    if tone=="ok": cls += " ok"
    elif tone=="warn": cls += " warn"
    elif tone=="err": cls += " err"
    st.markdown(f"""
    <div class="ris-row">
      <div class="ris-icon">💬</div>
      <div class="{cls}">{msg}</div>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------
# ユーティリティ：正規化・検証
# ----------------------------
REQUIRED_COLS = ["salon_name","genre","coupon_name","price","lower_limit"]

COL_ALIASES = {
    "サロン名":"salon_name","店舗名":"salon_name","store":"salon_name",
    "ジャンル":"genre","category":"genre",
    "クーポン名":"coupon_name","coupon":"coupon_name","メニュー名":"coupon_name","menu":"coupon_name",
    "価格":"price","料金":"price","price(yen)":"price",
    "下限":"lower_limit","下限価格":"lower_limit","limit":"lower_limit",
    "url":"url","coupon_url":"url","リンク":"url",
    "自店フラグ":"is_self","is_self":"is_self"
}

GENRE_MASTER = ["フェイシャル","痩身","脱毛","ブライダル","バストケア","シェービング","ヨガ・ピラティス・加圧","その他"]

def to_half_width(s:str) -> str:
    try:
        import unicodedata
        return unicodedata.normalize('NFKC', str(s))
    except:
        return str(s)

def to_number(x):
    if pd.isna(x): return np.nan
    s = to_half_width(str(x))
    s = re.sub(r"[^\d\.-]", "", s)  # 数字・小数点・マイナス以外除去（¥,カンマ,全角など）
    try:
        return float(s)
    except:
        return np.nan

def normalize_columns(df:pd.DataFrame) -> pd.DataFrame:
    cols = {c: COL_ALIASES.get(c, c) for c in df.columns}
    df = df.rename(columns=cols)
    return df

def validate_and_clean(df:pd.DataFrame):
    # 列名正規化
    df = normalize_columns(df.copy())
    # 必須列チェック
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"必須列が不足しています：{missing}\n必要列は {REQUIRED_COLS} です。列名が違う場合は表頭の表記を合わせてください。")
    # 型整形
    df["salon_name"] = df["salon_name"].astype(str).str.strip()
    df["genre"] = df["genre"].astype(str).str.strip()
    df["coupon_name"] = df["coupon_name"].astype(str).str.strip()
    df["price"] = df["price"].apply(to_number)
    df["lower_limit"] = df["lower_limit"].apply(to_number)
    if "is_self" in df.columns:
        df["is_self"] = df["is_self"].fillna(0).apply(lambda v: 1 if str(v).strip() in ["1","True","true","自店","yes","YES"] else 0)
    else:
        df["is_self"] = 0
    # 欠損除外
    df = df.dropna(subset=["price","lower_limit","genre","salon_name","coupon_name"]).reset_index(drop=True)
    # ジャンル表記ゆれ（簡易正規化）
    df["genre"] = df["genre"].replace({
        "ﾌｪｲｼｬﾙ":"フェイシャル","フェーシャル":"フェイシャル",
        "痩せ身":"痩身","ブライドル":"ブライダル","よが":"ヨガ・ピラティス・加圧","ピラティス":"ヨガ・ピラティス・加圧"
    })
    df.loc[~df["genre"].isin(GENRE_MASTER), "genre"] = "その他"
    # URL列（任意）
    if "url" not in df.columns:
        df["url"] = ""
    return df

# ----------------------------
# 下限設定（UI・保存）
# ----------------------------
if "limits" not in st.session_state:
    st.session_state["limits"] = {g: None for g in GENRE_MASTER}

def apply_limits(df:pd.DataFrame):
    # lower_limit が欠損または0の行に、UI設定のジャンル下限を適用
    for g, v in st.session_state["limits"].items():
        if v is not None:
            mask = (df["genre"]==g) & ((df["lower_limit"].isna()) | (df["lower_limit"]<=0))
            df.loc[mask, "lower_limit"] = v
    return df

# ----------------------------
# アラート判定・提案生成
# ----------------------------
def suggest_price(lower, comp):
    # 仕様：提案価格 = 下限 − ((下限−競合)×0.5) = (lower + comp)/2
    # 丸め（100円単位）
    raw = (lower + comp) / 2.0
    return int(round(raw/100.0)*100)

def detect_alerts(df:pd.DataFrame):
    # 自店は除外。競合が下限未満のみ。
    q = df[(df["is_self"]!=1) & (df["price"] < df["lower_limit"])]
    if q.empty:
        return pd.DataFrame()
    # 差額等計算
    q = q.copy()
    q["diff"] = q["lower_limit"] - q["price"]
    q["diff_rate"] = q["diff"] / q["lower_limit"]
    # 優先度：フェイシャル＞痩身＞ブライダル＞脱毛＞その他
    priority = {"フェイシャル":0,"痩身":1,"ブライダル":2,"脱毛":3,"その他":4,"バストケア":4,"シェービング":4,"ヨガ・ピラティス・加圧":4}
    q["prio"] = q["genre"].map(priority).fillna(4)
    # スコア = 価格差重視（60） + 簡易ジャンル優先（40）
    q["score"] = (q["diff_rate"]*60) + ((4 - q["prio"])/4*40)
    # 提案価格
    q["suggested_price"] = q.apply(lambda r: suggest_price(r["lower_limit"], r["price"]), axis=1)
    # 並び替え（スコア降順、差額降順）
    q = q.sort_values(by=["score","diff"], ascending=[False, False]).reset_index(drop=True)
    return q

# ----------------------------
# 履歴保存・読み込み（重複排除/90日保持）
# ----------------------------
HISTORY_FILE = "alert_history.csv"
HISTORY_COLS = ["date","salon_name","genre","coupon_name","price","lower_limit","diff","suggested_price","url","state"]

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return pd.DataFrame(columns=HISTORY_COLS)
    try:
        df = pd.read_csv(HISTORY_FILE)
        # 型補正
        for c in ["price","lower_limit","diff","suggested_price"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        return df
    except:
        return pd.DataFrame(columns=HISTORY_COLS)

def save_history(new_rows:pd.DataFrame):
    hist = load_history()
    if new_rows.empty:
        return hist
    # キーで重複排除（date, salon_name, coupon_name, genre, price）
    key_cols = ["date","salon_name","coupon_name","genre","price"]
    new_rows = new_rows.drop_duplicates(subset=key_cols)
    hist = pd.concat([hist, new_rows], ignore_index=True)
    # 90日より古いものをアーカイブ除去
    try:
        hist["date_dt"] = pd.to_datetime(hist["date"])
        cutoff = datetime.now(JST).date() - timedelta(days=90)
        hist = hist[hist["date_dt"].dt.date >= cutoff]
        hist = hist.drop(columns=["date_dt"])
    except:
        pass
    hist.to_csv(HISTORY_FILE, index=False)
    return hist

# ----------------------------
# ヘッダー
# ----------------------------
left, mid, right = st.columns([1,2,1])
with mid:
    st.markdown("## 🩵 SBレスキュー（単一版）")
    st.caption("価格チェックを自動化し、下限割れ時のみ提案を表示します。")

# ----------------------------
# サイドバー：設定
# ----------------------------
with st.sidebar:
    st.markdown("### ⚙️ 設定")
    st.markdown("下限価格（500円単位）を必要なジャンルにだけ設定してください。CSVのlower_limitが空なら、ここでの値を適用します。")
    for g in GENRE_MASTER:
        v = st.number_input(f"{g}の下限（円）", min_value=0, max_value=100000, step=500,
                            value=st.session_state["limits"][g] if st.session_state["limits"][g] is not None else 0)
        st.session_state["limits"][g] = None if v==0 else v

    st.markdown("---")
    st.markdown("**自店データを除外する列**：`is_self` が 1 / True の行はアラート対象外になります。")
    st.markdown("**任意列**：`url`（クーポンURL）があれば履歴に保存します。")

# ----------------------------
# メイン：タブ
# ----------------------------
tab_scan, tab_suggest, tab_hist, tab_summary, tab_guide = st.tabs(["🔍 スキャン", "💡 提案", "🗂 履歴", "📈 サマリー", "📘 使い方"])

# セッション保持
if "last_alerts" not in st.session_state:
    st.session_state["last_alerts"] = pd.DataFrame()

with tab_scan:
    st.markdown("#### 今日のスキャン")
    up = st.file_uploader("📂 クーポンデータ（CSV）をアップロード", type=["csv"])
    if up:
        try:
            df_raw = pd.read_csv(up)
        except UnicodeDecodeError:
            up.seek(0)
            df_raw = pd.read_csv(up, encoding="cp932")
        try:
            df = validate_and_clean(df_raw)
        except Exception as e:
            ris_says(f"データの読み込みに失敗しました：{e}", "err")
            st.stop()

        # UI下限の適用
        df = apply_limits(df)

        # 表示（軽く）
        st.markdown("**読み込み結果（整形後）**")
        st.dataframe(df.head(50), use_container_width=True)

        # スキャン実行ボタン
        if st.button("🚀 スキャン開始"):
            ris_says("スキャンを始めます。少しお待ちくださいね。")
            alerts = detect_alerts(df)
            st.session_state["last_alerts"] = alerts

            if alerts.empty:
                ris_says("価格の大きな変動はありませんでした。安定しています。", "ok")
            else:
                # 上位3件のみ掲示（吹き出し過多防止）
                top3 = alerts.head(3).copy()
                ris_says("一部のジャンルで下限を下回るクーポンが見つかりました。", "warn")
                for _, r in top3.iterrows():
                    genre = r["genre"]; salon = r["salon_name"]; price=int(r["price"]); low=int(r["lower_limit"])
                    diff=int(r["diff"]); sug=int(r["suggested_price"])
                    msg = f"【{genre}｜{salon}】 競合価格：{price:,}円 / 下限：{low:,}円（差額 -{diff:,}円）。本日中に **{(low):,}→{sug:,}円** への調整をおすすめします。"
                    ris_says(msg, "warn")
                if len(alerts)>3:
                    ris_says(f"他に {len(alerts)-3} 件あります。提案タブをご確認ください。", "warn")

                # 履歴保存
                today = datetime.now(JST).strftime("%Y-%m-%d")
                save_rows = alerts.copy()
                save_rows["date"] = today
                save_rows["state"] = "未対応"
                save_rows = save_rows.rename(columns={"diff":"diff","suggested_price":"suggested_price"})
                save_rows = save_rows[["date","salon_name","genre","coupon_name","price","lower_limit","diff","suggested_price","url","state"]]
                _ = save_history(save_rows)
                st.success("検出結果を履歴に保存しました。")

    else:
        st.info("CSVをアップロードしてスキャンを実行してください。必須列：salon_name, genre, coupon_name, price, lower_limit（任意：url, is_self）")

with tab_suggest:
    st.markdown("#### 今日のサジェスト（上位3件）")
    alerts = st.session_state.get("last_alerts", pd.DataFrame())
    if alerts is None or alerts.empty:
        st.info("現在、提案はありません。スキャンタブから解析してください。")
    else:
        top3 = alerts.head(3).copy()
        for _, r in top3.iterrows():
            with st.container(border=True):
                st.markdown(f"**🟥【{r['genre']}】 {r['salon_name']}** 　<span class='badge'>優先度:{int(r['score'])}</span>", unsafe_allow_html=True)
                st.write(f"💴 競合価格：{int(r['price']):,}円　｜　下限：{int(r['lower_limit']):,}円　｜　差額：-{int(r['diff']):,}円（{r['diff_rate']*100:.1f}%）")
                st.write("📈 **現状分析**：このままでは比較段階で他店への流出が予測されます。")
                st.write(f"💡 **ご提案**：本日中に、**{int(r['lower_limit']):,}円 → {int(r['suggested_price']):,}円** への再設定をおすすめいたします。")
                if str(r.get("url","")).strip():
                    st.write(f"🔗 参考URL：{r['url']}")
                cols = st.columns([1,1,4])
                with cols[0]:
                    if st.button("対応済みにする", key=f"done_{_}"):
                        hist = load_history()
                        today = datetime.now(JST).strftime("%Y-%m-%d")
                        mask = (hist["date"]==today) & (hist["salon_name"]==r["salon_name"]) & (hist["coupon_name"]==r["coupon_name"])
                        hist.loc[mask,"state"]="対応済み"
                        hist.to_csv(HISTORY_FILE, index=False)
                        st.success("対応済みにしました。")
                with cols[1]:
                    if st.button("明日へ回す", key=f"snooze_{_}"):
                        hist = load_history()
                        today = datetime.now(JST).strftime("%Y-%m-%d")
                        mask = (hist["date"]==today) & (hist["salon_name"]==r["salon_name"]) & (hist["coupon_name"]==r["coupon_name"])
                        hist.loc[mask,"state"]="スヌーズ"
                        hist.to_csv(HISTORY_FILE, index=False)
                        st.info("当日は非表示にします。翌日のスキャン時に再表示します。")

with tab_hist:
    st.markdown("#### 過去の対応履歴（90日以内）")
    hist = load_history()
    if hist.empty:
        st.info("履歴はまだありません。スキャンを実行すると保存されます。")
    else:
        # フィルタ
        c1, c2, c3 = st.columns(3)
        with c1:
            gsel = st.multiselect("ジャンル", GENRE_MASTER, default=GENRE_MASTER)
        with c2:
            ssel = st.multiselect("状態", ["未対応","対応済み","スヌーズ"], default=["未対応","対応済み","スヌーズ"])
        with c3:
            sort_key = st.selectbox("並び順", ["新しい順","古い順","差額の大きい順"], index=0)

        dfh = hist.copy()
        dfh = dfh[dfh["genre"].isin(gsel) & dfh["state"].isin(ssel)]
        if sort_key=="新しい順":
            dfh = dfh.sort_values(by="date", ascending=False)
        elif sort_key=="古い順":
            dfh = dfh.sort_values(by="date", ascending=True)
        else:
            dfh = dfh.sort_values(by="diff", ascending=False)

        st.dataframe(dfh, use_container_width=True, hide_index=True)

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
                st.markdown("<div class='kpi'><h3>総アラート件数</h3><div style='font-size:1.6rem;'>"+str(len(last30))+"</div><div class='small'>過去30日</div></div>", unsafe_allow_html=True)
            with c2:
                done = (last30["state"]=="対応済み").sum()
                rate = (done/len(last30)*100) if len(last30)>0 else 0
                st.markdown(f"<div class='kpi'><h3>対応済み率</h3><div style='font-size:1.6rem;'>{rate:.0f}%</div><div class='small'>過去30日</div></div>", unsafe_allow_html=True)
            with c3:
                if "date_dt" in last30 and "state" in last30:
                    # 簡易：当日対応のみを即日とみなす
                    same_day = 0
                    # 本格的な対応日時管理は将来拡張。ここはダミーで0。
                st.markdown(f"<div class='kpi'><h3>平均差額</h3><div style='font-size:1.6rem;'>{int(last30['diff'].mean() if len(last30)>0 else 0):,}円</div><div class='small'>過去30日</div></div>", unsafe_allow_html=True)
            st.markdown("##### ジャンル別アラート件数（過去30日）")
            agg = last30.groupby("genre")["coupon_name"].count().reset_index().rename(columns={"coupon_name":"count"})
            st.bar_chart(agg, x="genre", y="count", height=240)
        except Exception as e:
            st.warning(f"サマリー生成で一部エラー：{e}")

with tab_guide:
    st.markdown("### 📘 ご利用ガイド（SBレスキュー）")
    st.markdown("""
**目的**：お店のクーポン価格を自動でチェックし、下限を下回る競合を見つけたときだけ提案を表示します。  
**やること**：  
1) 左の「⚙️設定」でジャンル下限を登録（任意）  
2) 🔍スキャンにCSVをアップロード → 「スキャン開始」  
3) 💡提案タブで「対応済み」or「明日へ回す」を選ぶ  
4) 🗂履歴・📈サマリーで振り返り

**CSVの必須列**：`salon_name, genre, coupon_name, price, lower_limit`（任意：`url, is_self`）  
**注意**：`is_self` が 1 の行はアラート対象外（自店は通知しない仕様）
    """)

    st.markdown("—")
    ris_says("不明点があれば、CSVの列名を見直してから再度お試しください。", "ok")
