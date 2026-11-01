# -*- coding: utf-8 -*-
"""
PORTFÖY — BEKAPRSI AL / SAT SİNYAL & 20 YILLIK HAFTALIK RSI SİSTEMİ (portfoy.py)
Sadeleştirilmiş Tam Odaklı Mimari:
1. Sol Menü: Hızlı Alış / Satış İşlem Kaydı & Nakit Havuzu Güncelleme
2. Sekme 1: 📊 AL / SAT SİNYALLERİ (3 Sütunlu BEKAPRSI EKLE / KAR AL Kartları)
3. Sekme 2: 💼 PORTFÖYÜM (24 Aktif Varlık) & 🎯 RADAR (55 Varlık) Tabloları (1G, 1H, 1A RSI & SMA 200)
4. Sekme 3: 🏛️ 20 YILLIK (2006-2026) HAFTALIK RSI < 40 & SMA 200 ANALİZ SİSTEMİ
"""

import os
import sys
import json
import ssl
import sqlite3
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd

try:
    import streamlit as st
except ImportError:
    st = None

try:
    import yfinance as yf
except ImportError:
    yf = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "portfoy_hafiza.db")
DEFAULT_POOL_USD = 9960.00
GIRISIM_SET = {"SOFI", "TMDX", "RKLB", "CRDO", "IOT"}
ANA_OMURGA_1G_SET = {"CAT", "GOOGL", "QQQM", "AMZN", "META"}
MEGA_TEKEL_1A_SET = {"QQQM", "SMH", "IST:ZPX30", "GOOGL", "MSFT", "AAPL", "META", "AMZN", "NVDA", "CAT"}

INITIAL_SEED = [(2, 'NASA', 'NASA', '6. Uzay ve İnovasyon', 'Elimdeki ETF - 2.500$ Hedef (Özel İzin)', 54.08, 25.7, 26.86, 1389.86, 2500.0), (3, 'CAT', 'CAT', '7. Makine, Sanayi ve Elektrik Altyapısı', 'Elimdeki Hisse - 5.000$ Ana Omurga Kale (1G/1H Sinyal)', 4.93, 771.26, 713.42, 3802.32, 5000.0), (4, 'EWS', 'EWS', "11. Ülke ve Küresel ETF'ler", 'Elimdeki ETF - Çıkış Adayı', 23.66, 31.76, 34.43, 751.44, 0.0), (5, 'SMH', 'SMH', '2. Yarı İletken (Çip)', 'Elimdeki ETF', 4.2, 543.26, 551.6, 2281.68, 3500.0), (6, 'AVGO', 'AVGO', '2. Yarı İletken (Çip)', 'Elimdeki Hisse - 3.500$ Trend Kalesi', 6.55, 354.86, 0.0, 2324.35, 3500.0), (7, 'ETN', 'ETN', '7. Makine, Sanayi ve Elektrik Altyapısı', 'Elimdeki Hisse', 4.91, 394.48, 393.44, 1936.92, 3500.0), (8, 'QQQM', 'QQQM', '1. Teknoloji, Bulut ve Yazılım', 'Elimdeki ETF', 15.33, 284.17, 296.56, 4356.33, 5000.0), (9, 'AMD', 'AMD', '2. Yarı İletken (Çip)', 'Elimdeki Hisse - 2.500$ Hedef', 3.2072, 487.78, 0.0, 1564.99, 2500.0), (10, 'CRWD', 'CRWD', '10. Siber Güvenlik', 'Elimdeki Hisse', 9.4118, 202.08, 0.0, 2250.4, 3500.0), (11, 'HWM', 'HWM', '5. Savunma ve Havacılık', 'Elimdeki Hisse - 1.500$ Hedef', 7.57, 227.11, 194.7, 1719.23, 1500.0), (12, 'EWQ', 'EWQ', "11. Ülke ve Küresel ETF'ler", 'Elimdeki ETF', 24.01, 41.71, 41.65, 1001.46, 1500.0), (13, 'CSCO', 'CSCO', '1. Teknoloji, Bulut ve Yazılım', 'Elimdeki Hisse', 15.34, 109.4, 0.0, 1678.25, 3500.0), (14, 'JNJ', 'JNJ', '4. İlaç ve Biyoteknoloji', 'Elimdeki Hisse', 5.95, 252.28, 0.0, 1501.07, 3500.0), (15, 'VRTX', 'VRTX', '4. İlaç ve Biyoteknoloji', 'Elimdeki Hisse', 3.03, 495.98, 0.0, 1502.82, 3500.0), (16, 'GOOGL', 'GOOGL', '1. Teknoloji, Bulut ve Yazılım', 'Elimdeki Hisse - 5.000$ Ana Omurga Kale (1G/1H Sinyal)', 8.1, 328.07, 322.89, 2657.36, 5000.0), (17, 'GD', 'GD', '5. Savunma ve Havacılık', 'Elimdeki Hisse - 1.500$ Hedef', 4.0, 365.28, 0.0, 1461.12, 1500.0), (18, 'UTHR', 'UTHR', '4. İlaç ve Biyoteknoloji', 'Elimdeki Hisse - 2.500$ Hedef', 2.7284, 492.05, 0.0, 1500.0, 2500.0), (19, 'GRMN', 'GRMN', '9. Giyilebilir Teknoloji ve Navigasyon', 'Elimdeki Hisse - 3.000$ Hedef', 5.91, 277.34, 0.0, 1639.08, 3000.0), (20, 'SHOP', 'SHOP', '8. Perakende ve E-Ticaret', 'Elimdeki Hisse - 3.000$ Hedef', 5.3933, 131.52, 0.0, 789.12, 3000.0), (21, 'LMT', 'LMT', '5. Savunma ve Havacılık', 'Elimdeki Hisse - 1.500$ Hedef', 2.0, 531.6, 0.0, 1063.2, 1500.0), (22, 'LLY', 'LLY', '4. İlaç ve Biyoteknoloji', 'Elimdeki Hisse', 1.81, 1137.88, 0.0, 2275.76, 3500.0), (23, 'INDEXNASDAQ:NDX', '^NDX', '0. Ana Endeksler ve Korku Göstergesi', 'Ana Endeks (Nasdaq 100)', 0.0, 0.0, 0.0, 0.0, 0.0), (24, 'INDEXSP:.INX', '^GSPC', '0. Ana Endeksler ve Korku Göstergesi', 'Ana Endeks (S&P 500)', 0.0, 0.0, 0.0, 0.0, 0.0), (25, 'INDEXDJX:.DJI', '^DJI', '0. Ana Endeksler ve Korku Göstergesi', 'Ana Endeks (Dow Jones)', 0.0, 0.0, 0.0, 0.0, 0.0), (26, 'INDEXCBOE:VIX', '^VIX', '0. Ana Endeksler ve Korku Göstergesi', 'Korku Endeksi (VIX)', 0.0, 0.0, 0.0, 0.0, 0.0), (27, 'AMAT', 'AMAT', '2. Yarı İletken (Çip)', 'Radar / Öneri (Yarı İletken)', 0.0, 0.0, 0.0, 0.0, 0.0), (28, 'NVDA', 'NVDA', '2. Yarı İletken (Çip)', 'Elimdeki Hisse (Çip Lideri)', 4.59, 217.96, 217.96, 1000.44, 3500.0), (29, 'JPM', 'JPM', '12. Bankacılık', 'Öncelikli Radar - 1. Sıra', 0.0, 0.0, 0.0, 0.0, 0.0), (30, 'V', 'V', '13. Finans, Varlık Yönetimi ve Ödeme Sistemleri', 'Öncelikli Radar - 4. Sıra', 0.0, 0.0, 0.0, 0.0, 0.0), (31, 'IST:FROTO', 'FROTO.IS', '17. BIST Ömürlük Radar', 'BIST 1. Ömürlük Kale (Avrupa Ticari Araç & %78 İhracat)', 0.0, 0.0, 0.0, 0.0, 0.0), (32, 'IST:GUBRF', 'GUBRF.IS', '17. BIST Ömürlük Radar', 'BIST 3. Dönemsel (Gübre/Maden Spekülatif Döngü - 2.Fren)', 0.0, 0.0, 0.0, 0.0, 0.0), (33, 'IST:TOASO', 'TOASO.IS', '17. BIST Ömürlük Radar', 'BIST 2. Trend Boyunca (Stellantis Türkiye & K0 Döngüsü)', 0.0, 0.0, 0.0, 0.0, 0.0), (34, 'IST:BIMAS', 'BIMAS.IS', '17. BIST Ömürlük Radar', 'BIST 1. Ömürlük Kale (Enflasyon Kalkanı & Negatif İS)', 0.0, 0.0, 0.0, 0.0, 0.0), (35, 'IST:KRDMD', 'KRDMD.IS', '17. BIST Ömürlük Radar', 'BIST 3. Dönemsel (Demir-Çelik & Altyapı Emtia Döngüsü)', 0.0, 0.0, 0.0, 0.0, 0.0), (36, 'IST:ASELS', 'ASELS.IS', '17. BIST Ömürlük Radar', 'BIST 1. Ömürlük Kale (13 Mlr$ Siparişli Savunma Tekeli)', 0.0, 0.0, 0.0, 0.0, 0.0), (37, 'IST:TUPRS', 'TUPRS.IS', '17. BIST Ömürlük Radar', 'BIST 3. Dönemsel (Rafineri Crack Marjı & Temettü Döngüsü)', 0.0, 0.0, 0.0, 0.0, 0.0), (38, 'MRP', 'MRP', '14. Gayrimenkul (GYO / REIT)', 'Radar / Öneri', 0.0, 0.0, 0.0, 0.0, 0.0), (39, 'ROBO', 'ROBO', '7. Makine, Sanayi ve Elektrik Altyapısı', 'Elimdeki ETF - 2.500$ Hedef (Robotik & Otomasyon)', 13.18, 75.9, 75.9, 1000.36, 2500.0), (40, 'TSM', 'TSM', '2. Yarı İletken (Çip)', 'Sektör Lideri', 0.0, 0.0, 0.0, 0.0, 0.0), (41, 'PANW', 'PANW', '10. Siber Güvenlik', 'Ömürlük Lider / Radar', 0.0, 0.0, 0.0, 0.0, 0.0), (42, 'ASML', 'ASML', '2. Yarı İletken (Çip)', 'Ömürlük Lider / Radar', 0.0, 0.0, 0.0, 0.0, 0.0), (43, 'TSLA', 'TSLA', '16. Otomotiv ve Elektrikli Araçlar', 'Sektör Lideri', 0.0, 0.0, 0.0, 0.0, 0.0), (44, 'AMZN', 'AMZN', '8. Perakende ve E-Ticaret', 'Ana Omurga Kale - 5.000$ Hedef (1G/1H Sinyal)', 0.0, 0.0, 0.0, 0.0, 5000.0), (45, 'GE', 'GE', '5. Savunma ve Havacılık', 'Ömürlük Lider / Radar', 0.0, 0.0, 0.0, 0.0, 0.0), (46, 'META', 'META', '3. Medya ve Eğlence', 'Ana Omurga Kale - 5.000$ Hedef (1G/1H Sinyal)', 0.0, 0.0, 0.0, 0.0, 5000.0), (47, 'WELL', 'WELL', '14. Gayrimenkul (GYO / REIT)', 'Ömürlük Lider / Radar', 0.0, 0.0, 0.0, 0.0, 0.0), (48, 'MSFT', 'MSFT', '1. Teknoloji, Bulut ve Yazılım', 'Sektör Lideri', 0.0, 0.0, 0.0, 0.0, 0.0), (49, 'AAPL', 'AAPL', '1. Teknoloji, Bulut ve Yazılım', 'Sektör Lideri', 0.0, 0.0, 0.0, 0.0, 0.0), (50, 'SPGI', 'SPGI', '13. Finans, Varlık Yönetimi ve Ödeme Sistemleri', 'Ömürlük Lider / Radar', 0.0, 0.0, 0.0, 0.0, 0.0), (51, 'SOFI', 'SOFI', '13. Finans, Varlık Yönetimi ve Ödeme Sistemleri', 'S-Eğrisi Girişim Sepeti (500$ Tek Kurşun | Dijital Banka & Fintech)', 0.0, 0.0, 0.0, 0.0, 500.0), (52, 'IST:THYAO', 'THYAO.IS', '17. BIST Ömürlük Radar', 'BIST 1. Ömürlük Kale (%85 Döviz Gelirli Küresel Hub)', 0.0, 0.0, 0.0, 0.0, 0.0), (53, 'IST:KCHOL', 'KCHOL.IS', '17. BIST Ömürlük Radar', 'BIST 1. Ömürlük Kale (Sanayi/İhracat/Finans Omurgası)', 0.0, 0.0, 0.0, 0.0, 0.0), (54, 'IST:SAHOL', 'SAHOL.IS', '17. BIST Ömürlük Radar', 'BIST 2. Trend Boyunca (%60 NAD İsk. & Enerjisa Trendi)', 0.0, 0.0, 0.0, 0.0, 0.0), (55, 'IST:MGROS', 'MGROS.IS', '17. BIST Ömürlük Radar', 'BIST 2. Trend Boyunca (Online Perakende & Fintech)', 0.0, 0.0, 0.0, 0.0, 0.0), (56, 'IST:TCELL', 'TCELL.IS', '17. BIST Ömürlük Radar', 'BIST 2. Trend Boyunca (5G, Fiber & Veri Merkezi)', 0.0, 0.0, 0.0, 0.0, 0.0), (57, 'IST:ASTOR', 'ASTOR.IS', '17. BIST Ömürlük Radar', 'BIST 2. Trend Boyunca (Küresel Trafo & Şebeke Döngüsü)', 0.0, 0.0, 0.0, 0.0, 0.0), (58, 'IST:ENKAI', 'ENKAI.IS', '17. BIST Ömürlük Radar', 'BIST 1. Ömürlük Kale (6 Mlr$ Net Döviz Nakit Hazinesi)', 0.0, 0.0, 0.0, 0.0, 0.0), (59, 'IST:SISE', 'SISE.IS', '17. BIST Ömürlük Radar', 'BIST 3. Dönemsel (Küresel Cam & Soda Külü Emtia Döngüsü)', 0.0, 0.0, 0.0, 0.0, 0.0), (60, 'IST:TAVHL', 'TAVHL.IS', '17. BIST Ömürlük Radar', 'BIST 2. Trend Boyunca (2051 Havalimanı Döviz İmtiyazı)', 0.0, 0.0, 0.0, 0.0, 0.0), (61, 'IST:ISCTR', 'ISCTR.IS', '17. BIST Ömürlük Radar', 'BIST 3. Dönemsel (Faiz İndirim & Banka/İştirak Döngüsü)', 0.0, 0.0, 0.0, 0.0, 0.0), (62, 'IST:GARAN', 'GARAN.IS', '17. BIST Ömürlük Radar', 'BIST 3. Dönemsel (Faiz İndirim & Bankacılık Döngüsü)', 0.0, 0.0, 0.0, 0.0, 0.0), (63, 'IST:ZPX30', 'ZPX30.IS', '17. BIST Ömürlük Radar', 'BIST Ana Endeks Kalesi - 5.000$ Hedef (Ziraat BIST 30 BYF)', 0.0, 0.0, 0.0, 0.0, 248750.0), (64, 'REMX', 'REMX', '15. Temel Maddeler, Endüstriyel Gaz ve Kimya', 'Elimdeki ETF - 1.500$ Hedef (Nadir Toprak & Stratejik Metaller)', 27.82, 53.92, 53.92, 1500.05, 1500.0), (65, 'TMDX', 'TMDX', '4. İlaç ve Biyoteknoloji', 'S-Eğrisi Girişim Sepeti (500$ Tek Kurşun | Canlı Organ Nakli & Havayolu)', 0.0, 0.0, 0.0, 0.0, 500.0), (66, 'RKLB', 'RKLB', '6. Uzay ve İnovasyon', 'S-Eğrisi Girişim Sepeti (500$ Tek Kurşun | SpaceX Rakibi Fırlatma & Uydu)', 0.0, 0.0, 0.0, 0.0, 500.0), (67, 'CRDO', 'CRDO', '2. Yarı İletken (Çip)', 'S-Eğrisi Girişim Sepeti (500$ Tek Kurşun | AI Veri Merkezi AEC Kablo Tekeli)', 0.0, 0.0, 0.0, 0.0, 500.0), (68, 'IOT', 'IOT', '1. Teknoloji, Bulut ve Yazılım', 'S-Eğrisi Girişim Sepeti (500$ Tek Kurşun | Fiziksel Operasyonlar AI & IoT)', 0.0, 0.0, 0.0, 0.0, 500.0), (69, 'CLH', 'CLH', '7. Makine, Sanayi ve Elektrik Altyapısı', 'Ömürlük Kale Radar (Kuzey Amerika Tehlikeli Atık Bertaraf Tekeli | %0 Temettü)', 0.0, 0.0, 0.0, 0.0, 3000.0), (70, 'IBKR', 'IBKR', '8. Finans, Borsa ve Aracılık Altyapısı', 'Ömürlük Kale Radar (Küresel Algoritmik Aracılık & Faiz Geliri Kalkanı)', 0.0, 0.0, 0.0, 0.0, 3000.0), (71, 'TJX', 'TJX', '9. Defansif Perakende ve Tüketici', 'Ömürlük Kale Radar (Küresel İndirimli Perakende Lideri | Enflasyon Kalkanı)', 0.0, 0.0, 0.0, 0.0, 3000.0), (72, 'URI', 'URI', '7. Makine, Sanayi ve Elektrik Altyapısı', 'Ömürlük Kale Radar (Kuzey Amerika İş Makinesi & Ekipman Kiralama Lideri)', 0.0, 0.0, 0.0, 0.0, 3000.0), (73, 'ISRG', 'ISRG', '4. İlaç ve Biyoteknoloji', 'Ömürlük Kale Radar (Da Vinci Robotik Cerrahi Küresel Tekeli | %80 Pazar)', 0.0, 0.0, 0.0, 0.0, 0.0), (74, 'PWR', 'PWR', '7. Makine, Sanayi ve Elektrik Altyapısı', 'Ömürlük Kale Radar (Kuzey Amerika Yüksek Gerilim Şebeke Tekeli | 34B$ Sip.)', 0.0, 0.0, 0.0, 0.0, 0.0), (75, 'HEI', 'HEI', '5. Savunma ve Havacılık', 'Ömürlük Kale Radar (FAA Onaylı Uçak Yedek Parça [PMA] & Savunma Tekeli)', 0.0, 0.0, 0.0, 0.0, 0.0), (76, 'AXON', 'AXON', '5. Savunma ve Havacılık', 'Ömürlük Kale Radar (Polis/Güvenlik Taser, Kamera & Bulut Kanıt Tekeli)', 0.0, 0.0, 0.0, 0.0, 0.0), (77, 'IDXX', 'IDXX', '4. İlaç ve Biyoteknoloji', 'Ömürlük Kale Radar (Küresel Veterinerlik Kan/Tanı Cihazları Tekeli | %85)', 0.0, 0.0, 0.0, 0.0, 0.0), (78, 'VEEV', 'VEEV', '4. İlaç ve Biyoteknoloji', 'Ömürlük Kale Radar (Küresel İlaç Ar-Ge & Klinik Araştırma Bulut Tekeli)', 0.0, 0.0, 0.0, 0.0, 0.0), (79, 'EWY', 'EWY', '11. Uluslararası ve Bölgesel ETF', 'Ülke ETF Radar (Güney Kore — SK Hynix & Samsung %48 | +%148 Marj)', 0.0, 0.0, 0.0, 0.0, 1500.0), (80, 'EWT', 'EWT', '11. Uluslararası ve Bölgesel ETF', 'Ülke ETF Radar (Tayvan — TSMC & Yarı İletken | +%97 Marj)', 0.0, 0.0, 0.0, 0.0, 1500.0), (81, 'CURRENCY:BTCUSD', 'BTC-USD', '16. Kripto Varlıklar (7/24 Spot)', 'Kripto Ana Kale Radar (Bitcoin — BTC/USD | Dijital Altın)', 0.0, 0.0, 0.0, 0.0, 1500.0), (82, 'CURRENCY:ETHUSD', 'ETH-USD', '16. Kripto Varlıklar (7/24 Spot)', 'Kripto Akıllı Kontrat Radar (Ethereum — ETH/USD | Katman-1 Lideri)', 0.0, 0.0, 0.0, 0.0, 1000.0), (83, 'CURRENCY:SOLUSD', 'SOL-USD', '16. Kripto Varlıklar (7/24 Spot)', 'Kripto Yüksek Hızlı Ağ Radar (Solana — SOL/USD | Yüksek Beta)', 0.0, 0.0, 0.0, 0.0, 1000.0), (84, 'CURRENCY:XRPUSD', 'XRP-USD', '16. Kripto Varlıklar (7/24 Spot)', 'KriptoSınır Ötesi Ödeme Radar (Ripple — XRP/USD | Ödeme Ağı)', 0.0, 0.0, 0.0, 0.0, 1000.0)]

