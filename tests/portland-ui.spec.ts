import { expect, Page, test, TestInfo } from '@playwright/test';
import { mkdirSync } from 'node:fs';
import path from 'node:path';

const screenshotRoot = path.join(process.cwd(), 'tests', 'screenshots', 'portland-ui');

test.beforeAll(() => {
  mkdirSync(screenshotRoot, { recursive: true });
});

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.setItem('PORTLAND_DISABLE_LOCAL_LLM', 'true');
  });
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
    await expect(page.getByLabel('Current search filters')).toContainText('"notice requirements"');
    await expect(page.getByRole('button', { name: /^Select / }).first()).toContainText('Selected');

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
    await expect(page.locator('#panel-section')).not.toContainText(/^Label:/);
    await expect(page.locator('#panel-section').getByLabel('Clause A')).toHaveCount(1);

    await page.getByRole('tab', { name: 'GraphRAG' }).click();
    await page.locator('#panel-chat').getByLabel('Question').fill('What does this section say in simple terms?');
    await page.getByRole('button', { name: /^Ask$/ }).click();
    await expect(page.getByLabel('GraphRAG answer')).toBeVisible({ timeout: 30000 });
    await expect(page.getByLabel('GraphRAG answer')).not.toContainText('Label:');
    await expect(page.getByLabel('GraphRAG evidence')).toBeVisible();
    await page.locator('#research-workbench').screenshot({
      path: screenshotPath(testInfo, 'desktop-graphrag-chat.png'),
    });

    await page.getByRole('tab', { name: 'Knowledge Graph' }).click();
    await expect(page.getByRole('heading', { name: 'Knowledge Graph Entities' })).toBeVisible();
    await expect(page.locator('#panel-graph')).toContainText('Selected section');
    await expect(page.locator('#panel-graph')).not.toContainText('authority_grant');
    await page.locator('#research-workbench').screenshot({
      path: screenshotPath(testInfo, 'desktop-knowledge-graph.png'),
    });

    await page.getByRole('tab', { name: 'Logic Proofs' }).click();
    await expect(page.getByRole('heading', { name: 'Logic Proof Explorer' })).toBeVisible();
    await expect(page.locator('#panel-proof')).toContainText('DCEC parse');
    await expect(page.locator('#panel-proof')).toContainText('DCEC structure');
    await expectWorkbenchHasBoundedHeight(page);
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
    const browseTitles = page.locator('summary').filter({ hasText: 'Browse titles' });
    const mobileDirectory = page.getByRole('navigation', { name: 'City Code mobile' });
    await expect(browseTitles).toBeVisible();
    await expect(mobileDirectory).not.toBeVisible();
    await expect(browseTitles).toContainText('Expand');
    await browseTitles.click();
    await expect(mobileDirectory).toBeVisible();
    await expect(browseTitles).toContainText('Collapse');
    await expect(mobileDirectory.getByRole('button', { name: 'Title 1 General Provisions 7 chapters · 43 sections' })).toBeVisible();
    await browseTitles.click();
    await expect(mobileDirectory).not.toBeVisible();
    await expect(browseTitles).toContainText('Expand');
    await expect(page.getByText('Search the Portland code with graph, proof, and chat tools.')).toBeVisible();
    await expectElementTopLessThan(page, '#code-search', 230);
    await expectNoHorizontalOverflow(page);
    await page.screenshot({
      path: screenshotPath(testInfo, 'mobile-full-page-stack.png'),
      fullPage: true,
    });

    await page.getByRole('tab', { name: 'Knowledge Graph' }).click();
    await expect(page.getByRole('tab', { name: 'Knowledge Graph' })).toHaveAttribute('aria-selected', 'true');
    await expect(page.locator('#panel-graph')).toContainText('Selected section', { timeout: 10000 });
    await expect(page.locator('#panel-graph')).not.toContainText('authority_grant');
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
    await expect(page.getByRole('button', { name: /^Select / }).first()).toContainText('Selected');
    await expect(page.getByRole('button', { name: /Show \d+ more results/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /^Select / }).first()).not.toContainText(/^Label:/);
    const mobileFilters = page.locator('summary').filter({ hasText: 'Filters and examples' });
    await expect(mobileFilters).toBeVisible();
    await expect(mobileFilters).toContainText('Expand');
    await mobileFilters.click();
    await expect(mobileFilters).toContainText('Collapse');
    await mobileFilters.click();
    await expect(mobileFilters).toContainText('Expand');
    await expect(page.getByRole('button', { name: 'temporary administrative rules' })).not.toBeVisible();
    await expect(page.getByLabel(/Relevance score/).first()).toBeVisible();
    await expect(page.getByLabel('Current search filters')).toContainText('"noise"');
    await expectMobileSearchButtonSpansPanel(page);
    await expectElementTopLessThan(page, '#search-status', 520);
    await page.getByLabel('Search Portland City Code').focus();

    await expectNoHorizontalOverflow(page);
    await page.locator('#code-search').screenshot({
      path: screenshotPath(testInfo, 'mobile-search-results.png'),
    });

    await page.getByRole('button', { name: /Show \d+ more results/ }).click();
    await expect(page.locator('#search-status')).toContainText(/showing 12/);
    await page.getByRole('button', { name: 'Clear' }).click();
    await expect(page.getByLabel('Current search filters')).toContainText('All titles and norms');
  });

  test('moves mobile users from a selected result into the research workbench', async ({ page }, testInfo) => {
    await page.getByRole('button', { name: /^Select / }).first().click();
    await expect(page.locator('#panel-section')).toBeFocused();
    await expect(page.locator('#panel-section')).not.toContainText(/^Label:/);
    await expect(page.locator('#panel-section').getByLabel('Clause A')).toHaveCount(1);

    const workbenchPosition = await page.locator('#research-workbench').evaluate((element) => {
      const box = element.getBoundingClientRect();
      return { left: box.left, top: box.top };
    });
    expect(workbenchPosition.top).toBeLessThan(80);
    expect(workbenchPosition.left).toBeGreaterThanOrEqual(0);
    await expectWorkbenchToolbarIsCompact(page);
    await expectWorkbenchTabsFitWithoutHorizontalScroll(page);
    await expectNoHorizontalOverflow(page);

    await page.screenshot({
      path: screenshotPath(testInfo, 'mobile-selected-result-workbench.png'),
      fullPage: false,
    });

    await page.getByRole('tab', { name: 'Logic Proofs' }).click();
    await expect(page.locator('#panel-proof')).toContainText('DCEC structure');
    await expectProofMetricsUseTwoColumns(page);
    await expectNoHorizontalOverflow(page);
    await page.locator('#research-workbench').screenshot({
      path: screenshotPath(testInfo, 'mobile-logic-proofs.png'),
    });

    await page.getByRole('link', { name: 'Back to results' }).click();
    const searchPosition = await page.locator('#code-search').evaluate((element) => {
      const box = element.getBoundingClientRect();
      return { top: box.top };
    });
    expect(searchPosition.top).toBeLessThan(80);
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

async function expectWorkbenchHasBoundedHeight(page: Page) {
  const height = await page.locator('#research-workbench').evaluate((element) => {
    return element.getBoundingClientRect().height;
  });

  expect(height).toBeLessThan(1200);
}

async function expectProofMetricsUseTwoColumns(page: Page) {
  const positions = await page
    .locator('[aria-label="Logic proof status metrics"] > div')
    .evaluateAll((elements) =>
      elements.slice(0, 2).map((element) => {
        const box = element.getBoundingClientRect();
        return { left: box.left, top: box.top };
      }),
    );

  expect(positions).toHaveLength(2);
  expect(Math.abs(positions[0].top - positions[1].top)).toBeLessThan(2);
  expect(positions[1].left).toBeGreaterThan(positions[0].left);
}

async function expectElementTopLessThan(page: Page, selector: string, maxTop: number) {
  const top = await page.locator(selector).evaluate((element) => element.getBoundingClientRect().top);
  expect(top).toBeLessThan(maxTop);
}

async function expectWorkbenchToolbarIsCompact(page: Page) {
  const toolbarHeight = await page.locator('#research-workbench [role="tablist"]').evaluate((element) => {
    return element.getBoundingClientRect().height;
  });

  expect(toolbarHeight).toBeLessThan(54);
}

async function expectWorkbenchTabsFitWithoutHorizontalScroll(page: Page) {
  const tablist = await page.locator('#research-workbench [role="tablist"]').evaluate((element) => ({
    clientWidth: element.clientWidth,
    scrollLeft: element.scrollLeft,
    scrollWidth: element.scrollWidth,
  }));

  expect(tablist.scrollWidth, JSON.stringify(tablist)).toBeLessThanOrEqual(tablist.clientWidth + 1);
  expect(tablist.scrollLeft, JSON.stringify(tablist)).toBeLessThanOrEqual(1);
}

async function expectMobileSearchButtonSpansPanel(page: Page) {
  const dimensions = await page
    .locator('#code-search form > div.sm\\:hidden')
    .evaluate((element) => {
      const container = element.getBoundingClientRect();
      const button = element.querySelector('button')?.getBoundingClientRect();
      return {
        buttonWidth: button?.width ?? 0,
        containerWidth: container.width,
      };
    });

  expect(dimensions.buttonWidth, JSON.stringify(dimensions)).toBeGreaterThan(dimensions.containerWidth - 2);
}

function screenshotPath(testInfo: TestInfo, fileName: string) {
  const projectName = testInfo.project.name.replace(/[^a-z0-9-]+/gi, '-').toLowerCase();
  return path.join(screenshotRoot, projectName, fileName);
}
