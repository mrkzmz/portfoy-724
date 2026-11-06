import warnings
warnings.filterwarnings("ignore")
# -*- coding: utf-8 -*-
import os
import sys
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor

os.environ["PORTFOY_CLI_IMPORT"] = "1"
import portfoy as pf

def should_dispatch_now() -> tuple:
    is_scheduled = (os.environ.get("GITHUB_EVENT_NAME") == "schedule") or ("--scheduled" in sys.argv)
    if not is_scheduled:
        return True, "Manuel tetikleme -> Anında gönderiliyor."
    tr_now = datetime.now(ZoneInfo("Europe/Istanbul"))
    ny_now = datetime.now(ZoneInfo("America/New_York"))
    if tr_now.hour in (22, 23):
        if ny_now.hour == 15:
            return True, f"✅ ABD Kapanış Onay Saati Eşleşti ({ny_now.strftime('%H:%M %Z')} = {tr_now.strftime('%H:%M TSİ')}) -> Gönderiliyor."
        target_tsi = "23:35 TSİ" if ny_now.tzname() == "EST" else "22:35 TSİ"
        return False, f"⏳ Otomatik Yaz/Kış Saati Koruması: Şu an NY saati {ny_now.strftime('%H:%M %Z')}. ABD kapanış bülteni 15:35 NY ({target_tsi}) saatinde gönderilecek."
    return True, f"✅ Sabit Türkiye Seansı ({tr_now.strftime('%H:%M TSİ')}) -> Gönderiliyor."

def run_cloud_newsletter():
    ok_time, time_msg = should_dispatch_now()
    print(time_msg)
    if not ok_time:
        return
    df_db, pool_usd = pf.load_portfolio_db()
    yf_tickers = df_db["yf_ticker"].tolist()
    series_map = {}
    def _w(sym):
        return sym, pf.fetch_direct_series(sym, "2y")
    with ThreadPoolExecutor(max_workers=28) as ex:
        for sym, ser in ex.map(_w, yf_tickers):
            if ser is not None and len(ser) >= 15:
                series_map[sym] = ser
    results = []
    for _, r in df_db.iterrows():
        tck_raw = r["ticker"]
        if tck_raw.startswith("INDEX"):
            continue
        yt = r["yf_ticker"]
        metrics = {}
        if yt in series_map:
            try:
                metrics = pf.analyze_price_history(pd.DataFrame({"Close": series_map[yt]}))
            except Exception:
                metrics = {}
        if not metrics or metrics.get("fiyat", 0.0) <= 0:
            metrics = pf.get_fallback_metrics(tck_raw)
        if tck_raw.startswith("CURRENCY:"):
            temiz_ad = tck_raw.replace("CURRENCY:", "").replace("USD", "")
        elif tck_raw.startswith("IST:"):
            temiz_ad = tck_raw.replace("IST:", "") + " (BIST)"
        else:
            temiz_ad = tck_raw
        row_d = {
            "satir_no": int(r["satir_no"]), "ticker": tck_raw, "yf_ticker": yt, "sembol": temiz_ad,
            "sektor": r["sektor"], "kategori": r["kategori"], "eldeki_adet": float(r["eldeki_adet"]),
            "ort_maliyet": float(r["ort_maliyet"]), "son_alim": float(r["son_alim"]),
            "korunan_ana_para": float(r["korunan_ana_para"]), "hedef_tutar": float(r["hedef_tutar"]),
            "fiyat": metrics.get("fiyat", 0.0), "degisim_pct": metrics.get("degisim_pct", 0.0),
            "canli_rsi_1g": metrics.get("canli_rsi_1g", 0.0), "dunku_rsi_1g": metrics.get("dunku_rsi_1g", 0.0),
            "canli_rsi_1h": metrics.get("canli_rsi_1h", 0.0), "canli_rsi_1a": metrics.get("canli_rsi_1a", 0.0),
            "sma200": metrics.get("sma200", 0.0), "sma200_fark_pct": metrics.get("sma200_fark_pct", 0.0),
            "high52": metrics.get("high52", 0.0), "low52": metrics.get("low52", 0.0),
            "dd52_pct": metrics.get("dd52_pct", 0.0), "marj52_pct": metrics.get("marj52_pct", 0.0),
            "tv_sinyal": metrics.get("tv_sinyal", "YOK"), "tv_etiket": metrics.get("tv_etiket", ""),
            "tv_tepe": metrics.get("tv_tepe", 0.0), "tv_tepeden_dusus_pct": metrics.get("tv_tepeden_dusus_pct", 0.0),
            "tv_kademe_no": metrics.get("tv_kademe_no", 1), "tv_son_ekle_fiyat": metrics.get("tv_son_ekle_fiyat", 0.0),
            "tv_sonraki_esik": metrics.get("tv_sonraki_esik", 0.0),
        }
        esik, deger, fren, kad_u, lot_v, karar = pf.evaluate_portfolio_decision(row_d)
        row_d["guncel_deger"] = deger
        row_d["kademe_u"] = kad_u
        row_d["alinacak_v"] = lot_v
        row_d["karar"] = karar
        results.append(row_d)
    df_live = pd.DataFrame(results)
    em, pw = pf.detect_existing_smtp_creds()
    ok, msg = pf.send_bekaprsi_email(df_live, pool_usd, em, pw)
    print(msg)

