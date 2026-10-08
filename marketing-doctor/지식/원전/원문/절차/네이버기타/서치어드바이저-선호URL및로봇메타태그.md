# 선호 URL 및 로봇 메타 태그 - 네이버 서치어드바이저
- 출처: https://searchadvisor.naver.com/guide/markup-structure
- 확인: 2026-10-08 (헤들리스 Edge 로 본문 수집, node fetch_text.mjs)
- 등급: A 공식 가이드

선호 URL (=대표 URL)

HTML 문서의 <head> 태그내에 있는 <link> 태그를 활용합니다

<head>
<link rel="canonical" href="http://www.mysite.com/article/article1.html">
</head>

동일 콘텐츠를 여러 개의 URL로 표현이 가능할 경우 가장 선호되는 대표 URL을 지정합니다. 예를 들어 아래 세 개의 URL이 동일한 페이지를 보여준다면, 선호 URL을 http://www.mysite.com/article/article1.html 로 지정하는 것이 좋습니다. 또한, URL 표현시에는 상대 경로가 아닌 절대 경로를 사용해야 합니다.

http://www.mysite.com/article/article1.html
http://www.mysite.com/article/article1.html?type=1&code=a
http://www.mysite.com/article/article1.html?type=2&code=b

사이트의 메인 페이지의 경우는 link 태그를 활용한 선호 URL 지정보다는 HTTP redirect를 사용하여 사이트를 방문하는 사용자에게 혼동을 주지 않는 것이 좋습니다. 자세한 내용은 검색엔진 최적화 가이드를 참고하세요.

로봇 메타 태그

HTML 문서의 <head> 태그내에 있는 <meta> 태그를 활용합니다

<head>
<meta name="robots" content="명령어">
</head>

로봇 메타 태그는 페이지 별로 검색로봇의 접근 여부를 제어할 수 있는 정보입니다.
명령어에 noindex를 사용하면 해당 페이지는 검색 결과에서 제외되며, nofollow를 사용하면 검색로봇이 해당 페이지 내의 링크를 수집하지 않도록 설정할 수 있습니다.
명령어에 nosourceinfo를 사용하는 경우, 해당 사이트에 대해 AI로 자동 생성된 출처설명이 제공되지 않습니다.

색인 대상으로 처리, 페이지 내 링크 미 수집
<head>
<meta name="robots" content="index,nofollow">
</head>

색인 대상에서 제외, 페이지 내 링크 수집
<head>
<meta name="robots" content="noindex,follow">
</head>

색인 대상에서 제외, 페이지 내 링크 미 수집
<head>
<meta name="robots" content="noindex,nofollow">
</head>

사이트 출처설명 제외
<head>
<meta name="robots" content="nosourceinfo">
</head>

검색로봇에 대하여 특별한 제약조건이 없다면 웹 페이지가 검색 결과에서 제외되지 않도록 로봇 메타 태그를 삭제하거나 아래와 같이 기본 설정인 index, follow로 설정하시는 것을 권장합니다.

<head>
<meta name="robots" content="index,follow">
</head>

참고로, 로봇이 태그를 해석함에 있어서, 해당 페이지가 다른 URL로 이동하는 리다이렉트 기능만으로 구성되어 있는 페이지의 경우에는 메타 태그가 제대로 반영하지 않을 수 있습니다.
이 경우에는 리다이렉트 타겟이 된 모든 페이지에 동일한 설정을 하는 것을 권장드립니다.
