import asyncio
import os
import re
import subprocess
import sys
import tempfile

SITE_DIR = os.path.join(os.path.dirname(__file__), "site")


def find_mermaid_blocks(html: str):
    pattern = re.compile(
        r'<pre\s+class\s*=\s*["\']mermaid["\']\s*><code>\s*(.*?)\s*</code></pre>',
        re.DOTALL,
    )
    for match in pattern.finditer(html):
        yield match


def run_mkdocs_build():
    config = os.path.join(os.path.dirname(__file__), "mkdocs.yml")
    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--config-file", config],
        capture_output=True, text=True,
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    result.check_returncode()


async def render_one(mermaid_code: str) -> str:
    from playwright.async_api import async_playwright

    mermaid_code = mermaid_code.strip()
    html = f"""<!DOCTYPE html>
<html><head>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js">
</script>
<script>
mermaid.initialize({{startOnLoad:true}});
</script>
<style>body{{margin:0;}}svg{{max-width:100%;height:auto;}}</style>
</head>
<body><div class="mermaid">{mermaid_code}</div></body></html>"""

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8")
    tmp.write(html)
    tmp.close()

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            ctx = await browser.new_context(
                bypass_csp=True,
                ignore_https_errors=True,
            )
            page = await ctx.new_page()
            await page.goto(f"file://{tmp.name}", wait_until="networkidle")
            await page.wait_for_selector(".mermaid svg", timeout=30000)
            svg = await page.eval_on_selector(".mermaid", "el => el.innerHTML")
            await browser.close()
        return svg
    except Exception:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            ctx = await browser.new_context(
                bypass_csp=True,
                ignore_https_errors=True,
            )
            page = await ctx.new_page()
            await page.goto(f"file://{tmp.name}", wait_until="networkidle")
            await page.wait_for_timeout(5000)
            svg = await page.evaluate("""
                async () => {
                    const el = document.querySelector('.mermaid');
                    const {svg} = await mermaid.render('renderTarget', el.textContent);
                    return svg;
                }
            """)
            await browser.close()
        return svg
    finally:
        os.unlink(tmp.name)


def replace_svg(html: str, old_block: str, svg: str) -> str:
    return html.replace(old_block, svg)


async def process_file(filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    blocks = list(find_mermaid_blocks(html))
    if not blocks:
        return

    print(f"  {os.path.relpath(filepath, SITE_DIR)} — {len(blocks)} diagram(s)")

    for match in blocks:
        code = match.group(1).strip()
        try:
            svg = await render_one(code)
            html = replace_svg(html, match.group(0), svg)
        except Exception as e:
            print(f"    ERROR: {e}", file=sys.stderr)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)


async def main():
    run_mkdocs_build()

    tasks = []
    for root, _dirs, files in os.walk(SITE_DIR):
        for f in files:
            if f.endswith(".html"):
                tasks.append(process_file(os.path.join(root, f)))

    await asyncio.gather(*tasks)
    print("Done")


if __name__ == "__main__":
    asyncio.run(main())
