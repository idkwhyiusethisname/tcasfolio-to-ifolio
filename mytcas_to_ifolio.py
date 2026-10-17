import base64
import json
import mimetypes
import os
import re
import sys
from datetime import datetime, timedelta, timezone

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(HERE, "copied_to_ifolio.json")
COOKIES_FILE = os.path.join(HERE, "cookies.json")

DEFAULT_DATE = "2026-01-01"
TH = timezone(timedelta(hours=7))

TCAS = "https://tcas65.as.r.appspot.com"
IFOLIO = "https://ifolio.kmitl.ac.th"
FN_PORTFOLIOS = "f751e299279b93741f40f30c6ed4269fb2e2884de4c161f849b33fde4bd18a38"
FN_COMPETITION = "8ae75f5098ca4ce3576773f77771466778f38d4ccb990f1744918e0b54e099c8"
FN_ACTIVITY = "25a85b2dafd5e7cffc5893c6c3c11ae2f5c204b03fcd479b77f2d043a6b438ed"
WHITE_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII="
)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def decode(node, refs=None):
    refs = {} if refs is None else refs
    t = node.get("t")
    if t in (0, 1):
        return node["s"]
    if t == 2:
        return {0: None, 1: None, 2: True, 3: False}.get(node["s"])
    if t == 4:
        return refs.get(node["i"])
    if t == 5:
        refs[node.get("i")] = node["s"]
        return node["s"]
    if t == 9:
        out = []
        if node.get("i") is not None:
            refs[node["i"]] = out
        out.extend(decode(n, refs) for n in node.get("a", []))
        return out
    if t == 10:
        out = {}
        if node.get("i") is not None:
            refs[node["i"]] = out
        for k, v in zip(node["p"]["k"], node["p"]["v"]):
            out[k] = decode(v, refs)
        return out
    return None


def parse(resp):
    body = resp.json()
    return decode(body["t"] if isinstance(body.get("t"), dict) else body)


def find_portfolio(obj, name, depth=0):
    if depth > 9 or not isinstance(obj, (dict, list)):
        return None
    if isinstance(obj, dict):
        if obj.get("name") == name and isinstance(obj.get("id"), str) and "isCurrentlySelected" in obj:
            return obj
        obj = obj.values()
    for v in obj:
        found = find_portfolio(v, name, depth + 1)
        if found:
            return found
    return None


def start_date(title):
    m = re.search(r"(?<!\d)(20\d{2}|25\d{2})(?!\d)", title)
    day = DEFAULT_DATE
    if m:
        year = int(m.group(1))
        day = f"{year - 543 if year > 2400 else year}-01-01"
    d = datetime.fromisoformat(day).replace(tzinfo=TH)
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def build_data(item, kind):
    title = item["title"].strip()
    data = {
        "organizationType": "OTHERS",
        "organizationName": (item.get("organizer") or "").strip() or "-",
        "name": title,
        "startDate": {"$$TSS_DATE$$": start_date(title)},
        "description": (item.get("description") or "").strip(),
    }
    if kind == "competition":
        result = (item.get("result") or "").strip()
        data["competitionType"] = "INTERNATIONAL" if "นานาชาติ" in (item.get("level") or "") else "NATIONAL"
        data["otherTypeName"] = ""
        data["result"] = "OTHERS" if result else "PARTICIPATION"
        data["otherResultName"] = result
    return data


def download(url):
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    name = url.split("?")[0].rsplit("/", 1)[-1] or "image.jpg"
    mime = r.headers.get("content-type") or mimetypes.guess_type(name)[0] or "image/jpeg"
    return name, r.content, mime


def create(session, fn, portfolio_id, data, image):
    form = {
        "studentPortfolioId": (None, json.dumps(portfolio_id)),
        "data": (None, json.dumps(data, ensure_ascii=False)),
        "selectedImage": image,
    }
    r = session.post(f"{IFOLIO}/_serverFn/{fn}", files=form, headers={"x-tsr-serverfn": "true"}, timeout=120)
    if r.status_code != 200:
        return False, f"HTTP {r.status_code} {r.text[:200]!r}"
    res = parse(r)
    return bool(res and res.get("result", {}).get("success")), res


