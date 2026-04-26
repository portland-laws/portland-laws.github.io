import { expect, Page, test, TestInfo } from '@playwright/test';
import { mkdirSync } from 'node:fs';
import path from 'node:path';

const screenshotRoot = path.join(process.cwd(), 'tests', 'screenshots', 'portland-ui');

test.beforeAll(() => {
  mkdirSync(screenshotRoot, { recursive: true });
});

test.beforeEach(async ({ page }) => {
  await page.goto('/');
  await page.addStyleTag({
    content: `
      *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        caret-color: transparent !important;
        scroll-behavior: auto !important;
        transition-duration: 0.01ms !important;
      }
    `,
  });
  await waitForCorpusReady(page);
});

test.describe('Portland legal corpus UI screenshots', () => {
  test('captures the desktop legal directory, search, and workbench layout', async ({ page }, testInfo) => {
    await expect(page.getByRole('heading', { name: 'City Code Research Directory' })).toBeVisible();
    await expect(page.getByRole('navigation', { name: 'City Code' })).toBeVisible();
    await expect(page.getByRole('region', { name: 'Find Code Sections' })).toBeVisible();
    await expect(page.getByRole('region', { name: 'Selected section and research tools' })).toBeVisible();

    await expectNoHorizontalOverflow(page);
    await page.screenshot({
      path: screenshotPath(testInfo, 'desktop-directory-search-workbench.png'),
      fullPage: true,
    });
  });

  test('captures search, section reader, and all research workbench tabs', async ({ page }, testInfo) => {
    await page.getByLabel('Search Portland City Code').fill('rental housing permits');
    await page.getByRole('button', { name: /^Search$/ }).click();
    await expect(page.locator('#search-status')).toContainText(/matches/);

    await page.getByRole('button', { name: /^Select / }).first().click();
    await expect(page.getByRole('heading', { name: /Logic Proof Explorer|GraphRAG Chat|Knowledge Graph Entities|.+/ }).first()).toBeVisible();

    await page.locator('#research-workbench').screenshot({
      path: screenshotPath(testInfo, 'desktop-section-reader.png'),
    });

    await page.getByRole('tab', { name: 'GraphRAG' }).click();
    await page.locator('#panel-chat').getByLabel('Question').fill('What does this section say in simple terms?');
    await page.getByRole('button', { name: /^Ask$/ }).click();
    await expect(page.locator('#panel-chat')).toContainText(/informational|code|section|evidence/i, { timeout: 15000 });
    await page.locator('#research-workbench').screenshot({
      path: screenshotPath(testInfo, 'desktop-graphrag-chat.png'),
    });

    await page.getByRole('tab', { name: 'Knowledge Graph' }).click();
    await expect(page.getByRole('heading', { name: 'Knowledge Graph Entities' })).toBeVisible();
    await page.locator('#research-workbench').screenshot({
      path: screenshotPath(testInfo, 'desktop-knowledge-graph.png'),
    });

    await page.getByRole('tab', { name: 'Logic Proofs' }).click();
    await expect(page.getByRole('heading', { name: 'Logic Proof Explorer' })).toBeVisible();
    await page.locator('#research-workbench').screenshot({
      path: screenshotPath(testInfo, 'desktop-logic-proofs.png'),
    });

    await expectNoHorizontalOverflow(page);
  });

  test('captures keyboard skip links and tab keyboard navigation states', async ({ page }, testInfo) => {
    await page.keyboard.press('Tab');
    await expect(page.getByRole('link', { name: 'Skip to code directory' })).toBeFocused();
    await page.screenshot({
      path: screenshotPath(testInfo, 'keyboard-skip-links-visible.png'),
      fullPage: true,
    });

    await page.getByRole('button', { name: /^Select / }).first().click();
    await page.getByRole('tab', { name: 'Section' }).focus();
    await page.keyboard.press('ArrowRight');
    await expect(page.getByRole('tab', { name: 'GraphRAG' })).toBeFocused();
    await expect(page.getByRole('tab', { name: 'GraphRAG' })).toHaveAttribute('aria-selected', 'true');
    await page.locator('#research-workbench').screenshot({
      path: screenshotPath(testInfo, 'keyboard-workbench-tab-focus.png'),
    });
  });
});