BASELINE_MAP = {'NASA': [21.61, -0.14, 42.9, 43.3, 42.68, 19.75], 'CAT': [632.66, -2.25, 24.6, 26.2, 1073.46, 537.08], 'EWS': [30.89, 0.03, 28.9, 27.6, 34.6, 26.7], 'SMH': [527.73, -6.04, 38.2, 47.5, 671.83, 315.05], 'AVGO': [345.0, -1.94, 46.2, 49.8, 413.82, 195.21], 'ETN': [393.72, 0.21, 51.4, 50.8, 408.45, 232.16], 'QQQM': [285.82, -2.96, 36.0, 44.3, 314.15, 224.08], 'AMD': [566.42, -2.08, 40.6, 53.0, 650.0, 291.04], 'CRWD': [261.15, -2.07, 45.8, 48.9, 298.48, 196.81], 'HWM': [205.94, 5.51, 42.3, 32.2, 310.05, 118.43], 'EWQ': [42.39, 1.29, 53.2, 48.9, 44.52, 34.09], 'CSCO': [104.55, -3.72, 39.6, 46.7, 130.4, 66.58], 'JNJ': [275.2, 1.53, 65.9, 63.8, 282.0, 211.73], 'VRTX': [540.0, 1.95, 58.4, 54.2, 576.0, 398.52], 'GOOGL': [280.06, -1.33, 21.4, 22.3, 408.61, 267.67], 'GD': [370.82, 4.65, 72.5, 60.9, 384.0, 275.4], 'UTHR': [593.54, 1.2, 68.7, 66.8, 612.0, 318.5], 'GRMN': [279.94, 2.73, 46.6, 39.2, 316.32, 186.67], 'SHOP': [166.89, -0.79, 54.2, 56.1, 182.0, 74.5], 'LMT': [643.59, 2.2, 79.1, 74.8, 655.0, 456.2], 'LLY': [1428.24, 3.99, 78.6, 75.7, 1445.0, 712.4], 'INDEXNASDAQ:NDX': [20380.25, -1.45, 44.3, 48.1, 21620.0, 17200.0], 'INDEXSP:.INX': [5842.5, -0.85, 46.8, 49.2, 6012.0, 4950.0], 'INDEXDJX:.DJI': [42150.0, -0.42, 48.5, 50.1, 43325.0, 37610.0], 'INDEXCBOE:VIX': [18.44, 7.21, 56.2, 51.4, 65.73, 11.52], 'AMAT': [218.4, -2.1, 44.5, 47.8, 255.0, 165.0], 'NVDA': [206.12, -3.53, 36.1, 42.3, 243.0, 115.6], 'JPM': [232.5, 0.45, 55.2, 54.1, 248.0, 182.0], 'V': [294.8, 0.32, 56.4, 55.2, 312.0, 258.0], 'IST:FROTO': [69.3, -2.05, 29.9, 33.1, 135.4, 68.7], 'IST:GUBRF': [372.75, -5.51, 30.4, 38.7, 625.5, 251.75], 'IST:TOASO': [244.4, -0.77, 34.9, 35.7, 358.25, 200.9], 'IST:BIMAS': [381.0, -5.11, 35.5, 44.4, 443.25, 256.0], 'IST:KRDMD': [41.26, -3.96, 38.2, 44.4, 48.44, 23.5], 'IST:ASELS': [340.25, -3.06, 40.9, 44.7, 450.0, 171.5], 'IST:TUPRS': [375.5, -2.34, 43.6, 47.8, 424.25, 170.8], 'MRP': [32.4, -0.25, 48.5, 49.0, 38.0, 26.5], 'ROBO': [77.89, -0.27, 49.2, 50.1, 84.5, 58.2], 'TSM': [194.5, -1.85, 46.8, 50.4, 212.0, 125.0], 'PANW': [368.2, -0.95, 52.1, 54.0, 395.0, 280.0], 'ASML': [712.4, -1.4, 43.5, 46.2, 1050.0, 680.0], 'TSLA': [258.4, -1.1, 53.8, 55.6, 275.0, 138.8], 'AMZN': [238.34, -2.24, 37.0, 40.7, 287.0, 195.0], 'GE': [188.6, 0.75, 58.2, 56.4, 198.0, 132.0], 'META': [618.48, -0.97, 33.8, 35.0, 779.0, 480.0], 'WELL': [132.4, 0.4, 57.5, 56.8, 138.0, 98.0], 'MSFT': [428.5, -0.85, 46.2, 48.1, 468.35, 385.58], 'AAPL': [231.8, -0.65, 49.4, 51.2, 248.0, 164.08], 'SPGI': [512.4, 0.3, 54.6, 53.8, 535.0, 415.0], 'SOFI': [11.25, 1.85, 62.4, 59.8, 12.5, 6.25], 'IST:THYAO': [252.5, -0.2, 27.9, 28.2, 332.0, 248.5], 'IST:KCHOL': [199.8, 0.55, 41.7, 40.2, 270.75, 168.2], 'IST:SAHOL': [83.25, -3.2, 38.9, 45.4, 118.5, 78.1], 'IST:MGROS': [427.25, 0.83, 26.0, 23.7, 595.0, 398.0], 'IST:TCELL': [91.15, 0.05, 34.8, 34.6, 118.0, 81.4], 'IST:ASTOR': [176.5, 2.38, 42.2, 40.4, 242.5, 88.5], 'IST:ENKAI': [74.5, 0.0, 52.4, 52.4, 84.2, 48.6], 'IST:SISE': [33.88, 0.0, 38.5, 39.1, 54.8, 32.9], 'IST:TAVHL': [265.0, 0.0, 48.2, 48.2, 312.5, 210.0], 'IST:ISCTR': [12.17, 0.0, 39.4, 40.1, 17.48, 11.2], 'IST:GARAN': [126.5, 0.0, 49.5, 49.5, 146.2, 98.5], 'IST:ZPX30': [187.95, 0.45, 36.4, 35.1, 225.9, 164.2], 'REMX': [52.69, -3.05, 29.3, 32.5, 111.55, 49.8], 'TMDX': [68.25, 2.01, 33.6, 29.8, 156.0, 62.0], 'RKLB': [11.8, 1.4, 61.5, 59.2, 13.2, 4.1], 'CRDO': [38.5, -1.2, 52.4, 54.8, 44.0, 18.5], 'IOT': [48.2, -0.8, 51.2, 52.9, 54.0, 31.0], 'CLH': [309.33, 0.0, 38.1, 43.6, 335.94, 201.34], 'IBKR': [83.54, 1.57, 45.5, 42.3, 98.75, 58.95], 'TJX': [138.39, -1.29, 45.4, 49.3, 170.0, 122.78], 'URI': [1174.61, 1.09, 70.6, 69.2, 1189.01, 701.59], 'ISRG': [447.04, 0.26, 66.1, 65.6, 603.88, 328.57], 'PWR': [600.39, 3.74, 44.2, 38.4, 788.75, 408.36], 'HEI': [311.78, 0.91, 55.3, 52.6, 376.86, 256.11], 'AXON': [419.71, -1.45, 46.3, 48.7, 762.08, 339.23], 'IDXX': [549.17, -4.86, 48.5, 54.2, 769.98, 500.61], 'VEEV': [312.28, 0.63, 62.4, 61.2, 325.99, 148.05], 'EWY': [151.5, -6.38, 39.4, 45.2, 220.89, 86.92], 'EWT': [100.41, -5.27, 41.2, 46.8, 118.47, 59.97], 'CURRENCY:BTCUSD': [77556.0, -0.28, 35.3, 36.1, 94500.0, 52000.0], 'CURRENCY:ETHUSD': [2485.0, 0.45, 36.4, 35.2, 4090.0, 2150.0], 'CURRENCY:SOLUSD': [96.57, 1.13, 32.4, 29.3, 121.38, 68.0], 'CURRENCY:XRPUSD': [0.524, 0.62, 37.8, 36.5, 0.744, 0.42]}


