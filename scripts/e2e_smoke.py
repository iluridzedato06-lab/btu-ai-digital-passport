"""End-to-end smoke test against a running stack (docker compose up).

    pip install playwright && python -m playwright install chromium   (or use an installed Chrome)
    python scripts/e2e_smoke.py [--base http://localhost:3000] [--mailpit http://localhost:8025] [--shots DIR]

Covers: public verification, client-side PDF hash match, tamper detection, student magic-link
sign-in + download, staff sign-in, sheet change -> new version, superseded status, revocation.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
STUDENT = "demo.nino.beridze@btu.edu.ge"
STUDENT2_NUMBER = "DEMO-0002"
ADMIN = "passport.admin@btu.edu.ge"
results: list[tuple[str, bool, str]] = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (f"  ({detail})" if detail else ""), flush=True)


def get_json(url):
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.loads(r.read())


def latest_link(mailpit, email, after_ts):
    for _ in range(30):
        msgs = get_json(f"{mailpit}/api/v1/messages?limit=20").get("messages", [])
        for m in msgs:
            if any(t["Address"] == email for t in m["To"]) and "sign-in" in m["Subject"].lower() or "შესვლის" in m["Subject"]:
                if not any(t["Address"] == email for t in m["To"]):
                    continue
                full = get_json(f"{mailpit}/api/v1/message/{m['ID']}")
                found = re.search(r"https?://\S+/auth/callback#token=[\w\-]+", full["Text"])
                if found and m["Created"] >= after_ts:
                    return found.group(0)
        time.sleep(1)
    return None


def compose(*args):
    return subprocess.run(["docker", "compose", *args], cwd=ROOT, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:3000")
    ap.add_argument("--mailpit", default="http://localhost:8025")
    ap.add_argument("--shots", default="")
    ap.add_argument("--channel", default="chrome")
    a = ap.parse_args()
    base = a.base.rstrip("/")
    shots = Path(a.shots) if a.shots else None
    if shots:
        shots.mkdir(parents=True, exist_ok=True)

    def shot(page, name):
        if shots:
            page.screenshot(path=str(shots / f"{name}.png"), full_page=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel=a.channel or None)
        ctx = browser.new_context(viewport={"width": 1366, "height": 900}, accept_downloads=True)
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        # ---- health & issuer identity
        h = page.request.get(f"{base}/api/health").json()
        check("API healthy and chain reachable", h["status"] == "ok" and h["chain_reachable"], h.get("contract") or "")
        wk = page.request.get(f"{base}/.well-known/btu-issuer.json").json()
        check("well-known issuer record published", wk["issuer"] == "Business and Technology University" and wk["issuer_addresses"])

        # ---- student sign-in via magic link
        page.goto(f"{base}/en/login")
        t0 = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() - 5))
        page.fill("#email", STUDENT)
        page.click("button[type=submit]")
        page.wait_for_selector("text=Check your inbox")
        link = latest_link(a.mailpit, STUDENT, t0)
        check("magic link delivered to BTU email", bool(link))
        page.goto(link)
        page.wait_for_url(re.compile(r"/dashboard"), timeout=20000)
        page.wait_for_selector("text=Passport versions")
        check("student dashboard shows passport", page.locator("text=BTU-AI-").first.is_visible())
        shot(page, "dashboard")
        reused = page.request.post(f"{base}/api/auth/magic-link/consume",
                                   data={"token": link.split("token=")[1]},
                                   headers={"X-CSRFToken": next((c["value"] for c in ctx.cookies() if c["name"] == "csrftoken"), "")})
        check("magic link is single-use", reused.status == 400)

        me = page.request.get(f"{base}/api/me").json()
        v = me["passport"]["versions"][0]
        dl = page.request.get(f"{base}/api/me/passport/versions/{v['version_number']}/download")
        pdf = dl.body()
        check("student can download own PDF", dl.status == 200 and pdf[:4] == b"%PDF")
        check("downloaded PDF hash equals anchored hash", hashlib.sha256(pdf).hexdigest() == v["pdf_sha256"])
        pdf_path = ROOT / ".scratch" / "e2e_passport.pdf"
        pdf_path.parent.mkdir(exist_ok=True)
        pdf_path.write_bytes(pdf)
        tampered = bytearray(pdf)
        idx = pdf.find(b"BERIDZE") if b"BERIDZE" in pdf else len(pdf) // 2
        tampered[idx + 1] ^= 0x01
        tampered_path = ROOT / ".scratch" / "e2e_passport_tampered.pdf"
        tampered_path.write_bytes(bytes(tampered))

        # ---- public verification (separate, signed-out context)
        anon = browser.new_context(viewport={"width": 1366, "height": 900})
        ap_ = anon.new_page()
        ap_.goto(f"{base}/en/verify/{v['verification_code']}")
        ap_.wait_for_selector("text=Authentic. This is the latest version.", timeout=20000)
        check("public verification without login: valid_latest", True)
        ap_.set_input_files("input[type=file]", str(pdf_path))
        ap_.wait_for_selector("text=Exact match", timeout=10000)
        check("browser-side PDF check: exact match", True)
        shot(ap_, "verify_match")
        ap_.set_input_files("input[type=file]", str(tampered_path))
        ap_.wait_for_selector("text=No match", timeout=10000)
        check("tampered PDF (1 byte) fails verification", True)
        shot(ap_, "verify_tampered")
        bad = ap_.request.get(f"{base}/api/public/verify/by-hash/{hashlib.sha256(bytes(tampered)).hexdigest()}").json()
        check("tampered hash unknown on chain/registry", bad["status"] == "not_found")
        nf = ap_.request.get(f"{base}/api/public/verify/ZZZZ-ZZZZ-ZZZZ").json()
        check("unknown code -> not_found", nf["status"] == "not_found")
        forbidden = ap_.request.get(f"{base}/api/me/passport/versions/1/download")
        check("download requires sign-in", forbidden.status in (401, 403))
        adm = ap_.request.get(f"{base}/api/admin/overview")
        check("admin API refuses anonymous", adm.status in (401, 403))
        stud_admin = page.request.get(f"{base}/api/admin/overview")
        check("admin API refuses students", stud_admin.status == 403)

        # ---- staff sign-in, live sheet update -> new version
        staff_ctx = browser.new_context(viewport={"width": 1366, "height": 900})
        sp = staff_ctx.new_page()
        sp.goto(f"{base}/ka/login")
        t1 = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() - 5))
        sp.fill("#email", ADMIN)
        sp.click("button[type=submit]")
        sp.wait_for_timeout(1500)
        link2 = latest_link(a.mailpit, ADMIN, t1)
        check("admin magic link delivered", bool(link2))
        sp.goto(link2)
        sp.wait_for_url(re.compile(r"/admin"), timeout=20000)
        sp.wait_for_timeout(1500)
        shot(sp, "admin_overview")

        students = sp.request.get(f"{base}/api/admin/students?q={STUDENT2_NUMBER}").json()
        sid = students[0]["id"]
        before = sp.request.get(f"{base}/api/admin/students/{sid}").json()
        old_v = before["versions"][-1]
        r = compose("exec", "-T", "web", "python", "manage.py", "demo_confirm", "AW-DEMO-0013")
        check("admin confirms a new skill in the sheet", r.returncode == 0, r.stdout.strip() or r.stderr.strip())
        csrf = next((c["value"] for c in staff_ctx.cookies() if c["name"] == "csrftoken"), "")
        trig = sp.request.post(f"{base}/api/admin/sync-runs", headers={"X-CSRFToken": csrf})
        check("staff can trigger a sync", trig.status == 202)
        new = None
        for _ in range(60):
            d = sp.request.get(f"{base}/api/admin/students/{sid}").json()
            anchored = [x for x in d["versions"] if x["status"] == "anchored"]
            if len(anchored) > len([x for x in before["versions"] if x["status"] == "anchored"]):
                new = anchored[0]
                break
            time.sleep(2)
        check("new skill produces a new anchored version, same passport ID",
              bool(new) and d["passport_id"] == before["passport_id"],
              f"{d['passport_id']} v{new['version_number'] if new else '?'}")
        if new:
            check("new version keeps earlier stamps", new["award_count"] == old_v["award_count"] + 1)
            old = sp.request.get(f"{base}/api/public/verify/{old_v['verification_code']}").json()
            check("older version reported as superseded", old["status"] == "valid_superseded")
            sp.goto(f"{base}/ka/verify/{old_v['verification_code']}")
            sp.wait_for_timeout(2500)
            shot(sp, "verify_superseded_ka")

            # ---- revoke the newest version
            rv = sp.request.post(f"{base}/api/admin/versions/{new['id']}/revoke",
                                 data={"reason": "Demonstration of revocation"}, headers={"X-CSRFToken": csrf})
            check("admin can revoke a version on chain", rv.status == 200, rv.text()[:120])
            rs = sp.request.get(f"{base}/api/public/verify/{new['verification_code']}").json()
            check("revoked version fails verification", rs["status"] == "revoked")
            sp.goto(f"{base}/admin/sync")
            shot(sp, "admin_sync")

        check("no uncaught page errors", not errors, "; ".join(errors[:3]))
        browser.close()

    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