test.describe('Portland legal corpus mobile screenshots', () => {
  test.use({ viewport: { width: 390, height: 844 }, isMobile: true });

  test('captures the mobile directory/search/workbench stack without page overflow', async ({ page }, testInfo) => {
    await expectNoHorizontalOverflow(page);
    await page.screenshot({
      path: screenshotPath(testInfo, 'mobile-full-page-stack.png'),
      fullPage: true,
    });

    await page.getByRole('tab', { name: 'Knowledge Graph' }).click();
    await expect(page.getByRole('tab', { name: 'Knowledge Graph' })).toHaveAttribute('aria-selected', 'true');
    await expectNoHorizontalOverflow(page);
    await page.locator('#research-workbench').screenshot({
      path: screenshotPath(testInfo, 'mobile-scrollable-tabs-knowledge-graph.png'),
    });
  });

  test('captures mobile search results after filtering', async ({ page }, testInfo) => {
    await page.getByLabel('Search Portland City Code').fill('noise');
    await page.getByRole('button', { name: /^Search$/ }).click();
    await expect(page.locator('#search-status')).toContainText(/matches/);
    await expect(page.getByRole('button', { name: /^Select / }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /Show \d+ more results/ })).toBeVisible();

    await expectNoHorizontalOverflow(page);
    await page.locator('#code-search').screenshot({
      path: screenshotPath(testInfo, 'mobile-search-results.png'),
    });

    await page.getByRole('button', { name: /Show \d+ more results/ }).click();
    await expect(page.locator('#search-status')).toContainText(/showing 12/);
  });

  test('moves mobile users from a selected result into the research workbench', async ({ page }, testInfo) => {
    await page.getByRole('button', { name: /^Select / }).first().click();
    await expect(page.locator('#panel-section')).toBeFocused();

    const workbenchPosition = await page.locator('#research-workbench').evaluate((element) => {
      const box = element.getBoundingClientRect();
      return { left: box.left, top: box.top };
    });
    expect(workbenchPosition.top).toBeLessThan(80);
    expect(workbenchPosition.left).toBeGreaterThanOrEqual(0);
    await expectNoHorizontalOverflow(page);

    await page.screenshot({
      path: screenshotPath(testInfo, 'mobile-selected-result-workbench.png'),
      fullPage: false,
    });
  });
});

async function waitForCorpusReady(page: Page) {
  await expect(page.getByRole('heading', { name: 'City Code Research Directory' })).toBeVisible({
    timeout: 15000,
  });
  await expect(page.locator('#search-status')).toContainText(/matches/, { timeout: 30000 });
  await expect(page.getByRole('button', { name: /^Search$/ })).toBeEnabled({ timeout: 30000 });
}

async function expectNoHorizontalOverflow(page: Page) {
  const overflow = await page.evaluate(() => ({
    bodyScrollWidth: document.body.scrollWidth,
    innerWidth: window.innerWidth,
    scrollX: window.scrollX,
    scrollWidth: document.documentElement.scrollWidth,
  }));

  expect(overflow.scrollWidth, JSON.stringify(overflow)).toBeLessThanOrEqual(overflow.innerWidth + 1);
  expect(overflow.bodyScrollWidth, JSON.stringify(overflow)).toBeLessThanOrEqual(overflow.innerWidth + 1);
  expect(overflow.scrollX, JSON.stringify(overflow)).toBeLessThanOrEqual(1);
}

function screenshotPath(testInfo: TestInfo, fileName: string) {
  const projectName = testInfo.project.name.replace(/[^a-z0-9-]+/gi, '-').toLowerCase();
  return path.join(screenshotRoot, projectName, fileName);
}
