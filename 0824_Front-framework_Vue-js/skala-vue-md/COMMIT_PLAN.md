# 커밋 분할안 (초안)

> 실행 전 확인용 문서입니다. 실제 커밋은 검토 후 진행합니다.
> 각 커밋은 그 시점에 `npm run lint`와 `npm run build`가 통과하는 상태를 유지합니다.

현재 상태: 기존 커밋 2개 위에 변경분이 쌓여 있음

```
54cda52 feat: Weather Mockup 및 Composition 구현
399aa3a feat: Vue hands-on 프로젝트 구현
```

---

## 1. `chore: 스캐폴딩 잔여 파일 정리`

Vite 기본 템플릿에서 생성됐지만 사용하지 않는 파일을 제거한다.
`HomeView → TheWelcome → WelcomeItem + icons` 전체가 라우터에서 끊어진 죽은 체인이었다.

```
D  src/views/HomeView.vue
D  src/views/AboutView.vue
D  src/components/HelloWorld.vue
D  src/components/TheWelcome.vue
D  src/components/WelcomeItem.vue
D  src/components/icons/           (5개)
D  src/assets/logo.svg
D  src/stores/counter.js
D  public/images/south-korea-locator.svg
```

---

## 2. `refactor: 실습 컴포넌트 폴더·파일명 정리`

과제 자료의 폴더 트리(`exercise`)와 컴포넌트 명명 규칙(두 단어 이상 PascalCase)에 맞춘다.

```
R  src/components/excercise/ → src/components/exercise/
R  EventHandler_v-on.vue → EventHandlerEx.vue
R  FormDataBinding_Modifier.vue → FormDataBindingModifier.vue
R  FormDataBinding_Declaringv-modelVariables.vue → FormDataBindingVModel.vue
M  src/views/WeatherHomeView.vue        (import 경로)
```

---

## 3. `feat: Hands-on 3·4 - 컴포넌트 분리와 라우팅`

Props·Emits·Slot 기반 컴포넌트 분리와 Vue Router 구성.

```
A  src/components/exercise/            (BaseDashboardCard, SearchBar, WeatherCard,
                                        WeatherStatusFilter, WeatherParent 등)
A  src/views/WeatherHomeView.vue
A  src/views/WeatherDetailView.vue
A  src/views/WeatherAboutView.vue
A  src/views/NotFoundView.vue
M  src/router/index.js
M  src/App.vue
D  src/components/hands-on/            (excercise로 이동)
```

포인트: `WeatherCard`의 `click-detail`은 값을 낱개로 넘기지 않고 **도시 객체 하나**를 전달해,
부모가 각자 필요한 값만 사용하도록 했다. (`WeatherParent`는 alert, `WeatherHomeView`는 `router.push`)

---

## 4. `feat: Hands-on 5 - Pinia Store와 온도 단위 전환`

```
A  src/stores/configStore.js           (unit / unitSymbol / toggleUnit / convertTemperature)
A  src/components/clothes/UnitToggler.vue
M  src/App.vue                          (Navigation Bar 옆 배치)
M  src/components/exercise/WeatherCard.vue
M  src/views/WeatherDetailView.vue
```

포인트: 단위 변환 로직을 View마다 복제하지 않고 `configStore.convertTemperature()` 하나로 모았다.
더움/선선함 판정은 화면 표시와 무관하게 **항상 원본 섭씨**로 계산한다.

---

## 5. `feat: 오늘 뭐 입지? - 지도 기반 옷차림 추천 View 추가`

Hands-on 4의 "본인 추가 View" 요구사항을 확장한 서비스.

```
A  src/views/views-clothes/            (ClothesMapView, ClothesWeatherDetailView,
                                        clothesWeatherData)
A  src/components/clothes/             (BaseMapPanel, ClothesCityMarker,
                                        ClothesSearchBar, ClothesWeatherFilter,
                                        ClothesWeatherPopup)
A  src/stores/weatherStore.js
A  public/images/                      (지도 SVG 3종)
M  src/router/index.js
```

