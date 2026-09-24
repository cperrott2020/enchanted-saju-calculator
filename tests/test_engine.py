from app.engine import _jdn,_ten_god,_growth,calculate_day,calculate_chart

def test_gapja_anchor():
    assert _jdn(1949,10,1)==2433191
    assert calculate_day("1949-10-01")["stem"]["hanja"]=="甲"
    assert calculate_day("1949-10-01")["branch"]["hanja"]=="子"

def test_2000_day():
    d=calculate_day("2000-01-01")
    assert d["stem"]["hanja"]=="戊" and d["branch"]["hanja"]=="午"

def test_ten_gods():
    assert _ten_god(0,2)["ko"]=="식신"
    assert _ten_god(0,7)["ko"]=="정관"

def test_growth():
    assert _growth(0,11)["ko"]=="장생"

def test_chart_shape():
    r=calculate_chart({"name":"Test","sex":"female","birth_date":"2000-01-01","birth_time":"12:00","time_status":"exact","place":"Seoul","latitude":37.5665,"longitude":126.978,"timezone":"Asia/Seoul","use_true_solar_time":True,"day_boundary":"midnight","luck_direction":"auto"})
    assert set(r["pillars"])=={"year","month","day","hour"}
    assert r["certified_forceteller_match"] is False