def folio_id(text):
    m = re.search(r"[0-9a-f]{24}", text)
    if not m:
        sys.exit("no folio id in: " + text)
    return m.group(0)


def tcas_token(text):
    m = re.search(r"(?:^|;\s*)accessToken=([^;]+)", text.strip())
    return m.group(1).strip() if m else text.strip()


def read_json(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    saved = read_json(COOKIES_FILE, {})
    tcas_cookie = saved.get("MYTCAS_COOKIE", "").strip()
    ifolio_cookie = saved.get("IFOLIO_COOKIE", "").strip()
    if not tcas_cookie or not ifolio_cookie:
        sys.exit(f"put MYTCAS_COOKIE and IFOLIO_COOKIE in {COOKIES_FILE}")

    folio = folio_id(input("mytcas folio URL: "))
    portfolio = input("iFolio portfolio name: ").strip()
    token = tcas_token(tcas_cookie)
    cookie = re.sub(r"^\s*cookie:\s*", "", ifolio_cookie, flags=re.I).strip().strip('"')

    r = requests.get(f"{TCAS}/folios/tcasfolios/{folio}", headers={"accessToken": token}, timeout=60)
    r.raise_for_status()
    src = r.json()["result"]
    jobs = [("competition", x) for x in src.get("awards", [])]
    jobs += [("activity", x) for x in src.get("activities", [])]
    jobs += [("activity", x) for x in src.get("projects", [])]
    print(f"mytcas: {len(jobs)} items")

    signed = {}
    firsts = [j[1]["files"][0] for j in jobs if j[1].get("files")]
    if firsts:
        r = requests.post(f"{TCAS}/folios/presign", headers={"accessToken": token}, json={"urls": firsts}, timeout=60)
        r.raise_for_status()
        urls = r.json().get("result") or []
        if len(urls) == len(firsts):
            signed = dict(zip(firsts, urls))
        else:
            print(f"presign gave {len(urls)} urls for {len(firsts)} files")

    session = requests.Session()
    session.headers.update(
        {
            "Cookie": cookie,
            "User-Agent": UA,
            "Accept": "*/*",
            "Origin": IFOLIO,
            "Referer": IFOLIO + "/student/portfolio",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
        }
    )
    r = session.get(f"{IFOLIO}/_serverFn/{FN_PORTFOLIOS}", headers={"x-tsr-serverfn": "true"}, timeout=60)
    if r.status_code != 200:
        sys.exit(f"iFolio {r.status_code}: {r.text[:300]!r}\nlog in again and copy the full Cookie header into cookies.json")
    target = find_portfolio(parse(r), portfolio)
    if not target:
        sys.exit(f"no iFolio portfolio named {portfolio}")
    print(f"iFolio {portfolio}: {target['id']}")

    done = set(read_json(STATE_FILE, []))

    for kind, item in jobs:
        key = f"{portfolio}|{kind}|{item['title']}"
        if key in done:
            print(f"skip {kind}: {item['title']}")
            continue

        data = build_data(item, kind)
        files = [signed.get(u, u) for u in item.get("files") or []]
        day = datetime.fromisoformat(data["startDate"]["$$TSS_DATE$$"].replace("Z", "+00:00")).astimezone(TH).date()
        print(f"{kind}: {item['title']} ({day}, {len(files)} images)")

        image = None
        if files:
            try:
                image = download(files[0])
            except Exception as e:
                print("  image failed:", e)
        if image is None:
            image = ("blank.png", WHITE_PNG, "image/png")
            print("  using blank image")

        try:
            ok, res = create(session, FN_COMPETITION if kind == "competition" else FN_ACTIVITY, target["id"], data, image)
        except Exception as e:
            print("  failed:", e)
            continue
        if not ok:
            print("  error:", res)
            continue

        print("  ok")
        done.add(key)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(done), f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
