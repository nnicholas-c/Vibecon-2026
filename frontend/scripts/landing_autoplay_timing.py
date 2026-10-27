"""Landing autoplay timing: page ready (loader gone) to the last autoplay scroll move, with software WebGL."""
import asyncio
import time

from playwright.async_api import async_playwright

URL = open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split()[0] + "/"


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        page = await b.new_page(viewport={"width": 640, "height": 360})
        await page.goto(URL, wait_until="domcontentloaded", timeout=90000)
        await page.wait_for_selector('[data-testid="landing-masthead-demo-button"]', state="attached", timeout=90000)
        print("plain mode:", await page.evaluate("Boolean(document.querySelector('.lp-plain'))"),
              "| webgl2:", await page.evaluate("Boolean(document.createElement('canvas').getContext('webgl2'))"))
        await page.wait_for_function("() => !document.querySelector('.lp-loader') || document.querySelector('.lp-loader').dataset.state === 'gone'"
                                     " || getComputedStyle(document.querySelector('.lp-loader')).opacity === '0'", timeout=90000, polling=100)
        await page.evaluate("""() => { window.__t = []; const t0 = performance.now(); let last = -1;
          setInterval(() => { const y = window.scrollY; if (y !== last) { window.__t.push([Math.round(performance.now() - t0), y]); last = y; } }, 100); }""")
        t_ready = time.time()
        start = last_move = None
        last, stable = None, 0
        while time.time() - t_ready < 90:
            await asyncio.sleep(0.2)
            y = await page.evaluate("window.scrollY")
            if start is None and y > 2:
                start = time.time() - t_ready
            if start is not None:
                if y != last:
                    last_move, stable = time.time() - t_ready, 0
                else:
                    stable += 1
                if stable >= 25 and y > 1000:
                    break
            last = y
        tr = await page.evaluate("window.__t")
        moves = [t for t in tr if t[1] > 2]
        print("in-page: first move", moves[0][0] if moves else None, "ms, last move", moves[-1][0] if moves else None, "ms, samples", len(tr))
        print(f"autoplay started {start}s after ready; autoplay end (last scroll) {last_move}s after ready; final scrollY {last}")
        await b.close()

asyncio.run(main())
