# Design QA - 오늘 뭐 입지?

## Comparison Target

- Source visual truth: `/Users/beeyaaa/.codex/generated_images/01a0127b-d5fe-7011-b98f-81f42297fc70/exec-58d5b2c2-9144-446a-ab64-9b8251fbfdae.png`
- Implementation screenshot: `/Users/beeyaaa/Workspace/SK-SKALA/0824_Front-framework_Vue-js/skala-vue/design-audit/09-popup-desktop-final.png`
- Responsive screenshot: `/Users/beeyaaa/Workspace/SK-SKALA/0824_Front-framework_Vue-js/skala-vue/design-audit/08-popup-mobile.png`
- Desktop viewport: 1488 x 1058 CSS px, device scale factor 1
- Source pixels: 1487 x 1058
- Implementation pixels: 1488 x 1058
- Responsive viewport: 390 x 844 CSS px; captured page pixels: 375 x 812
- State: `/clothes`에서 서울 마커를 선택하여 팝업이 열린 상태

## Full-view Comparison Evidence

- 동일한 데스크톱 크기와 동일한 서울 선택 상태로 원본 시안과 구현 화면을 함께 비교했다.
- 상단 내비게이션, 중앙 타이틀, 밝은 지도 배경, 알약형 도시 마커, 중앙 2열 팝업, 검정 CTA의 전체 구성이 시안과 같은 우선순위로 구현되었다.
- 원본 시안의 섬 표기를 유지하기 위해 울릉도와 독도를 별도 공개 지도 자산으로 표시했다.

## Focused Region Comparison Evidence

- 중앙 팝업의 도시명, 28°C 기온, 날씨 아이콘, 추천 근거, 요약/옷차림/준비물 3개 행, 상세 날씨 버튼을 확대해 비교했다.
- 팝업 폭, 내부 2열 비율, 구분선, 그림자, 아이콘 배경, 텍스트 위계가 원본 시안과 근접하며 모든 텍스트가 읽히는 것을 확인했다.

## Required Fidelity Surfaces

- Fonts and typography: 시스템 한글 산세리프를 사용해 굵기와 위계를 재현했다. 중앙 타이틀, 도시명, 대형 기온, 보조 텍스트의 대비가 명확하다.
- Spacing and layout rhythm: 82px 헤더, 넓은 지도 영역, 680px 팝업, 2열 정보 구조와 행 간격이 안정적이다.
- Colors and visual tokens: 밀크 화이트, 쿨 그레이 블루, 세이지 그린, 차콜 팔레트를 일관되게 적용했다.
- Image quality and asset fidelity: 대한민국/울릉도/독도 지도는 Wikimedia Commons 원본 SVG를 사용했다. 날씨 및 옷차림 아이콘은 Phosphor Icons를 사용해 텍스트 기호와 이모지를 제거했다.
- Copy and content: 서울 28°C 맑음과 옷차림 추천 문구가 시안의 목적과 일치하며 22개 주요 도시 모두 현실적인 Mock Data를 사용한다.

## Comparison History

### Iteration 1

- Earlier finding [P1]: 첫 지도 자산이 동아시아 전체 위치도여서 대한민국 중심의 시안과 크게 달랐다.
- Fix: 대한민국 행정구역 원본 지도로 교체하고, 울릉도와 독도 원본 지도 자산을 별도로 배치했다.
- Post-fix evidence: `design-audit/05-map-implemented.png`

### Iteration 2

- Earlier finding [P2]: 대한민국 지도 폭이 시안보다 지나치게 좁아 도시 마커가 중앙에 밀집했다.
- Fix: 지도 폭을 화면의 52%로 조정하고 주요 도시 마커를 시안의 공간 배치에 가깝게 재조정했다.
- Post-fix evidence: `design-audit/09-popup-desktop-final.png`

## Interaction Verification

- 도시 마커 클릭 시 팝업 열림
- 팝업 내부 클릭 시 유지
- 닫기 버튼 및 지도 빈 영역 클릭 시 팝업 닫힘
- 상세 날씨 보기 클릭 시 `/clothes/weather/city_01` 이동
- 모바일 화면에서 팝업이 단일 열로 전환되고 화면 안에서 스크롤 가능
- 브라우저 콘솔 warning/error 없음
- `npm run lint` 통과
- `npm run build` 통과

## Follow-up Polish

- [P3] 실시간 OpenWeatherMap API를 연결하면 도시별 기온과 날씨 상태를 실제 데이터로 교체할 수 있다.
- [P3] Pinia 단위 Store 실습에서 섭씨/화씨 전환을 마커, 팝업, 상세 화면에 공통 적용할 수 있다.

final result: passed
