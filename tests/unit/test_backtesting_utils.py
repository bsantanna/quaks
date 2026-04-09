import pandas as pd
import numpy as np
import pytest
from app.utils.backtesting_utils import (
    get_sma, get_ema, get_rsi, get_macd, get_stoch, get_adx, get_cci, get_aroon, get_bbands, get_ad, get_obv
)

@pytest.fixture
def sample_df():
    data = {
        'val_close': [100, 102, 101, 105, 107, 108, 110, 109, 111, 115, 114, 116, 118, 120, 119, 121, 125, 124, 126, 130],
        'val_high': [101, 103, 102, 106, 108, 109, 111, 110, 112, 116, 115, 117, 119, 121, 120, 122, 126, 125, 127, 131],
        'val_low': [99, 101, 100, 104, 106, 107, 109, 108, 110, 114, 113, 115, 117, 119, 118, 120, 124, 123, 125, 129],
        'val_volume': [1000, 1100, 1050, 1200, 1300, 1250, 1400, 1350, 1500, 1600, 1550, 1700, 1800, 1900, 1850, 2000, 2100, 2050, 2200, 2300]
    }
    return pd.DataFrame(data)

def test_get_sma(sample_df):
    df_res, df_cross = get_sma(sample_df, short_window=2, long_window=5)
    assert 'sma_short' in df_res.columns
    assert 'sma_long' in df_res.columns
    assert 'position' in df_res.columns
    assert not df_res.empty

def test_get_ema(sample_df):
    df_res, df_cross = get_ema(sample_df, short_window=2, long_window=5)
    assert 'ema_short' in df_res.columns
    assert 'ema_long' in df_res.columns
    assert not df_res.empty

def test_get_rsi(sample_df):
    df_res, df_cross = get_rsi(sample_df, period=5)
    assert 'rsi' in df_res.columns
    assert not df_res.empty

def test_get_macd(sample_df):
    df_res, df_cross = get_macd(sample_df, short_period=2, long_period=5, signal_period=3)
    assert 'macd' in df_res.columns
    assert 'signal' in df_res.columns
    assert not df_res.empty

def test_get_stoch(sample_df):
    df_res, df_cross = get_stoch(sample_df, lookback=5, smooth_k=3, smooth_d=3)
    assert 'slow_k' in df_res.columns
    assert 'slow_d' in df_res.columns
    assert not df_res.empty

def test_get_adx(sample_df):
    df_res, df_cross = get_adx(sample_df, period=5)
    assert 'adx' in df_res.columns
    assert not df_res.empty

def test_get_cci(sample_df):
    df_res, df_cross = get_cci(sample_df, period=5)
    assert 'cci' in df_res.columns
    assert not df_res.empty

def test_get_aroon(sample_df):
    df_res, df_cross = get_aroon(sample_df, period=5)
    assert 'aroon_up' in df_res.columns
    assert 'aroon_down' in df_res.columns
    assert not df_res.empty

def test_get_bbands(sample_df):
    df_res = get_bbands(sample_df, period=5)
    assert 'upper_band' in df_res.columns
    assert 'lower_band' in df_res.columns
    assert not df_res.empty

def test_get_ad(sample_df):
    df_res, df_cross = get_ad(sample_df)
    assert 'ad_line' in df_res.columns
    assert not df_res.empty

def test_get_obv(sample_df):
    df_res, df_cross = get_obv(sample_df)
    assert 'obv' in df_res.columns
    assert not df_res.empty