포인트: 마커 위치는 수작업 좌표가 아니라 **위경도 투영**으로 계산한다.
지도 SVG의 실제 렌더링 영역을 측정해 축척을 역산했고, 본토 남단(34.29°N)과
동단(129.57°E)으로 검증했다. 정확한 위치를 나타내는 **앵커 점**과 읽기 위한 **라벨**을
분리해, 라벨이 겹칠 때는 라벨만 옮기고 위치는 그대로 둔다.

---

## 6. `feat: Hands-on 6 - Axios 실시간 날씨 연동`

```
A  src/api/weatherApi.js               (현재날씨 / 예보 / 대기질 / 지역검색)
A  src/api/kmaWarningApi.js            (기상청 특보현황)
A  src/utils/airQuality.js             (PM10·PM2.5 등급 계산)
M  src/stores/weatherStore.js          (fetch 액션, 캐시, 10분 자동 갱신)
M  src/views/views-clothes/*           (예보 띠, 하루 계획, 대기질, 안전 모드)
M  package.json                        (axios)
```

포인트: 예보 응답의 `dt_txt`는 UTC라 도시 `timezone`으로 현지 시각 변환이 필요하다.
지도에서는 22건, 상세 화면에서는 해당 도시만 호출하고 캐시한다.
`Promise.allSettled`로 일부 실패해도 나머지 결과는 유지한다.

---

## 7. `feat: Hands-on 7 - Element Plus 적용 및 번들 최적화`

```
M  src/main.js
M  vite.config.js                      (unplugin-vue-components + ElementPlusResolver)
M  src/views/views-clothes/*           (el-skeleton / el-alert / el-tag / ElMessage)
M  package.json
```

포인트: `app.use(ElementPlus)` 전역 등록은 3개 컴포넌트만 써도 라이브러리 전체를 포함시켜
메인 번들이 182 kB → 1,095 kB(gzip 68 → 355 kB)가 됐다.
온디맨드 방식으로 전환해 189 kB(gzip 71 kB)로 되돌렸다.

---

## 8. `feat: Hands-on 8 - API Key 서버 이전 및 Vercel 배포 설정`

```
A  api/owm.js                          (OpenWeatherMap 중계, 엔드포인트 화이트리스트)
A  api/kma-warnings.js                 (기상청 중계, CORS 우회 + EUC-KR → UTF-8)
A  vercel.json                         (SPA 딥링크 rewrite)
A  .env.example
M  vite.config.js                      (개발 서버에서 동일 함수 실행)
M  src/api/*                           (키 파라미터 제거)
M  src/stores/weatherStore.js          (키 유무 분기 제거)
M  .gitignore
M  eslint.config.js                    (api/ 는 Node 환경)
```

포인트: `VITE_` 접두사 환경변수는 빌드 시 값이 코드에 치환되어 배포된 JS에서 확인 가능하다.
실제로 빌드 결과물에서 `authKey`가 검색됐다. 기상청 API는 CORS도 허용하지 않아,
두 문제를 서버리스 함수로 함께 해결했다. 검증 결과 두 키 모두 번들에서 사라졌다.

---

## 9. `chore: Prettier 검사 범위 확대`

`format` 스크립트가 `src/`만 대상이라 `api/`·`vite.config.js`·`index.html`·`README.md`가
검사에서 빠져 있었다.

```
M  package.json                        (format 범위 확대, format:check 추가)
A  .prettierignore
M  index.html
M  README.md
```

---

## 10. `docs: README 작성`

단계별 요구사항 충족 내역과 개인 Customization, 설계 판단 근거를 정리한다.

```
M  README.md
```

---

## 커밋 후 남는 작업

- [ ] GitHub Public 저장소에 push
- [ ] Vercel 프로젝트 연결 + 환경 변수 2개 등록 (`OPENWEATHER_API_KEY`, `KMA_API_KEY`)
- [ ] 배포 URL을 README 상단에 추가
- [ ] 시크릿 창으로 저장소·배포 주소 접근 확인 (과제 제출 전 확인 항목)

## 검토가 필요한 항목

- `design-audit/` (스크린샷 9장), `design-qa.md` — 지금 레이아웃과 내용이 어긋나 있다.
  갱신하거나 커밋에서 제외할지 결정 필요.
- `COMMIT_PLAN.md` (이 문서) — 커밋 전에 삭제할지 남길지 결정 필요.