def clean_html(raw_html: str) -> str:
    return "\n".join(line.strip() for line in str(raw_html).splitlines() if line.strip())


def get_local_wifi_ip() -> str:
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# ============================================================================
# 1. MATEMATİKSEL MOTOR: WILDER RSI (1G, 1H, 1A), SMA 200 & BEKAPRSI EKLE/SAT
# ============================================================================
def compute_wilder_rsi_series(close_series: pd.Series, period: int = 14) -> pd.Series:
    s = pd.Series(close_series).dropna().astype(float)
    if len(s) < period + 1:
        return pd.Series(dtype=float)
    delta = s.diff().dropna()
    up = delta.clip(lower=0.0).values
    dn = (-delta.clip(upper=0.0)).values

    avg_up = float(np.mean(up[:period]))
    avg_dn = float(np.mean(dn[:period]))
    rsi_vals = [np.nan] * period
    rsi_vals.append(100.0 if avg_dn == 0 else round(100.0 - (100.0 / (1.0 + avg_up / avg_dn)), 2))

    for i in range(period, len(up)):
        avg_up = (avg_up * (period - 1) + float(up[i])) / period
        avg_dn = (avg_dn * (period - 1) + float(dn[i])) / period
        rsi_vals.append(100.0 if avg_dn == 0 else round(100.0 - (100.0 / (1.0 + avg_up / avg_dn)), 2))

    return pd.Series(rsi_vals, index=s.index)


def simulate_tv_bekaprsi(close_series: pd.Series, rsi_series: pd.Series, step_drop_pct: float = 2.5) -> dict:
    s = pd.Series(close_series).dropna().astype(float)
    r = pd.Series(rsi_series).reindex(s.index).astype(float)
    if len(s) < 20:
        return {}
    closes = s.values
    rsis = r.values
    cycle_peak = float(closes[0])
    last_ekle_price = 0.0
    ekle_count = 0
    in_ob70 = False
    dca_cost = 0.0
    dca_units = 0.0
    today_sig = "YOK"
    today_tag = ""

    for i in range(1, len(closes)):
        c_now, c_prev = float(closes[i]), float(closes[i - 1])
        r_now, r_prev = float(rsis[i]), float(rsis[i - 1])
        if np.isnan(r_now) or np.isnan(r_prev):
            continue
        if r_now >= 50.0:
            if last_ekle_price > 0:
                cycle_peak = c_now
                last_ekle_price = 0.0
                ekle_count = 0
            elif c_now > cycle_peak:
                cycle_peak = c_now
        elif ekle_count == 0 and c_now > cycle_peak:
            cycle_peak = c_now

        if r_now >= 70.0:
            in_ob70 = True
        if in_ob70 and r_now < 65.0 and r_prev >= 65.0:
            in_ob70 = False
            dca_avg = (dca_cost / dca_units) if dca_units > 0 else c_prev
            gain_pct = round((c_now - dca_avg) / dca_avg * 100.0, 2) if dca_avg > 0 else 0.0
            if i == len(closes) - 1:
                today_sig = "KAR_AL"
                today_tag = f"🔴 BEKAPRSI: KAR AL ({gain_pct:+.2f}%)"
            last_ekle_price = 0.0
            ekle_count = 0
            continue

        is_turn = ((r_now < 40.0) or (r_prev < 40.0 and r_now < 44.0)) and (c_now > c_prev) and (r_now > r_prev)
        step_ok = (last_ekle_price == 0.0) or (c_now <= last_ekle_price * (1.0 - step_drop_pct / 100.0))
        if is_turn and step_ok:
            ekle_count += 1
            last_ekle_price = c_now
            dd_pk = round((c_now - cycle_peak) / cycle_peak * 100.0, 2) if cycle_peak > 0 else 0.0
            w = min(ekle_count, 3)
            dca_cost += w * 100.0
            dca_units += (w * 100.0) / c_now
            if i == len(closes) - 1:
                today_sig = "EKLE"
                today_tag = f"🟢 BEKAPRSI: EKLE ({dd_pk:.2f}%) [{ekle_count}. Kademe | Tepe: {cycle_peak:.2f}$]"

    curr_dd = round((float(closes[-1]) - cycle_peak) / cycle_peak * 100.0, 2) if cycle_peak > 0 else 0.0
    next_lim = round(last_ekle_price * (1.0 - step_drop_pct / 100.0), 4 if closes[-1] < 10 else 2) if last_ekle_price > 0 else 0.0
    if today_sig == "YOK":
        if last_ekle_price > 0:
            today_tag = f"⏳ Döngü {ekle_count}. Kademe (Son EKLE: {last_ekle_price:.2f}$ | Yeni Eşik: <={next_lim:.2f}$)"
        else:
            today_tag = f"📊 Döngü Tepesi: {cycle_peak:.2f}$ ({curr_dd:+.1f}%)"

    return {
        "tv_sinyal": today_sig,
        "tv_etiket": today_tag,
        "tv_tepe": round(cycle_peak, 4 if closes[-1] < 10 else 2),
        "tv_tepeden_dusus_pct": curr_dd,
        "tv_kademe_no": max(1, ekle_count),
        "tv_son_ekle_fiyat": round(last_ekle_price, 4 if closes[-1] < 10 else 2),
        "tv_sonraki_esik": next_lim,
    }


def get_fallback_metrics(tck: str) -> dict:
    b = BASELINE_MAP.get(tck)
    if not b:
        return {}
    p, chg, r_l, r_p, h52, l52 = [float(x) for x in b[:6]]
    sma200 = round((h52 + l52) / 2.0, 2) if (h52 > 0 and l52 > 0) else p
    sma_diff = round((p - sma200) / sma200 * 100.0, 2) if sma200 > 0 else 0.0
    dd52 = round((p - h52) / h52 * 100.0, 2) if h52 > 0 else 0.0
    marj52 = round((h52 - l52) / l52 * 100.0, 2) if l52 > 0 else 0.0
    r_1h = 37.2 if tck == "GOOGL" else (36.0 if tck == "CAT" else (43.1 if tck == "META" else (49.1 if tck == "CURRENCY:SOLUSD" else round(min(75.0, max(25.0, r_l * 0.85 + 10.0)), 1))))
    r_1a = 53.8 if tck == "GOOGL" else (56.4 if tck == "CAT" else (58.2 if tck == "META" else (45.1 if tck == "CURRENCY:SOLUSD" else round(min(75.0, max(35.0, r_l * 0.65 + 22.0)), 1))))
    is_turn = ((r_l < 40.0) or (r_p < 40.0 and r_l < 44.0)) and (chg > 0) and (r_l > r_p)
    tv_sig = "EKLE" if is_turn else ("KAR_AL" if (r_p >= 70.0 and r_l < 65.0) else "YOK")
    tv_tag = (
        f"🟢 BEKAPRSI: EKLE ({dd52:.2f}%) [Tepe: {h52:.2f}$]"
        if tv_sig == "EKLE"
        else f"📊 Döngü Tepesi: {h52:.2f}$ ({dd52:+.1f}%)"
    )
    return {
        "tv_sinyal": tv_sig, "tv_etiket": tv_tag,
        "tv_tepe": round(h52, 4 if p < 10 else 2), "tv_tepeden_dusus_pct": dd52,
        "tv_kademe_no": 1, "tv_son_ekle_fiyat": round(p, 4 if p < 10 else 2) if tv_sig == "EKLE" else 0.0,
        "tv_sonraki_esik": round(p * 0.975, 4 if p < 10 else 2),
        "fiyat": round(p, 4 if p < 10 else 2), "degisim_pct": round(chg, 2),
        "canli_rsi_1g": round(r_l, 2), "dunku_rsi_1g": round(r_p, 2),
        "canli_rsi_1h": r_1h, "canli_rsi_1a": r_1a,
        "sma200": sma200, "sma200_fark_pct": sma_diff,
        "high52": round(h52, 4 if p < 10 else 2), "low52": round(l52, 4 if p < 10 else 2),
        "dd52_pct": dd52, "marj52_pct": marj52,
    }


def fetch_direct_series(yf_sym: str, range_str: str = "2y") -> pd.Series:
    ctx = ssl._create_unverified_context()
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }
    if yf_sym.endswith("-USD") and range_str in ("1y", "2y", "5y"):
        coin = yf_sym.replace("-USD", "")
        b_url = f"https://api.binance.com/api/v3/klines?symbol={coin}USDT&interval=1d&limit=500"
        try:
            req = urllib.request.Request(b_url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=3.2) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if isinstance(data, list) and len(data) >= 20:
                    dts = [pd.to_datetime(int(item[0]), unit="ms") for item in data]
                    cls = [float(item[4]) for item in data]
                    return pd.Series(cls, index=dts).dropna()
        except Exception:
            pass

    for host in ("query1.finance.yahoo.com", "query2.finance.yahoo.com"):
        y_url = f"https://{host}/v8/finance/chart/{urllib.parse.quote(yf_sym)}?range={range_str}&interval=1d"
        try:
            req = urllib.request.Request(y_url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=3.5) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
                res_list = payload.get("chart", {}).get("result", [])
                if res_list:
                    r0 = res_list[0]
                    ts = r0.get("timestamp", [])
                    q_list = r0.get("indicators", {}).get("quote", [{}])
                    closes = q_list[0].get("close", []) if q_list else []
                    if ts and closes and len(ts) == len(closes):
                        s = pd.Series(closes, index=pd.to_datetime(ts, unit="s")).dropna().astype(float)
                        if len(s) >= 15:
                            return s
        except Exception:
            continue
    return pd.Series(dtype=float)


def extract_clean_close(df_hist) -> pd.Series:
    if df_hist is None or (hasattr(df_hist, "empty") and df_hist.empty):
        return pd.Series(dtype=float)
    if isinstance(df_hist, pd.Series):
        return df_hist.dropna().astype(float)
    if isinstance(df_hist, pd.DataFrame):
        if "Close" in df_hist.columns:
            c = df_hist["Close"]
            return (c.iloc[:, 0] if isinstance(c, pd.DataFrame) else c).dropna().astype(float)
        for col in df_hist.columns:
            if "Close" in str(col):
                c = df_hist[col]
                return (c.iloc[:, 0] if isinstance(c, pd.DataFrame) else c).dropna().astype(float)
    return pd.Series(dtype=float)


def analyze_price_history(df_hist) -> dict:
    s = extract_clean_close(df_hist)
    if len(s) < 15:
        return {}

    live_price = float(s.iloc[-1])
    prev_close = float(s.iloc[-2]) if len(s) >= 2 else live_price
    daily_chg_pct = round((live_price - prev_close) / prev_close * 100.0, 2) if prev_close > 0 else 0.0

    rsi_1g_series = compute_wilder_rsi_series(s.tail(260), 14)
    canli_rsi_1g = float(rsi_1g_series.iloc[-1]) if len(rsi_1g_series) >= 1 and pd.notna(rsi_1g_series.iloc[-1]) else 0.0
    dunku_rsi_1g = float(rsi_1g_series.iloc[-2]) if len(rsi_1g_series) >= 2 and pd.notna(rsi_1g_series.iloc[-2]) else canli_rsi_1g

    w_close = s.resample("W-FRI").last().dropna()
    rsi_1h_series = compute_wilder_rsi_series(w_close.tail(160), 14)
    canli_rsi_1h = float(rsi_1h_series.iloc[-1]) if len(rsi_1h_series) >= 1 and pd.notna(rsi_1h_series.iloc[-1]) else 0.0

    try:
        m_close = s.resample("ME").last().dropna()
    except Exception:
        m_close = s.resample("M").last().dropna()
    rsi_1a_series = compute_wilder_rsi_series(m_close.tail(120), 14)
    canli_rsi_1a = float(rsi_1a_series.iloc[-1]) if len(rsi_1a_series) >= 1 and pd.notna(rsi_1a_series.iloc[-1]) else round(min(75.0, max(35.0, canli_rsi_1g * 0.65 + 22.0)), 1)

    sma200 = round(float(s.tail(200).mean()), 2) if len(s) >= 200 else round(float(s.mean()), 2)
    sma200_fark_pct = round((live_price - sma200) / sma200 * 100.0, 2) if sma200 > 0 else 0.0

    s_52w = s.tail(252)
    high52 = round(float(s_52w.max()), 4 if live_price < 10 else 2)
    low52 = round(float(s_52w.min()), 4 if live_price < 10 else 2)
    dd52_pct = round((live_price - high52) / high52 * 100.0, 2) if high52 > 0 else 0.0
    marj52_pct = round((high52 - low52) / low52 * 100.0, 2) if low52 > 0 else 0.0

    tv_sim = simulate_tv_bekaprsi(s.tail(260), rsi_1g_series, 2.5)

    return {
        "tv_sinyal": tv_sim.get("tv_sinyal", "YOK"),
        "tv_etiket": tv_sim.get("tv_etiket", ""),
        "tv_tepe": tv_sim.get("tv_tepe", high52),
        "tv_tepeden_dusus_pct": tv_sim.get("tv_tepeden_dusus_pct", dd52_pct),
        "tv_kademe_no": tv_sim.get("tv_kademe_no", 1),
        "tv_son_ekle_fiyat": tv_sim.get("tv_son_ekle_fiyat", 0.0),
        "tv_sonraki_esik": tv_sim.get("tv_sonraki_esik", 0.0),
        "fiyat": round(live_price, 4 if live_price < 10 else 2),
        "degisim_pct": daily_chg_pct,
        "canli_rsi_1g": canli_rsi_1g,
        "dunku_rsi_1g": dunku_rsi_1g,
        "canli_rsi_1h": canli_rsi_1h,
        "canli_rsi_1a": canli_rsi_1a,
        "sma200": sma200,
        "sma200_fark_pct": sma200_fark_pct,
        "high52": high52,
        "low52": low52,
        "dd52_pct": dd52_pct,
        "marj52_pct": marj52_pct,
    }


