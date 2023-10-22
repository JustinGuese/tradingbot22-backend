import requests

BACKENDURL = "http://localhost:8000"
testbotExists = False


# check if bot "testbot" exists
def test_if_bot_testbot_exists():
    global testbotExists
    r = requests.get(BACKENDURL + "/bots/testbot")
    if r.status_code == 200:
        testbotExists = True
    elif r.status_code == 404:
        testbotExists = False
    assert r.status_code in [200, 404]


def test_delete_bot_if_exists():
    global testbotExists
    r = requests.delete(BACKENDURL + "/bots/testbot")
    if testbotExists:
        assert r.status_code == 200
    else:
        assert r.status_code == 404


def test_if_really_deleted():
    global testbotExists
    if testbotExists:
        r = requests.get(BACKENDURL + "/bots/testbot")
        assert r.status_code == 404


def test_create_bot():
    json = {
        "name": "Testbot",
        "description": "no mudda yet",
    }
    r = requests.put(BACKENDURL + "/bots", json=json)
    assert r.status_code == 200, r.text
    r = r.json()
    assert r["name"] == "Testbot"
    assert r["description"] == "no mudda yet"
    assert r["portfolio"] == {"USD": 10000}
    assert r["live"] == False
    assert r["portfolio_worth"] == 10000
    assert r["start_money"] == 10000


def test_update_bot():
    json = {
        "name": "Testbot",
        "description": "no ficka yet",
        "portfolio": {"USD": 984.21, "BTC": 3.21},
    }
    r = requests.put(BACKENDURL + "/bots", json=json)
    assert r.status_code == 200, r.text
    r = r.json()
    assert r["name"] == "Testbot"
    assert r["description"] == "no ficka yet"
    assert r["portfolio"] == {"USD": 984.21, "BTC": 3.21}
    assert r["live"] == False
    assert r["portfolio_worth"] == 10000
    assert r["start_money"] == 10000


def test_get_bot():
    r = requests.get(BACKENDURL + "/bots/Testbot")
    assert r.status_code == 200, r.text
    r = r.json()
    assert r["name"] == "Testbot"
    assert r["description"] == "no ficka yet"
    assert r["portfolio"] == {"USD": 984.21, "BTC": 3.21}
    assert r["live"] == False
    assert r["portfolio_worth"] == 10000
    assert r["start_money"] == 10000


def test_delete_bot():
    r = requests.delete(BACKENDURL + "/bots/Testbot")
    assert r.status_code == 200, r.text


def test_delete_success_bot():
    r = requests.delete(BACKENDURL + "/bots/Testbot")
    assert r.status_code == 404, r.text
    r = requests.get(BACKENDURL + "/bots/Testbot")
    assert r.status_code == 404, r.text


def test_create_bot_again():
    r = requests.put(BACKENDURL + "/bots", json={"name": "Testbot"})
    assert r.status_code == 200, r.text
    r = r.json()
    assert r["name"] == "Testbot"
    assert r["description"] == "no description yet"
    assert r["portfolio"] == {"USD": 10000}
    assert r["live"] == False
    assert r["portfolio_worth"] == 10000
    assert r["start_money"] == 10000


btcprice = None


def test_get_price():
    global btcprice
    r = requests.get(BACKENDURL + "/pricing/BTC")
    assert r.status_code == 200, r.text
    btcprice = float(r.json())
    assert btcprice > 0


def test_buy():
    global btcprice
    shouldAmount = 5000 / btcprice
    commission = shouldAmount * 0.0015
    shouldAmount -= commission
    r = requests.post(
        BACKENDURL + "/buysell/buy/Testbot/BTC/5000"
    )  # should auto amountInUSD = True
    assert r.status_code == 200, r.text
    # check bot route
    r = requests.get(BACKENDURL + "/bots/Testbot")
    assert r.status_code == 200, r.text
    r = r.json()
    assert r["portfolio"]["BTC"] == shouldAmount, r
    assert r["portfolio"]["USD"] == 5000, r

    # check portfolio route
    r = requests.get(BACKENDURL + "/portfolio/Testbot")
    assert r.status_code == 200, r.text
    r = r.json()
    assert r.get("BTC", 0) == shouldAmount, r
    assert r["USD"] == 5000, r


