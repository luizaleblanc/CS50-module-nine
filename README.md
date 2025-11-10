# CS50 2024 - Problem Set 9: C$50 Finance

This repository contains my solution for Problem Set 9 (C$50 Finance) from Harvard's CS50x 2024 course.

This project is a full-stack web application built using Python and the Flask framework. It simulates a stock trading platform where users can register, log in, look up stock prices, and buy or sell shares.

---

## ⚠️ Important Prerequisite Notice

This is a **project solution** and not a standalone application. It is built upon and dependent on the specific distribution code, libraries, and database files provided by the CS50x course.

**To run or test this project, you must:**
1.  Have access to the original Pset 9 `finance.zip` distribution code.
2.  Install all required Python dependencies from the `requirements.txt` file (e.g., `pip install -r requirements.txt`).
3.  Have the original `finance.db` SQLite database file.
4.  Set up the `API_KEY` environment variable. This solution is configured to use the **Alpha Vantage** API, as the IEX API was inaccessible.

---

## 🚀 Key Features Implemented

* **Full User Authentication:** Users can register for an account, log in, and log out. All passwords are securely stored using hashes.
* **External API Integration:** Connects to the Alpha Vantage API via a custom `lookup` function in `helpers.py` to fetch real-time stock prices.
* **Database Management:** Uses a SQLite database (`finance.db`) to manage user data, cash balances, and a full, persistent history of all transactions.
* **CRUD Operations:**
    * **Quote:** Users can look up the price of any stock.
    * **Buy:** Users can purchase shares of a stock, which updates their cash balance and portfolio.
    * **Sell:** Users can sell shares from their portfolio, updating their cash balance.
    * **History:** A complete log of all user transactions (buys and sells) is displayed.
* **Dynamic Web Pages:** Uses **Jinja** templating to dynamically render HTML pages with user-specific data, such as their current portfolio and cash balance on the `index` page.

---

## 🛠️ Technologies Used
* **Backend:** Python, Flask
* **Database:** SQL (SQLite)
* **Frontend:** HTML5, CSS3, JavaScript
* **Frameworks & Libraries:** Bootstrap
* **Templating:** Jinja
* **APIs:** REST (Alpha Vantage)
```
