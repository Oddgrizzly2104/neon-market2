from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.parse import unquote
import json
import time

PORT = 8000

# Cache stock prices for 30 seconds
cache = {}


def get_stock(symbol):
    symbol = symbol.upper()

    # Use cached price if available
    if symbol in cache:
        saved_time, saved_data = cache[symbol]

        if time.time() - saved_time < 30:
            return saved_data

    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + symbol
        + "?interval=1d&range=5d"
    )

    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urlopen(request, timeout=15) as response:
        data = json.loads(
            response.read().decode("utf-8")
        )

    if not data.get("chart"):
        raise Exception("No chart data")

    if not data["chart"].get("result"):
        error = data["chart"].get("error")

        raise Exception(
            str(error) if error else "No result"
        )

    result = data["chart"]["result"][0]
    meta = result.get("meta", {})

    price = (
        meta.get("regularMarketPrice")
        or meta.get("postMarketPrice")
        or meta.get("preMarketPrice")
    )

    previous = (
        meta.get("previousClose")
        or meta.get("chartPreviousClose")
    )

    if price is None:
        raise Exception("No current price")

    if previous is None:
        previous = price

    change = price - previous

    if previous != 0:
        change_percent = (change / previous) * 100
    else:
        change_percent = 0

    result_data = {
        "symbol": symbol,
        "price": price,
        "previous": previous,
        "change": change,
        "changePercent": change_percent
    }

    cache[symbol] = (
        time.time(),
        result_data
    )

    return result_data


class Handler(SimpleHTTPRequestHandler):

    def do_GET(self):

        # Stock API
        if self.path.startswith("/api/stock/"):

            symbol = unquote(
                self.path[len("/api/stock/"):]
            )

            symbol = symbol.split("?")[0]

            try:

                data = get_stock(symbol)

                self.send_response(200)

                self.send_header(
                    "Content-Type",
                    "application/json"
                )

                self.send_header(
                    "Access-Control-Allow-Origin",
                    "*"
                )

                self.end_headers()

                self.wfile.write(
                    json.dumps(data).encode()
                )

            except Exception as e:

                self.send_response(500)

                self.send_header(
                    "Content-Type",
                    "application/json"
                )

                self.send_header(
                    "Access-Control-Allow-Origin",
                    "*"
                )

                self.end_headers()

                self.wfile.write(
                    json.dumps({
                        "symbol": symbol,
                        "error": str(e)
                    }).encode()
                )

            return

        # Normal website files
        super().do_GET()


# IMPORTANT:
# 0.0.0.0 allows other devices on your network
# to connect to this computer.
server = ThreadingHTTPServer(
    ("0.0.0.0", PORT),
    Handler
)

print()
print("==============================")
print("        NEON MARKET")
print("==============================")
print()
print("Your computer:")
print("http://localhost:8000/coins.html")
print()
print("Other devices on your Wi-Fi:")
print("Use your PC's IPv4 address")
print()
print("Stock API:")
print("http://localhost:8000/api/stock/AAPL")
print()
print("Press Ctrl+C to stop.")
print()

server.serve_forever()
