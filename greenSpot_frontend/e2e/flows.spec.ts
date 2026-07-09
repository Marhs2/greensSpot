import { test, expect, type Page } from "@playwright/test";

async function searchRegion(page: Page, region: string) {
  const input = page.getByPlaceholder(/지역|용산|해운대|VWorld|검색/i);
  await input.fill(region);
  await page.getByRole("button", { name: /검색/ }).click();
  // 로딩 종료 대기
  await page.getByText(/실시간으로 부지를 조회/i).waitFor({ state: "hidden", timeout: 120_000 }).catch(() => {});
}

test.describe("GreenSpot 심화 플로우", () => {
  test("agent 검색 후 부지 선택·상세 탭", async ({ page }) => {
    await page.goto("/");
    await searchRegion(page, "용산구");

    // 요약 또는 목록 카드 대기
    await expect(
      page.getByText(/VWorld|결과 \d+건|추천됩니다|찾지|지역을/i).first(),
    ).toBeVisible({ timeout: 120_000 });

    const listCard = page.locator(".group.relative.cursor-pointer").first();
    await expect(listCard).toBeVisible({ timeout: 30_000 });
    await listCard.click();

    for (const tab of ["개요", "점수", "AI 설명", "시뮬레이션"]) {
      const t = page.getByRole("tab", { name: tab });
      if (await t.count()) {
        await t.click();
        await page.waitForTimeout(200);
      }
    }
    const scoresTab = page.getByRole("tab", { name: "점수" });
    if (await scoresTab.count()) {
      await scoresTab.click();
      await expect(
        page.getByText(/1순위 추천|수목 식재|텃밭|태양광|기여 요인/i).first(),
      ).toBeVisible({ timeout: 10_000 });
    }
  });

  test("비교: 부지 2개 선택 후 비교 다이얼로그", async ({ page }) => {
    await page.goto("/");
    await searchRegion(page, "중구");

    const cards = page.locator(".group.relative.cursor-pointer");
    await page.waitForTimeout(2000);
    const n = await cards.count();
    test.skip(n < 2, "비교할 부지가 2개 미만");

    // 비교 토글 버튼 (+ 아이콘 버튼)
    for (let i = 0; i < Math.min(2, n); i++) {
      const compareBtn = cards.nth(i).locator("button").filter({ has: page.locator("svg") }).last();
      // 비교 버튼 찾기: aria-label 비교
      const btn = cards.nth(i).getByRole("button", { name: "비교" });
      if (await btn.count()) await btn.click();
      else {
        // 마지막 작은 버튼들이 북마크/비교
        const buttons = cards.nth(i).locator("button");
        const bc = await buttons.count();
        if (bc >= 2) await buttons.nth(bc - 1).click();
      }
      await page.waitForTimeout(200);
    }

    const openCompare = page.getByRole("button", { name: /비교\s*\(/ });
    if (await openCompare.count()) {
      await openCompare.click();
      await expect(page.getByRole("dialog")).toBeVisible({ timeout: 15_000 });
    }
  });

  test("로그인 실패 시 에러 표시", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "로그인" }).click();
    await page.locator('input[type="email"]').fill("not-exist@example.com");
    await page.locator('input[type="password"]').fill("wrongpassword");
    await page.locator("form").getByRole("button", { name: "로그인" }).click();
    await expect(page.locator("text=/실패|Invalid|오류|올바르|없습니다|인증/i").first()).toBeVisible({
      timeout: 10_000,
    });
  });

  test("회원가입 짧은 비밀번호 검증", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "회원가입" }).click();
    await page.getByPlaceholder("홍길동").fill("테스트유저");
    await page.locator('input[type="email"]').fill(`short_${Date.now()}@ex.com`);
    await page.locator('input[type="password"]').fill("12");
    await page.locator("form").getByRole("button", { name: "회원가입" }).click();
    await expect(
      page.getByText("비밀번호는 최소 6자 이상이어야 합니다."),
    ).toBeVisible({ timeout: 5_000 });
  });

  test("다크모드 토글", async ({ page }) => {
    await page.goto("/");
    const themeBtn = page.getByRole("button", { name: "테마 전환" });
    await themeBtn.click();
    await expect(page.locator("html.dark")).toHaveCount(1);
    await themeBtn.click();
  });

  test("공유 버튼 클릭 시 토스트 또는 클립보드", async ({ page, context }) => {
    await context.grantPermissions(["clipboard-read", "clipboard-write"]).catch(() => {});
    await page.goto("/");
    await searchRegion(page, "마포구");
    const card = page.locator(".group.relative.cursor-pointer").first();
    if (!(await card.count())) {
      test.skip(true, "부지 없음");
      return;
    }
    await card.click();
    const share = page.getByRole("button", { name: /공유/ });
    if (await share.count()) {
      await share.click();
      await expect(
        page.getByText(/복사|공유|링크/i).first(),
      ).toBeVisible({ timeout: 5_000 });
    }
  });
});
