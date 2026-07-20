// 필요한 HTML 요소 선택

/* [빈칸 후보 20] ID가 menuToggle인 요소 한 개 선택 */
const menuToggle = document.getElementById("menuToggle");

const navList = document.getElementById("navList");

/* [빈칸 후보 21] 모든 filter-btn 요소 선택 */
const filterButtons =
  document.querySelectorAll(".filter-btn");

/* [빈칸 후보 22] 모든 menu-card 요소 선택 */
const menuCards =
  document.querySelectorAll(".menu-card");

const orderButtons =
  document.querySelectorAll(".order-btn");

const result = document.getElementById("result");


// 1. 모바일 메뉴 열기와 닫기

/* [빈칸 후보 23] 클릭 이벤트 등록 */
menuToggle.addEventListener("click", function () {
  /* [빈칸 후보 24] open 클래스를 추가하거나 제거 */
  navList.classList.toggle("open");

  const isOpen = navList.classList.contains("open");

  /*
    aria-expanded에는 문자열 "true" 또는 "false"가 들어간다.
  */
  menuToggle.setAttribute("aria-expanded", String(isOpen));
});


// 2. 상품 카테고리 필터링

filterButtons.forEach(function (button) {
  button.addEventListener("click", function (event) {
    /*
      [빈칸 후보 25]
      실제 클릭된 요소를 가져온다.
    */
    const clickedButton = event.target;

    /*
      data-category 속성 값을 가져온다.
      예: all, coffee, dessert
    */
    const selectedCategory =
      clickedButton.dataset.category;

    // 모든 필터 버튼에서 active 클래스 제거
    filterButtons.forEach(function (item) {
      item.classList.remove("active");
    });

    // 클릭한 버튼에 active 클래스 추가
    clickedButton.classList.add("active");

    menuCards.forEach(function (card) {
      const cardCategory = card.dataset.category;

      /*
        전체 버튼을 선택했거나
        카드의 카테고리가 선택값과 같으면 표시한다.
      */
      const shouldShow =
        selectedCategory === "all" ||
        cardCategory === selectedCategory;

      /*
        [빈칸 후보 26]
        shouldShow가 false일 때 hidden 클래스를 추가한다.
      */
      card.classList.toggle("hidden", !shouldShow);
    });
  });
});


// 3. 주문 버튼 처리

orderButtons.forEach(function (button) {
  button.addEventListener("click", function (event) {
    /*
      클릭된 버튼에서 가장 가까운
      .menu-card 부모 요소를 찾는다.
    */
    const card = event.target.closest(".menu-card");

    /*
      카드 내부의 h3를 찾아 상품명을 가져온다.
    */
    const productName =
      card.querySelector("h3").textContent;

    /* [빈칸 후보 27] 결과 영역에 문자열 출력 */
    result.textContent =
      `${productName}을(를) 선택했습니다.`;
  });
});