def test_if_buy_more_denied():
    r = requests.post(
        BACKENDURL + "/buysell/buy/Testbot/MSFT/6000"
    )  # should auto amountInUSD = True
    assert r.status_code == 400, r.text
    r = requests.get(BACKENDURL + "/bots/Testbot")
    assert r.status_code == 200, r.text
    r = r.json()
    assert r["portfolio"]["USD"] == 5000, r
    assert r["portfolio"].get("MSFT", 0) == 0, r
    assert r["portfolio"]["BTC"] > 0, r


def test_if_shorting_denied_for_now():
    r = requests.post(
        BACKENDURL + "/buysell/buy/Testbot/BTC/-2130"
    )  # should auto amountInUSD = True
    assert r.status_code == 400, r.text


def test_if_0_means_buy_all():
    # get crnt portfolio
    r = requests.get(BACKENDURL + "/bots/Testbot")
    assert r.status_code == 200, r.text
    r = r.json()
    BTCBefore = r["portfolio"]["BTC"]
    r = requests.post(
        BACKENDURL + "/buysell/buy/Testbot/BTC/0"
    )  # should auto amountInUSD = True
    assert r.status_code == 200, r.text
    r = requests.get(BACKENDURL + "/bots/Testbot")
    assert r.status_code == 200, r.text
    r = r.json()
    assert r["portfolio"]["BTC"] > BTCBefore, r
    assert r["portfolio"]["USD"] == 0, r


def test_if_0_means_sell_all():
    r = requests.post(
        BACKENDURL + "/buysell/sell/Testbot/BTC/0"
    )  # should auto amountInUSD = True
    assert r.status_code == 200, r.text
    r = requests.get(BACKENDURL + "/bots/Testbot")
    assert r.status_code == 200, r.text
    r = r.json()
    assert r["portfolio"]["BTC"] == 0, r
    assert r["portfolio"]["USD"] > 9970, r  # some fees and commission...


msftHeld = 0


def test_buy_specific_amount():
    global msftHeld
    # get price of MSFT
    r = requests.get(BACKENDURL + "/pricing/MSFT")
    assert r.status_code == 200, r.text
    msftPrice = float(r.json())
    amountToBuy = 5000 / msftPrice
    r = requests.post(
        BACKENDURL + "/buysell/buy/Testbot/MSFT/" + str(amountToBuy),
        params={"amountInUSD": False},
    )
    assert r.status_code == 200, r.text
    r = requests.get(BACKENDURL + "/bots/Testbot")
    assert r.status_code == 200, r.text
    r = r.json()
    assert abs(r["portfolio"]["MSFT"] - amountToBuy) < 0.1, r["portfolio"]
    msftHeld = r["portfolio"]["MSFT"]
    assert r["portfolio"]["USD"] > 4000, r["portfolio"]


def test_sell_specific_amount():
    global msftHeld
    # sell msftHeld of MSFT
    r = requests.post(
        BACKENDURL + "/buysell/sell/Testbot/MSFT/" + str(msftHeld),
        params={"amountInUSD": False},
    )
    assert r.status_code == 200, r.text
    r = requests.get(BACKENDURL + "/bots/Testbot")
    assert r.status_code == 200, r.text
    r = r.json()
    assert r["portfolio"]["MSFT"] == 0, r["portfolio"]
    assert r["portfolio"]["USD"] > 9000, r["portfolio"]


## that looks good!
def test_portfolio_worth_route():
    r = requests.get(BACKENDURL + "/portfolio/worth/Testbot")
    assert r.status_code == 200, r.text
    r = float(r.json())
    assert r > 9000, r


def test_delete_bot():
    r = requests.delete(BACKENDURL + "/bots/Testbot")
    assert r.status_code == 200, r.text
    r = requests.get(BACKENDURL + "/bots/Testbot")
    assert r.status_code == 404, r.text
