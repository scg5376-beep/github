# NS-01 RSS 및 사이트맵 제출
- 출처: https://searchadvisor.naver.com/guide/request-feed
- 확인: 2026-09-18 (헤들리스 본문 추출)
- 등급: A 공식 가이드

RSS (Rich Site Summary)

RSS는 사이트의 최신 콘텐츠를 본문까지 포함하여 발행하는 XML 기반의 퍼블리싱 규약입니다. 일반적으로 구독자가 RSS 리더기를 통해서 해당 사이트의 RSS 피드로 부터 콘텐츠를 소비하는 구조로 사용되며, 뉴스나 블로그 사이트에서 주로 RSS 피드를 제공하고 있습니다.

RSS 문서 예제
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>사이트 이름</title>
    <link>http://www.example.com/</link>
    <description>사이트 설명</description>
    <item>
      <title>콘텐츠 게시글 1</title>
      <link>http://www.example.com/article-1.html</link>
      <description>글 내용 전체(또는 일부)</description>
      <pubDate>발행시간</pubDate>
      <guid>http://www.example.com/article-1.html</guid>
    </item>
    <item>
      <title>콘텐츠 게시글 2</title>
      <link>http://www.example.com/article-2.html</link>
      <description>글 내용 전체(또는 일부)</description>
      <pubDate>발행시간</pubDate>
      <guid>http://www.example.com/article-2.html</guid>
    </item>
  </channel>
</rss>

RSS 제출시 주의사항

웹마스터도구는 RSS 피드 제출시 아래와 같이 기본적인 검증 절차를 진행합니다.

RSS 피드내 모든 URL의 도메인은 소유확인 된 사이트와 동일한 도메인 이어야 합니다.
item 항목이 1개 이상이어야 합니다. 발행된 글이 없는 RSS 피드는 제출할 수 없습니다.
RSS 피드 용량이 10MB 이상 넘어가는 경우 제출 할 수 없습니다.
RSS 피드 수집시 응답속도가 느린 경우 제출이 제한될 수 있습니다.
피드에 포함되는 각 item의 본문은 일부가 아닌 모든 내용(본문 전체 공개)이 포함될 수 있도록 처리해 주세요.

아쉽게도 RSS 피드는 본문을 포함하고 있기 때문에 많은 수의 URL 을 담기가 어렵습니다. 되도록 RSS 보다는 사이트맵을 적극적으로 활용하는 것을 권장합니다.

사이트맵 (Sitemap.xml)

사이트맵 은 검색로봇에게 사이트 내에 수집되어야 할 페이지들을 알려 주기 위하여 마련된 표준 규약입니다. 사이트맵을 활용하여 URL의 추가 정보를 검색로봇에 제공할 수 있으므로 검색로봇이 사이트의 콘텐츠를 더 잘 수집할 수 있도록 도울 수 있습니다.

사이트 맵은 본문이 아닌 콘텐츠의 URL 정보만 담고 있기 때문에 사이트 내의 모든 URL을 포함하는 것을 권장합니다. 검색로봇은 해당 사이트맵에 포함된 URL 정보를 추출후 내부 알고리즘을 통하여 수집 대상 URL을 선별하여 우선 순위별로 수집을 진행합니다.

사이트맵 문서 예제

사이트맵은 사이트의 URL 모두를 담을 수 있습니다. 용량에 따라서 아래와 같이 2가지 형식으로 제출할 수 있습니다.

수집 대상 URL을 포함하는 사이트 맵으로 수집 대상 콘텐츠 URL을 포함하는 문서
요소	설명	필수여부
loc	수집 대상 URL	필수
lastmod	페이지가 수정된 날짜	선택
changefreq	페이지 변경 빈도	선택
priority	사이트내 중요도	선택
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
	<loc>http://www.example.com/article-1.html</loc>
	<lastmod>2019-08-26T11:16:53+09:00</lastmod>
	<changefreq>weekly</changefreq>
	<priority>0.8</priority>
  </url>
  <url>
	<loc>http://www.example.com/article-2.html</loc>
	<lastmod>2019-08-26T11:16:53+09:00</lastmod>
	<changefreq>weekly</changefreq>
	<priority>0.8</priority>
  </url>  
</urlset>

또다른 사이트맵을 포함하는 사이트맵 인덱스

사이트맵은 모든 URL 정보를 담고 있기 때문에 콘텐츠 타입이나 카테고리 별로 여러개의 사이트맵 문서를 제작한뒤 인덱스 문서를 사용하여 담을 수 있습니다. 예를들어 커뮤니티 사이트와 같이 사이트 내의 콘텐츠가 많은 경우 1번과 같이 단일 사이트맵에 모든 URL을 포함하기 어려운 경우 사용합니다.

요소	설명	필수여부
loc	사이트맵 URL	필수
lastmod	사이트맵이 수정된 날짜	선택
<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>http://www.example.com/sitemap-1.xml</loc>
    <lastmod>2016-02-26T18:41:07+09:00</lastmod>
  </sitemap>
  <sitemap>
    <loc>http://www.example.com/sitemap-2.xml</loc>
    <lastmod>2015-05-14T21:06:14+09:00</lastmod>
  </sitemap>
</sitemapindex>

사이트맵 제출시 주의사항

웹마스터도구는 사이트맵 피드 제출시 아래와 같이 기본적인 검증 절차를 진행합니다.

사이트맵 피드내 모든 URL의 도메인은 소유확인 된 사이트와 동일한 도메인 이어야 합니다.
사이트맵 피드 용량이 10MB 이상 넘어가는 경우 제출 할 수 없습니다.
하나의 사이트맵은 50,000 개 이상의 URL 을 포함할 수 없습니다.
사이트맵 수집시 응답속도가 느린 경우 제출이 제한될 수 있습니다.