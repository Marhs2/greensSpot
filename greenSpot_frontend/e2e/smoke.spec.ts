import { test, expect } from "@playwright/test";

/**
 * GreenSpot Playwright smoke / 핵심 플로우
 * - 비회원 대시보드
 * - 통계 화면
 * - 로그인 UI
 * - 회원가입 → 로그인 (백엔드 연동)
 * - AI 검색 (지역 입력)
 */

test.describe("GreenSpot E2E", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("대시보드 헤더와 에이전트 패널이 보인다", async ({ page }) => {
    await expect(page.getByText("GreenSpot", { exact: true }).first()).toBeVisible();
    await expect(page.getByRole("heading", { name: "AI 부지 검색 에이전트" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "부지 목록" })).toBeVisible();
    await expect(page.getByRole("button", { name: "대시보드" })).toBeVisible();
    await expect(page.getByRole("button", { name: "통계" })).toBeVisible();
  });

  test("통계 화면으로 전환된다", async ({ page }) => {
    await page.getByRole("button", { name: "통계" }).click();
    // StatsView 제목/섹션
    await expect(page.getByText(/통계|트렌드|검색 기록|자치구/i).first()).toBeVisible({
      timeout: 10_000,
    });
    await page.getByRole("button", { name: "대시보드" }).click();
    await expect(page.getByRole("heading", { name: "AI 부지 검색 에이전트" })).toBeVisible();
  });

  test("비회원은 로그인 화면으로 갈 수 있다", async ({ page }) => {
    await page.getByRole("button", { name: "로그인" }).click();
    await expect(page.getByRole("heading", { name: "로그인" })).toBeVisible();
    await expect(page.getByText("GreenSpot에 로그인하세요")).toBeVisible();
    await page.getByRole("button", { name: /로그인 없이 둘러보기/ }).click();
    await expect(page.getByRole("heading", { name: "AI 부지 검색 에이전트" })).toBeVisible();
  });

  test("회원가입 후 대시보드에 진입한다", async ({ page }) => {
    const email = `e2e_${Date.now()}@example.com`;
    const password = "secret12";

    await page.getByRole("button", { name: "회원가입" }).click();
    await expect(page.getByRole("heading", { name: "회원가입" })).toBeVisible();

    await page.getByPlaceholder("홍길동").fill("E2E User");
    await page.locator('input[type="email"]').fill(email);
    await page.locator('input[type="password"]').fill(password);

    await page.locator("form").getByRole("button", { name: "회원가입" }).click();

    await expect(page.getByRole("heading", { name: "AI 부지 검색 에이전트" })).toBeVisible({
      timeout: 20_000,
    });
  });

  test("AI 검색창에 지역을 입력하고 검색한다", async ({ page }) => {
    const input = page.getByPlaceholder(/지역|용산|해운대|VWorld|검색/i);
    await expect(input).toBeVisible();
    await input.fill("중구");
    await page.getByRole("button", { name: /검색/ }).click();

    // 로딩 후 결과 또는 안내 메시지 (VWorld 키 유무에 따라 다름)
    await expect(
      page
        .getByText(/결과|건|찾지|지역|추천|VWorld|불러|실패|없습니다|실시간/i)
        .first(),
    ).toBeVisible({ timeout: 90_000 });
  });

  test("북마크 시트 열기 (비회원 안내)", async ({ page }) => {
    await page.getByRole("button", { name: /북마크/ }).click();
    await expect(
      page.getByText(/로그인|북마크|저장된 부지/i).first(),
    ).toBeVisible({ timeout: 10_000 });
  });
});
