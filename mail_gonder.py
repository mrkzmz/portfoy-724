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
    with ThreadPoolExecutor(max_workers=12) as ex:
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
