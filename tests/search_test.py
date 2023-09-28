from duckduckgo_search import DDGS

with DDGS(proxies="socks5://127.0.0.1:13659", timeout=20) as ddgs:
    for r in ddgs.text("马克龙、冯德莱恩访华"):
        print(r)
