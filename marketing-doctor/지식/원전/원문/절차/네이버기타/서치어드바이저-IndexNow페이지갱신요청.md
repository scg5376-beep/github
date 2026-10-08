# 페이지 갱신 요청하기 - 네이버 서치어드바이저
- 출처: https://searchadvisor.naver.com/guide/indexnow-request
- 확인: 2026-10-08 (헤들리스 Edge 로 본문 수집, node fetch_text.mjs)
- 등급: A 공식 가이드

한 개의 페이지에 대한 갱신 요청하기

HTTP 요청을 이용하여 웹사이트의 페이지가 갱신되었음을 검색엔진에 알립니다.

요청 형식
GET https://searchadvisor.naver.com/indexnow
 ?url=문자열
 &key=문자열
 &[keyLocation=문자열]

url (필수) : 검색엔진에 갱신되었음을 알리고 싶은 url 을 명시합니다. RFC3986 표준에 부합하는 URL 문자열이어야 합니다.
key (필수) : 웹사이트의 소유자임을 증명하는 key 문자열입니다.
keyLocation (선택) : key 파일 위치는 기본적으로 웹사이트의 루트에 위치하지만, 필요시 원하는 곳으로 지정할 수 있습니다.

key 와 keyLocation 관련해서는 link 의 문서도 참조하시기 바랍니다.

여러 개의 페이지에 대한 갱신 요청하기

HTTP POST 요청에 Json 데이터를 이용하여 웹사이트의 페이지가 갱신되었음을 검색엔진에 알립니다.
한 번에 여러 개의 URL에 대한 갱신을 알릴 수 있습니다.

요청형식
POST /indexnow HTTP/1.1
Content-Type: application/json; charset=utf-8
Host: searchadvisor.naver.com
{
    "host": "www.example.com",
    "key": "0f26d5e892544f74b806ec5c5522e6a1",
    "keyLocation": "https://www.example.com/myIndexNowKey63638.txt",
    "urlList": [
        "https://www.example.com/url1",
        "https://www.example.com/folder/url2",
        "https://www.example.com/url3"
    ]
}

host : 웹사이트 도메인을 기재합니다.
key : 웹사이트의 소유자임을 증명하는 key 문자열입니다.
keyLocation (선택) : key 파일 위치는 기본적으로 웹사이트의 루트에 위치하지만, 필요시 원하는 곳으로 지정할 수 있습니다.
urlList : 검색엔진에 갱신되었음을 알리고 싶은 url들을 명시합니다. RFC3986 표준에 부합하는 URL 문자열이어야 합니다. 한 번의 POST 요청에 최대 10,000개까지의 url 을 담을 수 있습니다.

key 와 keyLocation 관련해서는 link 의 문서도 참조하시기 바랍니다.

API의 HTTP 응답 형식
HTTP Code | 응답 메시지 | 설명
200 | Success | 전송이 성공하였습니다.
202 | Accepted | URL 정보가 수신되었습니다. key 정보를 확인 중입니다.
400 | Bad request | 잘못된 형식으로 요청되었습니다.
403 | Forbidden | key가 유효하지 않습니다.
422 | Unprocessable Entity | URL이 key 정보와 일치하지 않습니다.
429 | Too Many Requests | 과도하게 많은 요청을 보내고 있습니다.
500 | Server error | 서버 에러입니다.
