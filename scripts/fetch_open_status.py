"""admin 에 설정된 페어 오픈 상태를 ocreo 공개 API 에서 받아 open-status.json 으로 저장.

대시보드(github.io)는 API 서버가 ocreo.kr 출처만 허용해서 직접 못 부른다.
그래서 GitHub Actions 가 1시간마다 이 스크립트를 돌려 같은 저장소에 JSON 을 남긴다.
데이터가 바뀌었을 때만 파일 내용이 달라지도록 수집 시각은 넣지 않는다.
"""
import json
import pathlib
import urllib.request

API = "https://backend-api.ocreo.kr/graphql"
QUERY = """query{fairs{code name version type fairStartAt
  isFairStoryOpen isBuyerRegistrationOpen isFairParticipantListOpen
  fairPeriod{applicantType applyStartAt applyEndAt}}}"""
HEADERS = {
    "Content-Type": "application/json",
    "Origin": "https://ocreo.kr",
    "Referer": "https://ocreo.kr/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/139.0 Safari/537.36",
}


def main():
    req = urllib.request.Request(API, json.dumps({"query": QUERY}).encode(), HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if body.get("errors") or not body.get("data"):
        raise SystemExit(f"API 오류: {body.get('errors')}")
    fairs = []
    for f in sorted(body["data"]["fairs"], key=lambda x: x["code"]):
        fairs.append({
            "code": f["code"], "name": f["name"], "version": f["version"], "type": f["type"],
            "fairStartAt": f["fairStartAt"],
            "story": f["isFairStoryOpen"], "buyer": f["isBuyerRegistrationOpen"],
            "participants": f["isFairParticipantListOpen"],
            "periods": {p["applicantType"]: [p["applyStartAt"], p["applyEndAt"]]
                        for p in sorted(f["fairPeriod"] or [], key=lambda p: p["applicantType"])},
        })
    out = pathlib.Path(__file__).resolve().parent.parent / "open-status.json"
    out.write_text(json.dumps({"fairs": fairs}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(fairs)}개 페어 저장 → {out}")


if __name__ == "__main__":
    main()