if __name__ == "__main__":
    run_cloud_newsletter()


# === BEKAPRSI_TV_1H_SYNC_V1 ===
_WEEKLY_BAR_CACHE = {}

if "analyze_price_history" in globals() and "_orig_analyze_price_history_tv" not in globals():
    _orig_analyze_price_history_tv = analyze_price_history

    def analyze_price_history(s_close, *args, **kwargs):
        res = _orig_analyze_price_history_tv(s_close, *args, **kwargs)
        try:
            s_clean = s_close.dropna()
            s_w = s_clean.resample("W-FRI").last().dropna()
            if len(s_w) >= 2:
                prev_w = float(s_w.iloc[-2])
                curr_w = float(s_w.iloc[-1])
                chg_1h = round(((curr_w - prev_w) / prev_w) * 100.0, 2) if prev_w > 0 else 0.0
                tetik_1h = round(prev_w * 1.004, 2)
            else:
                prev_w = float(s_clean.iloc[-1]) if len(s_clean) > 0 else 0.0
                chg_1h = 0.0
                tetik_1h = round(prev_w * 1.004, 2)
            if isinstance(res, dict):
                res["chg_1h_pct"] = chg_1h
                res["prev_close_1h"] = prev_w
                res["tetik_1h"] = tetik_1h
                p_key = round(float(res.get("price", res.get("canli_fiyat", curr_w))), 2)
                _WEEKLY_BAR_CACHE[p_key] = (chg_1h, prev_w, tetik_1h)
        except Exception:
            pass
        return res

if "evaluate_portfolio_decision" in globals() and "_orig_evaluate_portfolio_decision_tv" not in globals():
    _orig_evaluate_portfolio_decision_tv = evaluate_portfolio_decision

    def evaluate_portfolio_decision(*args, **kwargs):
        dec = _orig_evaluate_portfolio_decision_tv(*args, **kwargs)
        try:
            # Girdi parametrelerinden metrikleri yakala
            metrics = {}
            for a in list(args) + list(kwargs.values()):
                if isinstance(a, dict):
                    metrics.update(a)
            if isinstance(dec, dict):
                metrics.update(dec)

            price_val = float(metrics.get("price") or metrics.get("canli_fiyat") or 0.0)
            rsi_1h_val = metrics.get("rsi_1h") if metrics.get("rsi_1h") is not None else metrics.get("canli_rsi_1h")
            dd52_val = metrics.get("dd52_pct") if metrics.get("dd52_pct") is not None else metrics.get("fark_52h")

            chg_1h = metrics.get("chg_1h_pct")
            tetik_1h = metrics.get("tetik_1h")
            if chg_1h is None and price_val > 0:
                cached = _WEEKLY_BAR_CACHE.get(round(price_val, 2))
                if cached:
                    chg_1h, _, tetik_1h = cached
            if chg_1h is None:
                chg_1h = 0.0
            if not tetik_1h and price_val > 0:
                tetik_1h = round(price_val * 1.004, 2)

            if isinstance(dec, dict):
                for k, v in list(dec.items()):
                    if isinstance(v, str):
                        # KURAL 1: 1H ANA KALE EKLE/AL sinyali için HAFTALIK mumun yeşil (>= +%0.40) olması şarttır
                        if "1H ANA KALE" in v and ("EKLE" in v or "🟢" in v) and float(chg_1h) < 0.40:
                            r1h_str = f"{float(rsi_1h_val):.1f}" if rsi_1h_val is not None else "<40"
                            dec[k] = f"🔻 🔵 1H ANA KALE DİPTE (1H={r1h_str} | 1H Mum: {float(chg_1h):+.1f}%) ➔ Haftalık Yeşil Onay: >={float(tetik_1h):.2f}$"
                            for ck in ("action_code", "kod", "status", "durum", "signal_type"):
                                if ck in dec and dec[ck] in ("AL", "EKLE", "YESIL", "BUY"):
                                    dec[ck] = "DIP_BEKLE"
                            for bk in ("is_buy", "yeşil_al", "al_sinyali"):
                                if bk in dec and isinstance(dec[bk], bool):
                                    dec[bk] = False

                        # KURAL 2: 1. Fren (-%21..-%35) bölgesinde 1H RSI < 40 olmadan 1G ÖNCÜ EKLE yanamaz
                        elif "1G ÖNCÜ" in v and ("EKLE" in v or "🟢" in v) and dd52_val is not None:
                            dd_f = float(dd52_val)
                            r1h_f = float(rsi_1h_val) if rsi_1h_val is not None else 50.0
                            if -35.0 < dd_f <= -21.0 and r1h_f >= 40.0:
                                dec[k] = f"⏳ 1. FREN AKTİF ({dd_f:.1f}%) ➔ 1H Haftalık Onay (1H RSI < 40, Şu an: {r1h_f:.1f}) Bekleniyor"
                                for ck in ("action_code", "kod", "status", "durum", "signal_type"):
                                    if ck in dec and dec[ck] in ("AL", "EKLE", "YESIL", "BUY"):
                                        dec[ck] = "DIP_BEKLE"
                                for bk in ("is_buy", "yeşil_al", "al_sinyali"):
                                    if bk in dec and isinstance(dec[bk], bool):
                                        dec[bk] = False
        except Exception:
            pass
        return dec
# === END_BEKAPRSI_TV_1H_SYNC_V1 ===