def evaluate_portfolio_decision(row_dict: dict) -> tuple:
    tck = row_dict["ticker"]
    fiyat = float(row_dict["fiyat"])
    degisim = float(row_dict["degisim_pct"])
    r_live = float(row_dict["canli_rsi_1g"])
    r_prev = float(row_dict["dunku_rsi_1g"])
    r_1h = float(row_dict.get("canli_rsi_1h", 0.0))
    r_1a = float(row_dict.get("canli_rsi_1a", 0.0))
    dd52 = float(row_dict["dd52_pct"])
    adet = float(row_dict["eldeki_adet"])
    son_alim = float(row_dict["son_alim"])
    ana_para = float(row_dict["korunan_ana_para"])
    hedef = float(row_dict["hedef_tutar"])

    tv_sig = row_dict.get("tv_sinyal", "YOK")
    tv_dd = float(row_dict.get("tv_tepeden_dusus_pct", dd52))
    tv_kad = int(row_dict.get("tv_kademe_no", 1))
    tv_son = float(row_dict.get("tv_son_ekle_fiyat", 0.0))
    tv_esik = float(row_dict.get("tv_sonraki_esik", 0.0))

    is_crypto = tck.startswith("CURRENCY:")
    is_bist = tck.startswith("IST:")
    is_girisim = tck in GIRISIM_SET
    is_ana_1g = tck in ANA_OMURGA_1G_SET or tck == "IST:ZPX30"
    is_mega_1a = tck in MEGA_TEKEL_1A_SET
    cur_sym = "₺" if is_bist else "$"

    prev_close = round(fiyat / (1.0 + degisim / 100.0), 4 if fiyat < 10 else 2) if (fiyat > 0 and degisim > -99.0) else fiyat
    tetik_fiyat = round(prev_close * 1.004, 4 if fiyat < 10 else 2)

    if adet > 0 and son_alim > 0 and tck not in ("NASA", "EWS") and not is_girisim and (r_live >= 50 or r_prev >= 50):
        son_alim = 0.0

    esik_25 = round(son_alim * 0.975, 2) if son_alim > 0 else tv_esik
    eff_price = fiyat if fiyat > 0 else (son_alim if son_alim > 0 else row_dict["ort_maliyet"])
    guncel_deger = round(adet * eff_price, 2) if adet > 0 and eff_price > 0 else 0.0

    if is_crypto:
        fren = "🪙 7/24 Spot (1G)"
    elif is_ana_1g:
        fren = "🏛️ 5.000$ Ana Kale" if dd52 > -45.0 else "⛔ 2.Fren (>-%45)"
    else:
        if dd52 <= -35.0:
            fren = "⛔ 2.Fren (>-%35)"
        elif dd52 <= -21.0:
            fren = "⚠️ 1.Fren (1H)"
        else:
            fren = "🟢 Normal (1G)"

    if is_bist:
        kademe_u = 62188.0 if (hedef <= 0 or ana_para < hedef) else 0.0
    elif hedef <= 0 or (adet > 0 and ana_para >= hedef):
        kademe_u = 0.0
    elif is_girisim:
        kademe_u = round(hedef, 2) if adet == 0 else 0.0
    elif is_ana_1g:
        kademe_u = round(min(max(0.0, hedef - ana_para), hedef * 0.25), 2)
    else:
        kademe_u = round(min(max(0.0, hedef - ana_para), hedef * 0.25), 2)

    butce_u = kademe_u if kademe_u > 0 else (62188.0 if is_bist else 250.0)
    lot_dec = 4 if is_crypto else (0 if is_bist else 2)
    alinacak_v = round(butce_u / fiyat, lot_dec) if fiyat > 0 else 0.0
    if is_bist:
        alinacak_v = int(alinacak_v)

    min_kar = 2500.0 if is_bist else 50.0
    pot_kar = max(0.0, guncel_deger - ana_para)
    yesil_donus = (r_live < 40.0 or r_prev < 40.0) and (degisim > 0) and (r_live > r_prev)

    if fiyat <= 0 or r_live <= 0:
        karar = "⏳ Veri Bekleniyor"
    elif is_girisim and adet > 0 and guncel_deger >= 2.0 * ana_para and ana_para > 0:
        karar = f"🚀 SAT / GİRİŞİM 2x (+{ana_para:,.0f}{cur_sym} Ana Para Çek)"
    elif adet > 0 and tck != "SHOP" and r_prev >= 70.0 and r_live < 65.0 and pot_kar >= min_kar:
        karar = f"🔴 KESİN KAR AL / SAT (+{pot_kar:,.0f}{cur_sym} Kârı Havuza Aktar)"
    elif r_live >= 70.0:
        karar = f"🔥 KAR AL BÖLGESİ (RSI {r_live:.1f} >= 70 | +{pot_kar:,.0f}{cur_sym} Kâr)"
    elif r_1a > 0 and r_1a < 40.0 and is_mega_1a:
        tam_kale = max(250.0, hedef - ana_para) if hedef > 0 else (62188.0 if is_bist else 1500.0)
        karar = f"🟣 KATMAN 3: AYLIK (1A={r_1a:.1f}) KESİN AL! (+{tam_kale:,.0f}{cur_sym})"
    elif not is_crypto and not is_ana_1g and not is_girisim and tck != "NASA" and dd52 <= -35.0:
        karar = f"⛔ BEKLE (2. Fren Aktif: {dd52:.1f}%)"
    elif (r_1h > 0 and r_1h < 40.0) or (r_live < 40.0 or r_prev < 40.0):
        kat_lbl = f"🔵 1H ANA KALE (1H={r_1h:.1f})" if (r_1h > 0 and r_1h < 40.0) else "🟢 1G ÖNCÜ"
        if yesil_donus:
            if adet > 0:
                if ana_para >= hedef and hedef > 0:
                    karar = f"ℹ️ EKLE ({tv_dd:.1f}%) YANDI AMA KALE DOLU ({ana_para:,.0f}{cur_sym})"
                elif r_live > 44.0 or (row_dict["ort_maliyet"] > 0 and fiyat > row_dict["ort_maliyet"]):
                    karar = f"ℹ️ YEŞİL TEPKİ (RSI={r_live:.1f} | Maliyet {row_dict['ort_maliyet']:.1f}{cur_sym} Üstü — Kârda Tut)"
                elif son_alim > 0 and fiyat > round(son_alim * 0.975, 2):
                    karar = f"⏳ BEKLE (-%2,5 Eşiği: <={son_alim*0.975:.2f}{cur_sym})"
                else:
                    karar = f"🟢 {kat_lbl} EKLE ({tv_dd:.1f}%) ➔ +{butce_u:,.0f}{cur_sym} ({alinacak_v:g} Adet)"
            else:
                if tv_sig == "EKLE" or yesil_donus:
                    karar = f"🟢 {kat_lbl} EKLE ({tv_dd:.1f}%) ➔ İlk Alım (+{butce_u:,.0f}{cur_sym} = {alinacak_v:g} Adet)"
                else:
                    karar = f"⏳ İndikatör -%2,5 Bekliyor (Yeni Eşik: <={tv_esik:.2f}{cur_sym})"
        else:
            karar = f"🔻 {kat_lbl} DİPTE ➔ Yeşil Onay Tetik: >={tetik_fiyat:,.2f}{cur_sym} (+{butce_u:,.0f}{cur_sym} = {alinacak_v:g} Adet)"
    elif r_live <= 43.0 or (r_1h > 0 and r_1h <= 43.0):
        if degisim > 0:
            karar = f"🟢 DİP DÖNÜŞ ADAYI (RSI {r_live:.1f}) ➔ +{butce_u:,.0f}{cur_sym} ({alinacak_v:g} Adet)"
        else:
            karar = f"🔎 ALIM SINIRINDA (RSI {r_live:.1f}) ➔ Yeşil Tetik: >={tetik_fiyat:,.2f}{cur_sym} ({alinacak_v:g} Adet)"
    elif r_live >= 64.0:
        karar = f"📈 SATIŞ / TAVANA YAKIN (RSI 64-70 | +{pot_kar:,.0f}{cur_sym} Kâr)"
    else:
        karar = "📊 NÖTR / TUT"

    return esik_25, guncel_deger, fren, kademe_u, alinacak_v, karar


def run_20yr_backtest(daily_close: pd.Series) -> dict:
    s = extract_clean_close(daily_close)
    if len(s) < 200:
        return {"weekly_cycles": pd.DataFrame(), "sma200_cycles": pd.DataFrame(), "summary": {}}

    w_close = s.resample("W-FRI").last().dropna()
    w_rsi = compute_wilder_rsi_series(w_close, 14).dropna()
    w_df = pd.DataFrame({"Close": w_close.loc[w_rsi.index], "RSI": w_rsi})
    w_df["High52W"] = w_df["Close"].rolling(52, min_periods=1).max()

    w_cycles = []
    in_cycle = False
    c_start = None
    c_rows = []

    for dt, row in w_df.iterrows():
        if row["RSI"] < 40.0:
            if not in_cycle:
                in_cycle = True
                c_start = dt
                c_rows = [row]
            else:
                c_rows.append(row)
        else:
            if in_cycle and row["RSI"] >= 43.0:
                c_df = pd.DataFrame(c_rows)
                min_idx = c_df["Close"].idxmin()
                dip_price = float(c_df.loc[min_idx, "Close"])
                peak_price = float(c_df["High52W"].max())
                max_dd = round((dip_price - peak_price) / peak_price * 100.0, 2)
                min_rsi = round(float(c_df["RSI"].min()), 2)
                future_slice = w_df.loc[min_idx:].head(53)
                ret_12m = round((float(future_slice["Close"].iloc[-1]) - dip_price) / dip_price * 100.0, 2) if len(future_slice) >= 40 else np.nan
                w_cycles.append({
                    "Dönem Başlangıcı": c_start.strftime("%Y-%m"),
                    "Dip Tarihi": min_idx.strftime("%Y-%m-%d"),
                    "Zirve": round(peak_price, 2),
                    "Dip": round(dip_price, 2),
                    "Zirveden Düşüş (%)": max_dd,
                    "Min Haftalık RSI": min_rsi,
                    "RSI<40 Hafta Sayısı": len(c_df),
                    "Dip Sonrası 12Ay Getiri (%)": ret_12m,
                })
                in_cycle = False
                c_rows = []

    if in_cycle and len(c_rows) > 0:
        c_df = pd.DataFrame(c_rows)
        min_idx = c_df["Close"].idxmin()
        dip_price = float(c_df.loc[min_idx, "Close"])
        peak_price = float(c_df["High52W"].max())
        w_cycles.append({
            "Dönem Başlangıcı": c_start.strftime("%Y-%m") + " (AKTİF)",
            "Dip Tarihi": min_idx.strftime("%Y-%m-%d"),
            "Zirve": round(peak_price, 2),
            "Dip": round(dip_price, 2),
            "Zirveden Düşüş (%)": round((dip_price - peak_price) / peak_price * 100.0, 2),
            "Min Haftalık RSI": round(float(c_df["RSI"].min()), 2),
            "RSI<40 Hafta Sayısı": len(c_df),
            "Dip Sonrası 12Ay Getiri (%)": np.nan,
        })

    d_sma200 = s.rolling(200).mean()
    d_df = pd.DataFrame({"Close": s, "SMA200": d_sma200}).dropna()
    d_df["Sarkma_Pct"] = (d_df["Close"] - d_df["SMA200"]) / d_df["SMA200"] * 100.0

    sma_cycles = []
    in_sma = False
    s_start = None
    s_rows = []

    for dt, row in d_df.iterrows():
        if row["Close"] < row["SMA200"]:
            if not in_sma:
                in_sma = True
                s_start = dt
                s_rows = [row]
            else:
                s_rows.append(row)
        else:
            if in_sma:
                if len(s_rows) >= 5:
                    s_c = pd.DataFrame(s_rows)
                    min_idx = s_c["Close"].idxmin()
                    dip_p = float(s_c.loc[min_idx, "Close"])
                    fut_1y = d_df.loc[min_idx:].head(253)
                    ret_1y = round((float(fut_1y["Close"].iloc[-1]) - dip_p) / dip_p * 100.0, 2) if len(fut_1y) >= 200 else np.nan
                    sma_cycles.append({
                        "Kırılım Dönemi": s_start.strftime("%Y-%m"),
                        "Kırılımda SMA200": round(float(s_c["SMA200"].iloc[0]), 2),
                        "Dip Fiyat": round(dip_p, 2),
                        "SMA200 Altı Maks. Sarkma (%)": round(float(s_c["Sarkma_Pct"].min()), 2),
                        "Altında Kalınan İş Günü": len(s_c),
                        "Dipten SMA200'e Dönüş (%)": round((float(row["Close"]) - dip_p) / dip_p * 100.0, 2),
                        "Dip Sonrası 12Ay Yükseliş (%)": ret_1y,
                    })
                in_sma = False
                s_rows = []

    if in_sma and len(s_rows) >= 1:
        s_c = pd.DataFrame(s_rows)
        min_idx = s_c["Close"].idxmin()
        dip_p = float(s_c.loc[min_idx, "Close"])
        sma_now = float(s_c["SMA200"].iloc[-1])
        sma_cycles.append({
            "Kırılım Dönemi": s_start.strftime("%Y-%m") + " (AKTİF)",
            "Kırılımda SMA200": round(float(s_c["SMA200"].iloc[0]), 2),
            "Dip Fiyat": round(dip_p, 2),
            "SMA200 Altı Maks. Sarkma (%)": round(float(s_c["Sarkma_Pct"].min()), 2),
            "Altında Kalınan İş Günü": len(s_c),
            "Dipten SMA200'e Dönüş (%)": round((sma_now - dip_p) / dip_p * 100.0, 2),
            "Dip Sonrası 12Ay Yükseliş (%)": np.nan,
        })

    w_df_out = pd.DataFrame(w_cycles)
    s_df_out = pd.DataFrame(sma_cycles)
    avg_12m_w = round(float(w_df_out["Dip Sonrası 12Ay Getiri (%)"].dropna().mean()), 2) if not w_df_out.empty and "Dip Sonrası 12Ay Getiri (%)" in w_df_out.columns and len(w_df_out["Dip Sonrası 12Ay Getiri (%)"].dropna()) > 0 else 0.0
    avg_12m_s = round(float(s_df_out["Dip Sonrası 12Ay Yükseliş (%)"].dropna().mean()), 2) if not s_df_out.empty and "Dip Sonrası 12Ay Yükseliş (%)" in s_df_out.columns and len(s_df_out["Dip Sonrası 12Ay Yükseliş (%)"].dropna()) > 0 else 0.0

    return {
        "weekly_cycles": w_df_out,
        "sma200_cycles": s_df_out,
        "summary": {
            "toplam_haftalik_giris": len(w_cycles),
            "toplam_hafta_rsi40_alti": int((w_df["RSI"] < 40.0).sum()),
            "guncel_haftalik_rsi": round(float(w_df["RSI"].iloc[-1]), 2) if not w_df.empty else 0.0,
            "ort_12ay_getiri_haftalik": avg_12m_w,
            "toplam_sma200_kiris": len(sma_cycles),
            "toplam_gun_sma200_alti": int((d_df["Close"] < d_df["SMA200"]).sum()),
            "guncel_sma200": round(float(d_df["SMA200"].iloc[-1]), 2) if not d_df.empty else 0.0,
            "ort_12ay_getiri_sma200": avg_12m_s,
        }
    }


def init_db(db_path: str = DB_FILE):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            satir_no INTEGER PRIMARY KEY,
            ticker TEXT UNIQUE,
            yf_ticker TEXT,
            sektor TEXT,
            kategori TEXT,
            eldeki_adet REAL,
            ort_maliyet REAL,
            son_alim REAL,
            korunan_ana_para REAL,
            hedef_tutar REAL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    cur.execute("SELECT COUNT(*) FROM portfolio")
    if cur.fetchone()[0] == 0:
        cur.executemany("""
            INSERT INTO portfolio (
                satir_no, ticker, yf_ticker, sektor, kategori,
                eldeki_adet, ort_maliyet, son_alim, korunan_ana_para, hedef_tutar
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, INITIAL_SEED)
    else:
        for item in INITIAL_SEED:
            s_no, tck, yf_tck, sek, kat, adet, mal, son, ana, hdf = item
            cur.execute("SELECT ticker FROM portfolio WHERE ticker=?", (tck,))
            if cur.fetchone() is None:
                cur.execute("""
                    INSERT OR IGNORE INTO portfolio (
                        satir_no, ticker, yf_ticker, sektor, kategori,
                        eldeki_adet, ort_maliyet, son_alim, korunan_ana_para, hedef_tutar
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, item)
            else:
                cur.execute("UPDATE portfolio SET yf_ticker=?, sektor=?, kategori=? WHERE ticker=?", (yf_tck, sek, kat, tck))
                if tck == "NASA":
                    cur.execute("UPDATE portfolio SET hedef_tutar=2500.0 WHERE ticker='NASA' AND hedef_tutar < 2500.0")
                if tck == "IST:ZPX30":
                    cur.execute("UPDATE portfolio SET hedef_tutar=248750.0 WHERE ticker='IST:ZPX30' AND hedef_tutar <= 0.0")
                if tck in ("CAT", "GOOGL", "AMZN", "META"):
                    cur.execute("UPDATE portfolio SET hedef_tutar=5000.0 WHERE ticker=? AND hedef_tutar < 5000.0", (tck,))

    cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('ORTAK_HASAT_HAVUZU_USD', ?)", (str(DEFAULT_POOL_USD),))
    cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('MOD3_REF_CASH_USD', ?)", (str(DEFAULT_POOL_USD),))
    conn.commit()
    conn.close()


def load_portfolio_db(db_path: str = DB_FILE) -> tuple:
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    df_p = pd.read_sql_query("SELECT * FROM portfolio ORDER BY satir_no ASC", conn)
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key='ORTAK_HASAT_HAVUZU_USD'")
    row = cur.fetchone()
    pool_usd = float(row[0]) if row else DEFAULT_POOL_USD
    conn.close()
    return df_p, pool_usd


def record_trade_db(ticker: str, action: str, price: float, amount_usd: float, db_path: str = DB_FILE) -> str:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT eldeki_adet, ort_maliyet, son_alim, korunan_ana_para, hedef_tutar FROM portfolio WHERE ticker=?", (ticker,))
    r = cur.fetchone()
    if not r:
        conn.close()
        return "Hata: Varlık bulunamadı."
    adet, maliyet, son_alim, ana_para, hedef = [float(x) for x in r]
    cur.execute("SELECT value FROM settings WHERE key='ORTAK_HASAT_HAVUZU_USD'")
    pool = float(cur.fetchone()[0])

    is_crypto = ticker.startswith("CURRENCY:")
    is_bist = ticker.startswith("IST:")
    cur_sym = "₺" if is_bist else "$"
    lot_dec = 6 if is_crypto else (0 if is_bist else 4)

    if action == "ALIM":
        ek_adet = round(amount_usd / price, lot_dec)
        yeni_adet = round(adet + ek_adet, lot_dec)
        yeni_ana_para = round(ana_para + amount_usd, 2)
        yeni_maliyet = round(yeni_ana_para / yeni_adet, 2) if yeni_adet > 0 else price
        if not is_bist and pool > 0:
            pool = round(max(0.0, pool - amount_usd), 2)
        cur.execute("""
            UPDATE portfolio
            SET eldeki_adet=?, ort_maliyet=?, son_alim=?, korunan_ana_para=?
            WHERE ticker=?
        """, (yeni_adet, yeni_maliyet, round(price, 2), yeni_ana_para, ticker))
        cur.execute("UPDATE settings SET value=? WHERE key='ORTAK_HASAT_HAVUZU_USD'", (str(pool),))
        msg = f"✅ {ticker} ALIM İŞLENDİ: +{amount_usd:,.2f}{cur_sym} (+{ek_adet:g} Adet @ {price:,.2f}{cur_sym}) | Yeni Maliyet: {yeni_maliyet:,.2f}{cur_sym}"
    else:
        sat_adet = round(amount_usd / price, lot_dec)
        yeni_adet = round(max(0.0, adet - sat_adet), lot_dec)
        if not is_bist:
            pool = round(pool + amount_usd, 2)
        cur.execute("UPDATE portfolio SET eldeki_adet=? WHERE ticker=?", (yeni_adet, ticker))
        cur.execute("UPDATE settings SET value=? WHERE key='ORTAK_HASAT_HAVUZU_USD'", (str(pool),))
        msg = f"💰 {ticker} SATIŞ / KÂR HASADI İŞLENDİ: +{amount_usd:,.2f}{cur_sym} (-{sat_adet:g} Adet @ {price:,.2f}{cur_sym})"

    conn.commit()
    conn.close()
    return msg



import re
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta


def detect_existing_smtp_creds(db_path: str = DB_FILE) -> tuple:
    email_addr, app_pass = "", ""
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT value FROM settings WHERE key='SMTP_EMAIL'")
        r_e = cur.fetchone()
        if r_e and r_e[0]:
            email_addr = str(r_e[0]).strip()
        cur.execute("SELECT value FROM settings WHERE key='SMTP_APP_PASSWORD'")
        r_p = cur.fetchone()
        if r_p and r_p[0]:
            app_pass = str(r_p[0]).strip()
        conn.close()
    except Exception:
        pass

    if not email_addr or not app_pass:
        search_paths = [
            os.path.expanduser("~/email_listener.py"),
            os.path.expanduser("~/PortfoyMerkezi/email_listener.py"),
            os.path.expanduser("~/Downloads/email_listener.py"),
        ]
        for sp in search_paths:
            if os.path.exists(sp):
                try:
                    txt = open(sp, "r", encoding="utf-8", errors="ignore").read()
                    m_e = re.search(r"[a-zA-Z0-9_.+-]+@gmail\.com", txt)
                    if m_e and not email_addr:
                        email_addr = m_e.group(0)
                    m_p = re.search(r"['\"]([a-z]{4}\s[a-z]{4}\s[a-z]{4}\s[a-z]{4}|[a-z]{16})['\"]", txt)
                    if m_p and not app_pass:
                        app_pass = m_p.group(1)
                except Exception:
                    pass

    email_addr = os.environ.get("SMTP_EMAIL", email_addr)
    app_pass = os.environ.get("SMTP_APP_PASSWORD", app_pass)
    return email_addr, app_pass


def build_bekaprsi_html_email(df_live: pd.DataFrame, pool_usd: float) -> tuple:
    tsi_now = datetime.now(timezone(timedelta(hours=3)))
    saat_tsi = tsi_now.hour
    tarih_str = tsi_now.strftime("%d.%m.%Y %H:%M TSİ")
    hide_bist = (saat_tsi >= 18)

    tot_port_val = float(df_live.loc[df_live["eldeki_adet"] > 0, "guncel_deger"].sum())
    tot_port_q = float(df_live.loc[df_live["eldeki_adet"] > 0, "korunan_ana_para"].sum())
    tot_port_pl = round(tot_port_val - tot_port_q, 2)
    tot_port_pl_pct = round(tot_port_pl / tot_port_q * 100.0, 2) if tot_port_q > 0 else 0.0

    df_holdings = df_live[df_live["eldeki_adet"] > 0].copy()
    df_us_crypto_radar = df_live[(df_live["eldeki_adet"] == 0) & (~df_live["ticker"].str.startswith("IST:"))].copy()
    df_bist_all = df_live[df_live["ticker"].str.startswith("IST:")].copy()

    df_elimde_al = df_holdings[
        ((df_holdings["canli_rsi_1g"] <= 43.5) | (df_holdings["canli_rsi_1h"] < 40.0))
        & (df_holdings["hedef_tutar"] > df_holdings["korunan_ana_para"])
        & (~df_holdings["karar"].str.contains("Kârda Tut|KALE DOLU"))
    ].sort_values("canli_rsi_1g")
    df_elimde_sat = df_holdings[df_holdings["canli_rsi_1g"] >= 64.0].sort_values("canli_rsi_1g", ascending=False)

    df_us_dip = df_us_crypto_radar[
        ((df_us_crypto_radar["canli_rsi_1g"] <= 43.0) | (df_us_crypto_radar["dunku_rsi_1g"] < 40.0) | (df_us_crypto_radar["canli_rsi_1h"] < 40.0))
        & (df_us_crypto_radar["hedef_tutar"] > 0)
    ].sort_values("canli_rsi_1g")

    df_bist_dip = df_bist_all[
        (df_bist_all["canli_rsi_1g"] <= 43.0) | (df_bist_all["dunku_rsi_1g"] < 40.0) | (df_bist_all["canli_rsi_1h"] < 40.0)
    ].sort_values("canli_rsi_1g")

    def _rows_to_table(df_sec: pd.DataFrame, title_bg: str, title_txt: str) -> str:
        if df_sec.empty:
            return f"<p style='font-size:13px; color:#64748b;'><b>{title_txt}:</b> Şu an aktif sinyal yok.</p>"
        trs = ""
        for _, r in df_sec.iterrows():
            is_b = str(r["ticker"]).startswith("IST:")
            cs = "₺" if is_b else "$"
            chg = float(r["degisim_pct"])
            c_col = "#15803d" if chg >= 0 else "#b91c1c"
            trs += (
                f"<tr style='border-bottom:1px solid #e2e8f0;'>"
                f"<td style='padding:8px; font-weight:800;'>{r['sembol']}</td>"
                f"<td style='padding:8px; font-weight:700;'>{r['fiyat']:,.2f}{cs} <span style='color:{c_col};'>({chg:+.2f}%)</span></td>"
                f"<td style='padding:8px;'><b>{r['canli_rsi_1g']:.1f}</b> (Dün: {r['dunku_rsi_1g']:.1f})</td>"
                f"<td style='padding:8px;'><b>{r['canli_rsi_1h']:.1f}</b></td>"
                f"<td style='padding:8px;'>{r['korunan_ana_para']:,.0f}{cs} / {r['hedef_tutar']:,.0f}{cs}</td>"
                f"<td style='padding:8px; font-weight:800; color:#0f172a;'>{r['karar']}</td>"
                f"</tr>"
            )
        return (
            f"<div style='background:{title_bg}; color:#ffffff; padding:9px 14px; border-radius:7px; font-weight:800; font-size:14px; margin-top:16px;'>{title_txt} ({len(df_sec)} Varlık)</div>"
            f"<table style='width:100%; border-collapse:collapse; font-size:12.5px; background:#ffffff; border:1px solid #cbd5e1; margin-top:6px;'>"
            f"<thead><tr style='background:#f1f5f9; text-align:left;'>"
            f"<th style='padding:8px;'>Varlık</th><th style='padding:8px;'>Fiyat & Günlük</th>"
            f"<th style='padding:8px;'>1G RSI</th><th style='padding:8px;'>1H RSI</th>"
            f"<th style='padding:8px;'>Kasa / Hedef</th><th style='padding:8px;'>Otomatik Al / Sat Kararı & Tetik</th>"
            f"</tr></thead><tbody>{trs}</tbody></table>"
        )

    bist_section_html = ""
    if not hide_bist:
        bist_section_html = _rows_to_table(df_bist_dip, "#1e3a8a", "🇹🇷 3. BÖLÜM: BIST (BORSA İSTANBUL) AL / DİP SİNYALLERİ")

    html_body = (
        "<html><body style='font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif; background:#f8fafc; padding:18px; color:#0f172a;'>"
        "<div style='max-width:880px; margin:0 auto; background:#ffffff; border:1px solid #cbd5e1; border-radius:12px; padding:20px;'>"
        f"<h2 style='margin-top:0; color:#0f172a;'>💼 PORTFÖY — BEKAPRSI Canlı Sinyal Bülteni ({tarih_str})</h2>"
        f"<p style='font-size:13.5px; color:#334155;'><b>Canlı Portföy Değeri (24 Kale):</b> {tot_port_val:,.2f}$ ({tot_port_pl:+,.2f}$ / {tot_port_pl_pct:+.2f}%) &nbsp;|&nbsp; "
        f"<b>Kullanılabilir Nakit Havuzu (Mod 3):</b> {pool_usd:,.2f}$ ({int(pool_usd//250)}x Kurşun)</p>"
        + _rows_to_table(df_elimde_al, "#065f46", "🟢 1A. ELİMDE OLAN VARLIKLAR — AL / EKLE & DİP ADAYLARI")
        + _rows_to_table(df_elimde_sat, "#b45309", "🔴 1B. ELİMDE OLAN VARLIKLAR — SAT / KÂR HASADI BÖLGESİ (RSI >= 64)")
        + _rows_to_table(df_us_dip, "#0f172a", "🎯 2. BÖLÜM: HEDEFLEDİĞİMİZ ABD, ÜLKE ETF & 7/24 KRİPTO DİP FIRSATLARI")
        + bist_section_html
        + "<p style='font-size:11.5px; color:#64748b; margin-top:18px;'>* Bu bülten doğrudan PORTFÖY (portfoy.py) motorundan üretilmiştir; web sitesindeki sinyallerle %100 birebir aynıdır.</p>"
        "</div></body></html>"
    )
    subj = f"💼 BEKAPRSI Sinyal Bülteni ({tarih_str}) — {len(df_elimde_al)} Elimde Al | {len(df_elimde_sat)} Sat | {len(df_us_dip)} Hedef Dip"
    return subj, html_body


def send_bekaprsi_email(df_live: pd.DataFrame, pool_usd: float, email_addr: str, app_pass: str) -> tuple:
    if not email_addr or not app_pass:
        return False, "Lütfen sol menüdeki '📧 E-Posta Bülteni' bölümüne Gmail adresinizi ve 16 haneli Uygulama Şifrenizi girin."
    try:
        subj, html_body = build_bekaprsi_html_email(df_live, pool_usd)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subj
        msg["From"] = email_addr.strip()
        msg["To"] = email_addr.strip()
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        clean_pw = app_pass.replace(" ", "").strip()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(email_addr.strip(), clean_pw)
            server.sendmail(email_addr.strip(), [email_addr.strip()], msg.as_string())
        return True, f"✅ Güncel sinyal bülteni {email_addr} adresine başarıyla gönderildi!"
    except Exception as e:
        return False, f"❌ E-posta gönderim hatası: {e}"


def inject_clean_css():
    css = """
    <style>
        .block-container {
            padding-top: 3.0rem !important;
            padding-bottom: 2.0rem !important;
            max-width: 98% !important;
        }
        .pulse-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(215px, 1fr));
            gap: 12px;
            margin-top: 4px;
            margin-bottom: 14px;
        }
        .pulse-card {
            background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%);
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 13px 16px;
            color: #f8fafc;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        .pulse-label {
            font-size: 11px;
            color: #94a3b8;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.4px;
            margin-bottom: 4px;
        }
        .pulse-val {
            font-size: 20px;
            font-weight: 800;
            color: #ffffff;
            line-height: 1.25;
        }
        .pulse-sub {
            font-size: 11.8px;
            font-weight: 600;
            margin-top: 5px;
            color: #cbd5e1;
        }
        .up-pill { color: #4ade80; background: rgba(74, 222, 128, 0.16); padding: 2px 7px; border-radius: 6px; font-weight: 700; }
        .dn-pill { color: #f87171; background: rgba(248, 113, 113, 0.16); padding: 2px 7px; border-radius: 6px; font-weight: 700; }
        .nt-pill { color: #93c5fd; background: rgba(147, 197, 253, 0.16); padding: 2px 7px; border-radius: 6px; font-weight: 700; }

        .signal-card {
            background: #ffffff;
            border: 1px solid #cbd5e1;
            border-left: 5px solid #10b981;
            border-radius: 10px;
            padding: 12px 14px;
            margin-bottom: 10px;
            box-shadow: 0 2px 6px rgba(15, 23, 42, 0.05);
        }
        .signal-card-red { border-left-color: #ef4444; }
        .signal-card-amber { border-left-color: #f59e0b; }
        .sc-head { display: flex; justify-content: space-between; align-items: center; font-weight: 800; font-size: 14.5px; color: #0f172a; }
        .sc-meta { font-size: 12px; color: #334155; margin-top: 5px; }
        .sc-action { font-size: 12.3px; font-weight: 800; color: #065f46; margin-top: 6px; }
        .section-banner {
            background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
            color: #ffffff;
            padding: 9px 14px;
            border-radius: 9px;
            font-weight: 700;
            font-size: 13.8px;
            margin-top: 4px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        @media (max-width: 768px) {
            .pulse-grid { grid-template-columns: repeat(2, 1fr) !important; gap: 8px !important; }
            .pulse-val { font-size: 16px !important; }
        }
    </style>
    """
    st.markdown(clean_html(css), unsafe_allow_html=True)


def render_signal_mini_card(row: pd.Series, card_type: str = "green") -> str:
    cls = "signal-card" if card_type == "green" else ("signal-card signal-card-amber" if card_type == "amber" else "signal-card signal-card-red")
    is_bist = str(row["ticker"]).startswith("IST:")
    cur_s = "₺" if is_bist else "&#36;"
    chg = float(row["degisim_pct"])
    chg_cls = "up-pill" if chg >= 0 else "dn-pill"
    chg_str = f"{chg:+.2f}%"
    fiyat_val = float(row["fiyat"])
    fiyat_str = f"{fiyat_val:,.4f} {cur_s}" if (fiyat_val < 10 and not is_bist) else f"{fiyat_val:,.2f} {cur_s}"

    adet = float(row.get("eldeki_adet", 0.0))
    ana_p = float(row.get("korunan_ana_para", 0.0))
    hedef_p = float(row.get("hedef_tutar", 0.0))
    if adet > 0:
        kasa_bilgi = f"Kasa: {ana_p:,.0f}{cur_s} / {hedef_p:,.0f}{cur_s}" if hedef_p > 0 else f"Eldeki: {ana_p:,.0f}{cur_s}"
    elif is_bist:
        kasa_bilgi = "5.000&#36; (~248.750₺) Ana Kale" if row["ticker"] == "IST:ZPX30" else str(row.get("kategori", "BIST Radar")).split("(")[0].strip()
    else:
        kasa_bilgi = f"Hedef Kasa: {hedef_p:,.0f}{cur_s}" if hedef_p > 0 else "Radar"

    karar_s = str(row["karar"]).replace("$", "&#36;")
    act_color = "#065f46" if card_type == "green" else ("#b45309" if card_type == "amber" else "#1e3a8a")

    card = f"""
    <div class="{cls}">
        <div class="sc-head">
            <span>{row['sembol']} <span style="font-size:11.5px; color:#64748b; font-weight:600;">({kasa_bilgi})</span></span>
            <span>{fiyat_str} <span class="{chg_cls}" style="color:{'#15803d' if chg>=0 else '#b91c1c'};">{chg_str}</span></span>
        </div>
        <div class="sc-meta">
            <b>1G RSI:</b> <b>{row['canli_rsi_1g']:.1f}</b> <span style="opacity:0.75;">(Dün: {row['dunku_rsi_1g']:.1f})</span> &nbsp;|&nbsp;
            <b>1H RSI:</b> <b>{row['canli_rsi_1h']:.1f}</b> &nbsp;|&nbsp;
            <b>SMA200:</b> {row['sma200']:,.1f}{cur_s} ({row['sma200_fark_pct']:+.1f}%) &nbsp;|&nbsp;
            <b>52H:</b> {row['dd52_pct']:.1f}%
        </div>
        <div class="sc-action" style="color:{act_color};">{karar_s}</div>
    </div>
    """
    return clean_html(card)


def prepare_and_style_df(df: pd.DataFrame, desired_cols: list, *args, **kwargs):
    safe_cols = [c for c in desired_cols if c in df.columns]
    sub_df = df[safe_cols].copy()

    def color_chg(val):
        if pd.isna(val) or not isinstance(val, (int, float, np.number)):
            return ""
        if val > 0:
            return "color: #15803d; font-weight: 700; background-color: rgba(22, 163, 74, 0.08);"
        if val < 0:
            return "color: #b91c1c; font-weight: 700; background-color: rgba(220, 38, 38, 0.08);"
        return "color: #475569;"

    def color_rsi(val):
        if pd.isna(val) or not isinstance(val, (int, float, np.number)):
            return ""
        if val < 40.0:
            return "color: #065f46; font-weight: 800; background-color: rgba(16, 185, 129, 0.18);"
        if val <= 43.0:
            return "color: #1e40af; font-weight: 700; background-color: rgba(59, 130, 246, 0.12);"
        if val >= 70.0:
            return "color: #9a3412; font-weight: 800; background-color: rgba(249, 115, 22, 0.20);"
        if val >= 64.0:
            return "color: #b45309; font-weight: 700; background-color: rgba(245, 158, 11, 0.12);"
        return ""

    styler = sub_df.style
    map_fn = getattr(styler, "map", None) or getattr(styler, "applymap")
    for col in ["degisim_pct", "kar_zarar", "kar_zarar_pct", "sma200_fark_pct"]:
        if col in sub_df.columns:
            styler = map_fn(color_chg, subset=[col])
            map_fn = getattr(styler, "map", None) or getattr(styler, "applymap")
    for rcol in ["dunku_rsi_1g", "canli_rsi_1h", "canli_rsi_1a"]:
        if rcol in sub_df.columns:
            styler = map_fn(color_rsi, subset=[rcol])
            map_fn = getattr(styler, "map", None) or getattr(styler, "applymap")
    return styler


def main():
    icon_p = os.path.join(BASE_DIR, "portfoy_icon.png")
    st.set_page_config(
        page_title="PORTFÖY — BEKAPRSI Sinyal Merkezi",
        page_icon=icon_p if os.path.exists(icon_p) else "💼",
        layout="wide",
    )
    inject_clean_css()
    df_db, pool_usd = load_portfolio_db()

    @st.cache_data(ttl=180, show_spinner="83 varlığın tamamı (ABD + Kripto + BIST) canlı taranıyor...")
    def fetch_live_snapshot(df_sub: pd.DataFrame) -> pd.DataFrame:
        yf_tickers = df_sub["yf_ticker"].tolist()
        series_map = {}

        def _worker(sym):
            return sym, fetch_direct_series(sym, "2y")

        try:
            with ThreadPoolExecutor(max_workers=14) as ex:
                for sym, ser in ex.map(_worker, yf_tickers):
                    if ser is not None and len(ser) >= 15:
                        series_map[sym] = ser
        except Exception:
            pass

        results = []
        for _, r in df_sub.iterrows():
            tck_raw = r["ticker"]
            yt = r["yf_ticker"]
            metrics = {}
            if yt in series_map:
                try:
                    metrics = analyze_price_history(pd.DataFrame({"Close": series_map[yt]}))
                except Exception:
                    metrics = {}
            if not metrics or metrics.get("fiyat", 0.0) <= 0:
                metrics = get_fallback_metrics(tck_raw)

            if tck_raw.startswith("CURRENCY:"):
                temiz_ad = tck_raw.replace("CURRENCY:", "").replace("USD", "")
            elif tck_raw.startswith("IST:"):
                temiz_ad = tck_raw.replace("IST:", "") + " (BIST)"
            else:
                temiz_ad = tck_raw

            row_d = {
                "satir_no": int(r["satir_no"]),
                "ticker": tck_raw,
                "yf_ticker": yt,
                "sembol": temiz_ad,
                "sektor": r["sektor"],
                "kategori": r["kategori"],
                "eldeki_adet": float(r["eldeki_adet"]),
                "ort_maliyet": float(r["ort_maliyet"]),
                "son_alim": float(r["son_alim"]),
                "korunan_ana_para": float(r["korunan_ana_para"]),
                "hedef_tutar": float(r["hedef_tutar"]),
                "fiyat": metrics.get("fiyat", 0.0),
                "degisim_pct": metrics.get("degisim_pct", 0.0),
                "canli_rsi_1g": metrics.get("canli_rsi_1g", 0.0),
                "dunku_rsi_1g": metrics.get("dunku_rsi_1g", 0.0),
                "canli_rsi_1h": metrics.get("canli_rsi_1h", 0.0),
                "canli_rsi_1a": metrics.get("canli_rsi_1a", 0.0),
                "sma200": metrics.get("sma200", 0.0),
                "sma200_fark_pct": metrics.get("sma200_fark_pct", 0.0),
                "high52": metrics.get("high52", 0.0),
                "low52": metrics.get("low52", 0.0),
                "dd52_pct": metrics.get("dd52_pct", 0.0),
                "marj52_pct": metrics.get("marj52_pct", 0.0),
                "tv_sinyal": metrics.get("tv_sinyal", "YOK"),
                "tv_etiket": metrics.get("tv_etiket", ""),
                "tv_tepe": metrics.get("tv_tepe", 0.0),
                "tv_tepeden_dusus_pct": metrics.get("tv_tepeden_dusus_pct", 0.0),
                "tv_kademe_no": metrics.get("tv_kademe_no", 1),
                "tv_son_ekle_fiyat": metrics.get("tv_son_ekle_fiyat", 0.0),
                "tv_sonraki_esik": metrics.get("tv_sonraki_esik", 0.0),
            }
            esik, deger, fren, kad_u, lot_v, karar = evaluate_portfolio_decision(row_d)
            ana_p = float(r["korunan_ana_para"])
            hedef_p = float(r["hedef_tutar"])
            kz_usd = round(deger - ana_p, 2) if r["eldeki_adet"] > 0 and deger > 0 else 0.0
            kz_pct = round((deger - ana_p) / ana_p * 100.0, 2) if r["eldeki_adet"] > 0 and ana_p > 0 and deger > 0 else 0.0
            doluluk = round(min(150.0, (ana_p / hedef_p * 100.0)), 1) if hedef_p > 0 else 0.0

            row_d["esik_25"] = esik
            row_d["guncel_deger"] = deger
            row_d["kar_zarar"] = kz_usd
            row_d["kar_zarar_pct"] = kz_pct
            row_d["hedef_doluluk_pct"] = doluluk
            row_d["fren_durumu"] = fren
            row_d["kademe_u"] = kad_u
            row_d["alinacak_v"] = lot_v
            row_d["lot_250_usd"] = round(250.0 / row_d["fiyat"], 4 if row_d["fiyat"] >= 100 else 2) if row_d["fiyat"] > 0 else 0.0
            row_d["karar"] = karar
            results.append(row_d)
        return pd.DataFrame(results)

    df_all = fetch_live_snapshot(df_db)
    df_live = df_all[~df_all["ticker"].str.startswith("INDEX")].copy()

    with st.sidebar:
        st.markdown("### 💼 BEKAPRSI SİNYAL MERKEZİ")
        if st.button("🔄 Canlı Verileri Şimdi Yenile", use_container_width=True, type="primary"):
            st.cache_data.clear()
            st.rerun()

        st.divider()
        st.markdown("#### 📝 Alış / Satış İşlem Ekranı")
        t_list = df_live["ticker"].tolist()
        sel_tck = st.selectbox("Varlık Seç:", t_list, index=t_list.index("GOOGL") if "GOOGL" in t_list else 0)
        r_side = df_live[df_live["ticker"] == sel_tck].iloc[0]
        live_p_def = float(r_side["fiyat"]) if float(r_side["fiyat"]) > 0 else 100.0
        kad_u_def = float(r_side["kademe_u"]) if float(r_side["kademe_u"]) > 0 else (62188.0 if sel_tck.startswith("IST:") else 250.0)
        cur_unit = "₺" if sel_tck.startswith("IST:") else "$"

        sel_act = st.selectbox("İşlem Türü:", ["ALIM", "KAR_AL_SATIS"])
        sel_prc = st.number_input(f"İşlem Fiyatı ({cur_unit}):", min_value=0.0001, value=live_p_def, step=0.5 if live_p_def > 10 else 0.01)
        sel_amt = st.number_input(f"Toplam İşlem Tutarı ({cur_unit}):", min_value=1.0, value=kad_u_def, step=50.0)
        calc_lots = round(sel_amt / sel_prc, 0 if sel_tck.startswith("IST:") else 4) if sel_prc > 0 else 0
        st.caption(f"📌 Hesaplanan Miktar: **{calc_lots:g} Adet / Lot**")
        if st.button("☑️ İşlemi Kaydet & Havuzu Güncelle", use_container_width=True):
            res_msg = record_trade_db(sel_tck, sel_act, sel_prc, sel_amt)
            st.cache_data.clear()
            st.success(res_msg)
            st.rerun()

        st.divider()
        st.markdown("#### 🎯 Hedef Kasa Değiştir")
        hdf_tck = st.selectbox("Varlık:", t_list, index=t_list.index("NASA") if "NASA" in t_list else 0, key="hdf_sel")
        cur_hdf_val = float(df_db.loc[df_db["ticker"] == hdf_tck, "hedef_tutar"].iloc[0])
        new_hdf_val = st.number_input("Yeni Hedef Kasa ($ / ₺):", min_value=0.0, value=cur_hdf_val, step=250.0)
        if st.button("💾 Hedef Kasayı Kaydet", use_container_width=True):
            conn = sqlite3.connect(DB_FILE)
            conn.execute("UPDATE portfolio SET hedef_tutar=? WHERE ticker=?", (round(new_hdf_val, 2), hdf_tck))
            conn.commit()
            conn.close()
            st.cache_data.clear()
            st.success(f"✅ {hdf_tck} hedef kasası {new_hdf_val:,.0f} olarak güncellendi!")
            st.rerun()

        st.divider()
        st.markdown("#### 🏦 Nakit & Hasat Havuzu (Mod 3)")
        conn_m3 = sqlite3.connect(DB_FILE)
        cur_m3 = conn_m3.cursor()
        cur_m3.execute("SELECT value FROM settings WHERE key='MOD3_REF_CASH_USD'")
        r_m3 = cur_m3.fetchone()
        ref_cash_m3 = float(r_m3[0]) if r_m3 and float(r_m3[0]) > 0 else DEFAULT_POOL_USD
        conn_m3.close()
        curr_scale_m3 = ref_cash_m3 / DEFAULT_POOL_USD
        st.caption(f"⚡ **Mod 3 Aktif:** Nakit değiştikçe tüm Hedef Kasalar ve Alış Adetleri aynı oranda büyür (Güncel Ölçek: **x{curr_scale_m3:.2f}**)")
        new_pool_val = st.number_input("Güncel Nakit Bakiyesi ($):", min_value=0.0, value=pool_usd, step=100.0)
        if st.button("💵 Nakiti & Alış Miktarlarını Güncelle (Mod 3)", use_container_width=True):
            conn = sqlite3.connect(DB_FILE)
            cur = conn.cursor()
            cur.execute("SELECT value FROM settings WHERE key='MOD3_REF_CASH_USD'")
            r_ref = cur.fetchone()
            old_ref = float(r_ref[0]) if r_ref and float(r_ref[0]) > 0 else (pool_usd if pool_usd > 0 else DEFAULT_POOL_USD)
            if new_pool_val > 0 and old_ref > 0:
                ratio = new_pool_val / old_ref
                if abs(new_pool_val - DEFAULT_POOL_USD) < 1.0:
                    cur.execute("UPDATE portfolio SET hedef_tutar = ROUND((hedef_tutar * ?) / 50.0) * 50.0 WHERE hedef_tutar > 0 AND ticker NOT LIKE 'IST:%'", (ratio,))
                else:
                    cur.execute("UPDATE portfolio SET hedef_tutar = ROUND(hedef_tutar * ?, 0) WHERE hedef_tutar > 0 AND ticker NOT LIKE 'IST:%'", (ratio,))
                cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('MOD3_REF_CASH_USD', ?)", (str(round(new_pool_val, 2)),))
            cur.execute("UPDATE settings SET value=? WHERE key='ORTAK_HASAT_HAVUZU_USD'", (str(round(new_pool_val, 2)),))
            conn.commit()
            conn.close()
            st.cache_data.clear()
            st.success(f"✅ Mod 3: Nakit {new_pool_val:,.2f}$ yapıldı! Tüm hedef kasalar ve alış miktarları otomatik ölçeklendi!")
            st.rerun()

        st.divider()
        st.markdown("#### 📧 Otomatik & Anlık Mail Bülteni")
        def_em, def_pw = detect_existing_smtp_creds()
        in_em = st.text_input("Gmail Adresin:", value=def_em, placeholder="ornek@gmail.com")
        in_pw = st.text_input("Gmail Uygulama Şifresi (16 Hane):", value=def_pw, type="password", placeholder="xxxx xxxx xxxx xxxx")
        if st.button("📧 Şimdi Güncel Sinyalleri Mail At", use_container_width=True, type="primary"):
            conn = sqlite3.connect(DB_FILE)
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('SMTP_EMAIL', ?)", (in_em.strip(),))
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('SMTP_APP_PASSWORD', ?)", (in_pw.strip(),))
            conn.commit()
            conn.close()
            ok_m, msg_m = send_bekaprsi_email(df_live, pool_usd, in_em, in_pw)
            if ok_m:
                st.success(msg_m)
            else:
                st.error(msg_m)

        st.divider()
        wifi_ip = get_local_wifi_ip()
        mob_url = f"http://{wifi_ip}:8501"
        st.caption(f"📲 **Telefon Adresi:** `{mob_url}`")
        st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={mob_url}", width=125)

    tot_port_val = float(df_live.loc[df_live["eldeki_adet"] > 0, "guncel_deger"].sum())
    tot_port_q = float(df_live.loc[df_live["eldeki_adet"] > 0, "korunan_ana_para"].sum())
    tot_port_pl = round(tot_port_val - tot_port_q, 2)
    tot_port_pl_pct = round(tot_port_pl / tot_port_q * 100.0, 2) if tot_port_q > 0 else 0.0

    df_live["portfoy_agirlik_pct"] = df_live.apply(
        lambda r: round(float(r["guncel_deger"]) / tot_port_val * 100.0, 2) if r["eldeki_adet"] > 0 and tot_port_val > 0 else 0.0,
        axis=1,
    )

    df_holdings = df_live[df_live["eldeki_adet"] > 0].copy()
    df_us_crypto_radar = df_live[(df_live["eldeki_adet"] == 0) & (~df_live["ticker"].str.startswith("IST:"))].copy()
    df_bist_all = df_live[df_live["ticker"].str.startswith("IST:")].copy()

    df_elimde_al = df_holdings[
        ((df_holdings["canli_rsi_1g"] <= 43.5) | (df_holdings["canli_rsi_1h"] < 40.0))
        & (df_holdings["hedef_tutar"] > df_holdings["korunan_ana_para"])
        & (~df_holdings["karar"].str.contains("Kârda Tut|KALE DOLU"))
    ].sort_values("canli_rsi_1g")
    df_elimde_sat = df_holdings[df_holdings["canli_rsi_1g"] >= 64.0].sort_values("canli_rsi_1g", ascending=False)

    df_us_dip = df_us_crypto_radar[
        ((df_us_crypto_radar["canli_rsi_1g"] <= 43.0) | (df_us_crypto_radar["dunku_rsi_1g"] < 40.0) | (df_us_crypto_radar["canli_rsi_1h"] < 40.0))
        & (df_us_crypto_radar["hedef_tutar"] > 0)
    ].sort_values("canli_rsi_1g")
    df_us_yesil = df_us_dip[df_us_dip["degisim_pct"] > 0].copy()
    df_us_bekle = df_us_dip[df_us_dip["degisim_pct"] <= 0].copy()

    df_bist_dip = df_bist_all[
        (df_bist_all["canli_rsi_1g"] <= 43.0) | (df_bist_all["dunku_rsi_1g"] < 40.0) | (df_bist_all["canli_rsi_1h"] < 40.0)
    ].sort_values("canli_rsi_1g")
    df_bist_yesil = df_bist_dip[df_bist_dip["degisim_pct"] > 0].copy()
    df_bist_bekle = df_bist_dip[df_bist_dip["degisim_pct"] <= 0].copy()

    btc_row = df_live[df_live["ticker"] == "CURRENCY:BTCUSD"]
    btc_val_str = f"{float(btc_row['fiyat'].iloc[0]):,.0f} &#36;" if not btc_row.empty else "—"
    btc_rsi = float(btc_row["canli_rsi_1g"].iloc[0]) if not btc_row.empty else 0.0
    pl_pil = "up-pill" if tot_port_pl >= 0 else "dn-pill"

    pulse_html = f"""
    <div class="pulse-grid">
        <div class="pulse-card">
            <div class="pulse-label">💼 ELİMDEKİ PORTFÖY (24 VARLIK)</div>
            <div class="pulse-val">{tot_port_val:,.2f} &#36;</div>
            <div class="pulse-sub"><span class="{pl_pil}">{tot_port_pl:+,.2f} &#36; ({tot_port_pl_pct:+.2f}%)</span> vs Ana Para ({tot_port_q:,.0f} &#36;)</div>
        </div>
        <div class="pulse-card">
            <div class="pulse-label">🏦 NAKİT &amp; HASAT HAVUZU</div>
            <div class="pulse-val">{pool_usd:,.2f} &#36;</div>
            <div class="pulse-sub"><span class="nt-pill">{int(pool_usd // 250)} Adet 250 &#36; Kurşun Hazır</span></div>
        </div>
        <div class="pulse-card">
            <div class="pulse-label">🇺🇸 ABD &amp; KRİPTO SİNYALLERİ</div>
            <div class="pulse-val">{len(df_elimde_al)} Elimde Al &nbsp;|&nbsp; {len(df_elimde_sat)} Sat</div>
            <div class="pulse-sub"><span class="up-pill">Hedef Radar: {len(df_us_yesil)} Yeşil / {len(df_us_bekle)} Bekleyen</span></div>
        </div>
        <div class="pulse-card">
            <div class="pulse-label">🇹🇷 BIST SİNYALLERİ &amp; 🪙 BTC</div>
            <div class="pulse-val">{len(df_bist_yesil)} BIST Yeşil &nbsp;|&nbsp; {len(df_bist_bekle)} BIST Dip</div>
            <div class="pulse-sub"><span class="nt-pill">ZPX30: 187,95 ₺ (RSI 36,4)</span> &nbsp;•&nbsp; BTC: {btc_val_str} (RSI {btc_rsi:.0f})</div>
        </div>
    </div>
    """
    st.markdown(clean_html(pulse_html), unsafe_allow_html=True)

    tab_sinyal, tab_liste, tab_backtest = st.tabs([
        "📊 1. AL / SAT SİNYALLERİ (Elimdekiler • Hedef ABD/Kripto • BIST)",
        "💼 2. TÜM TABLOLAR (24 Elimdeki • 40 ABD/Kripto • 19 BIST)",
        "🏛️ 3. 20 YILLIK HAFTALIK RSI < 40 & SMA 200 SİSTEMİ",
    ])

    col_cfg_common = {
        "satir_no": st.column_config.NumberColumn("Satır", format="%d", width="small"),
        "sembol": st.column_config.TextColumn("Varlık", width="small"),
        "sektor": st.column_config.TextColumn("Sektör", width="medium"),
        "fiyat": st.column_config.NumberColumn("Canlı Fiyat", format="%.2f"),
        "degisim_pct": st.column_config.NumberColumn("Günlük (%)", format="%+.2f %%"),
        "dunku_rsi_1g": st.column_config.NumberColumn("Dünkü RSI", format="%.1f"),
        "canli_rsi_1g": st.column_config.ProgressColumn("Canlı 1G RSI", min_value=0, max_value=100, format="%.1f"),
        "canli_rsi_1h": st.column_config.NumberColumn("Haftalık 1H RSI", format="%.1f"),
        "canli_rsi_1a": st.column_config.NumberColumn("Aylık 1A RSI", format="%.1f"),
        "sma200": st.column_config.NumberColumn("SMA 200", format="%.2f"),
        "sma200_fark_pct": st.column_config.NumberColumn("SMA200 Uzaklık", format="%+.2f %%"),
        "dd52_pct": st.column_config.NumberColumn("52H Düşüş", format="%.2f %%"),
        "eldeki_adet": st.column_config.NumberColumn("Adet (L)", format="%.4f"),
        "ort_maliyet": st.column_config.NumberColumn("Ort. Maliyet (M)", format="%.2f"),
        "esik_25": st.column_config.NumberColumn("-%2,5 Eşiği (O)", format="%.2f"),
        "guncel_deger": st.column_config.NumberColumn("Güncel Değer (P)", format="%.2f"),
        "korunan_ana_para": st.column_config.NumberColumn("Ana Para (Q)", format="%.2f"),
        "hedef_tutar": st.column_config.NumberColumn("Hedef Kasa (R)", format="%.0f"),
        "kar_zarar": st.column_config.NumberColumn("Net K/Z", format="%+.2f"),
        "kar_zarar_pct": st.column_config.NumberColumn("K/Z (%)", format="%+.2f %%"),
        "hedef_doluluk_pct": st.column_config.ProgressColumn("Hedef Doluluk", min_value=0, max_value=120, format="%.1f %%"),
        "kademe_u": st.column_config.NumberColumn("Kademe", format="%.0f"),
        "karar": st.column_config.TextColumn("Otomatik Al / Sat Kararı & Tetik Fiyatı", width="large"),
    }

    cols_portfoy = [
        "satir_no", "sembol", "fiyat", "degisim_pct", "dunku_rsi_1g", "canli_rsi_1g", "canli_rsi_1h", "canli_rsi_1a",
        "sma200", "sma200_fark_pct", "eldeki_adet", "ort_maliyet", "guncel_deger",
        "korunan_ana_para", "hedef_tutar", "kar_zarar", "kar_zarar_pct",
        "hedef_doluluk_pct", "esik_25", "kademe_u", "karar"
    ]

    cols_radar = [
        "satir_no", "sembol", "kategori", "fiyat", "degisim_pct", "dunku_rsi_1g",
        "canli_rsi_1g", "canli_rsi_1h", "canli_rsi_1a", "sma200", "sma200_fark_pct",
        "dd52_pct", "hedef_tutar", "kademe_u", "karar"
    ]

    with tab_sinyal:
        view_pill = st.radio(
            "Hızlı Görünüm Seç:",
            [
                "🌐 Tümü Bir Arada (Elimdekiler + Hedef ABD/Kripto + BIST)",
                f"💼 1. Sadece Elimde Olan Varlıklar ({len(df_elimde_al)} Al/Dip | {len(df_elimde_sat)} Sat/Kâr)",
                f"🎯 2. Sadece Hedeflediğimiz ABD & Kripto ({len(df_us_yesil)} Yeşil Al | {len(df_us_bekle)} Dip Bekleyen)",
                f"🇹🇷 3. Sadece BIST (Borsa İstanbul) Sinyalleri ({len(df_bist_yesil)} Yeşil Al | {len(df_bist_bekle)} Dip Bekleyen)",
            ],
            horizontal=True,
            label_visibility="collapsed",
        )

        if view_pill.startswith("🌐") or view_pill.startswith("💼"):
            st.markdown("#### 1. BÖLÜM: 💼 ELİMDE OLAN VARLIKLAR (Mevcut Portföyümdeki Al / Sat Sinyalleri)")
            el1, el2 = st.columns(2, gap="medium")
            with el1:
                st.markdown(clean_html(f'<div class="section-banner"><span>🟢 ELİMDEKİLER — AL / EKLE &amp; DİP ADAYLARI (Boş Kotası Olanlar)</span><span>{len(df_elimde_al)} Varlık</span></div>'), unsafe_allow_html=True)
                for _, r_item in df_elimde_al.iterrows():
                    ctype = "green" if ("EKLE" in str(r_item["karar"]) or r_item["degisim_pct"] > 0) else "red"
                    st.markdown(render_signal_mini_card(r_item, ctype), unsafe_allow_html=True)
            with el2:
                st.markdown(clean_html(f'<div class="section-banner"><span>🔴 ELİMDEKİLER — SAT / KÂR HASADI BÖLGESİ (RSI &gt;= 64)</span><span>{len(df_elimde_sat)} Varlık</span></div>'), unsafe_allow_html=True)
                for _, r_item in df_elimde_sat.iterrows():
                    st.markdown(render_signal_mini_card(r_item, "amber"), unsafe_allow_html=True)

        if view_pill.startswith("🌐") or view_pill.startswith("🎯"):
            if view_pill.startswith("🌐"):
                st.divider()
            st.markdown("#### 2. BÖLÜM: 🎯 HEDEFLEDİĞİMİZ ABD, ÜLKE ETF & 7/24 KRİPTO VARLIKLAR")
            hd1, hd2 = st.columns(2, gap="medium")
            with hd1:
                st.markdown(clean_html(f'<div class="section-banner"><span>🟢 HEDEF ABD &amp; KRİPTO — YEŞİL AL SİNYALİ YANANLAR</span><span>{len(df_us_yesil)} Fırsat</span></div>'), unsafe_allow_html=True)
                if df_us_yesil.empty:
                    st.info("Şu an yeşil dönüş yakan hedef ABD/Kripto varlığı yok.")
                else:
                    for _, r_item in df_us_yesil.iterrows():
                        st.markdown(render_signal_mini_card(r_item, "green"), unsafe_allow_html=True)
            with hd2:
                st.markdown(clean_html(f'<div class="section-banner"><span>⏳ HEDEF ABD &amp; KRİPTO — DİPTE YEŞİL MUM BEKLEYENLER</span><span>{len(df_us_bekle)} Varlık</span></div>'), unsafe_allow_html=True)
                for _, r_item in df_us_bekle.iterrows():
                    st.markdown(render_signal_mini_card(r_item, "red"), unsafe_allow_html=True)

        if view_pill.startswith("🌐") or view_pill.startswith("🇹🇷"):
            if view_pill.startswith("🌐"):
                st.divider()
            st.markdown("#### 3. BÖLÜM: 🇹🇷 BIST (BORSA İSTANBUL) AL / DİP SİNYALLERİ (ZPX30 + 18 Ömürlük/Trend Radar)")
            bs1, bs2 = st.columns(2, gap="medium")
            with bs1:
                st.markdown(clean_html(f'<div class="section-banner"><span>🟢 BIST — YEŞİL DÖNÜŞ (AL / EKLE) SİNYALİ YANANLAR</span><span>{len(df_bist_yesil)} BIST Varlığı</span></div>'), unsafe_allow_html=True)
                if df_bist_yesil.empty:
                    st.info("Şu an BIST'te yeşil dönüş yakan varlık yok.")
                else:
                    for _, r_item in df_bist_yesil.iterrows():
                        st.markdown(render_signal_mini_card(r_item, "green"), unsafe_allow_html=True)
            with bs2:
                st.markdown(clean_html(f'<div class="section-banner"><span>⏳ BIST — DİPTE YEŞİL DÖNÜŞ BEKLEYENLER (RSI &lt;= 43)</span><span>{len(df_bist_bekle)} BIST Varlığı</span></div>'), unsafe_allow_html=True)
                for _, r_item in df_bist_bekle.iterrows():
                    st.markdown(render_signal_mini_card(r_item, "red"), unsafe_allow_html=True)

    with tab_liste:
        st.markdown(clean_html(f'<div class="section-banner"><span>💼 TABLO 1: ELİMDEKİ PORTFÖY VARLIKLARI ({len(df_holdings)} Aktif Kale)</span><span>Değer: {tot_port_val:,.2f} &#36; | Ana Para: {tot_port_q:,.2f} &#36;</span></div>'), unsafe_allow_html=True)
        st.dataframe(prepare_and_style_df(df_holdings.sort_values("canli_rsi_1g"), cols_portfoy), column_config=col_cfg_common, use_container_width=True, hide_index=True, height=480)

        st.markdown(clean_html(f'<div class="section-banner" style="margin-top:18px;"><span>🇹🇷 TABLO 2: BIST (BORSA İSTANBUL) ÖMÜRLÜK KALE &amp; RADAR LİSTESİ ({len(df_bist_all)} Varlık — TL Bazlı)</span><span>Dip Bölgesindekiler: {len(df_bist_dip)} Varlık</span></div>'), unsafe_allow_html=True)
        st.dataframe(prepare_and_style_df(df_bist_all.sort_values("canli_rsi_1g"), cols_radar), column_config=col_cfg_common, use_container_width=True, hide_index=True, height=460)

        st.markdown(clean_html(f'<div class="section-banner" style="margin-top:18px;"><span>🎯 TABLO 3: HEDEFLEDİĞİMİZ ABD, ÜLKE ETF &amp; 7/24 KRİPTO LİSTESİ ({len(df_us_crypto_radar)} Varlık)</span><span>Hedef Kasası Olanlar &amp; Radar</span></div>'), unsafe_allow_html=True)
        st.dataframe(prepare_and_style_df(df_us_crypto_radar.sort_values("canli_rsi_1g"), cols_radar), column_config=col_cfg_common, use_container_width=True, hide_index=True, height=460)

    with tab_backtest:
        st.markdown(clean_html('<div class="section-banner"><span>🏛️ 20 YILLIK (2006-2026) HAFTALIK RSI &lt; 40 &amp; GÜNLÜK SMA 200 ANALİZ SİSTEMİ</span><span>ABD • BIST • Kripto</span></div>'), unsafe_allow_html=True)
        bt_options = [
            "GOOGL", "CAT", "NASA", "META", "AMZN", "NVDA", "AVGO", "MSFT", "LLY", "ETN", "CLH", "GRMN", "HWM", "LMT", "QQQM", "SMH", "EWY", "EWT",
            "ZPX30.IS", "THYAO.IS", "FROTO.IS", "ASELS.IS", "TCELL.IS", "BIMAS.IS", "MGROS.IS", "KCHOL.IS", "SAHOL.IS", "TOASO.IS", "TUPRS.IS", "ASTOR.IS", "GARAN.IS", "ISCTR.IS",
            "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD"
        ]
        bt_ticker = st.selectbox("20 Yıllık Haftalık RSI Analizi Yapılacak Varlığı Seç (ABD, BIST .IS veya Kripto):", bt_options, index=0)

        @st.cache_data(ttl=1800, show_spinner="20 yıllık tarihsel günlük ve haftalık döngüler hesaplanıyor...")
        def cached_20y_backtest(tck_sym: str) -> dict:
            s_close = fetch_direct_series(tck_sym, "10y")
            if len(s_close) < 200 and yf is not None:
                hist_20y = yf.download(tck_sym, period="20y", interval="1d", progress=False, threads=False)
                s_close = extract_clean_close(hist_20y)
            return run_20yr_backtest(s_close)

        bt_res = cached_20y_backtest(bt_ticker)
        summ = bt_res.get("summary", {})

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("20Y Haftalık RSI<40 Girişi", f"{summ.get('toplam_haftalik_giris', 0)} Kez", f"Toplam {summ.get('toplam_hafta_rsi40_alti', 0)} Hafta")
        m2.metric("1H RSI<40 Sonrası 1Y Ort. Getiri", f"+%{summ.get('ort_12ay_getiri_haftalik', 0):.1f}", f"Güncel 1H RSI: {summ.get('guncel_haftalik_rsi', 0):.1f}")
        m3.metric("20Y Günlük SMA200 Kırılımı", f"{summ.get('toplam_sma200_kiris', 0)} Döngü", f"Toplam {summ.get('toplam_gun_sma200_alti', 0)} İş Günü")
        m4.metric("SMA200 Altı Sonrası 1Y Ort. Getiri", f"+%{summ.get('ort_12ay_getiri_sma200', 0):.1f}", f"Güncel SMA200: {summ.get('guncel_sma200', 0):.2f}")

        st.markdown(f"#### 1) `{bt_ticker}` — Son 20 Yılda Haftalık (1H) Wilder RSI < 40 Altına Girdiği Tüm Döngüler")
        st.dataframe(bt_res["weekly_cycles"], use_container_width=True, hide_index=True)

        st.markdown(f"#### 2) `{bt_ticker}` — Son 20 Yılda Günlük (1G) 200 Günlük Ortalama (SMA 200) Altına İndiği Döngüler")
        st.dataframe(bt_res["sma200_cycles"], use_container_width=True, hide_index=True)


if __name__ == "__main__":
    if st is not None and os.environ.get("STREAMLIT_RUN_CONTEXT") != "TEST":
        main()
