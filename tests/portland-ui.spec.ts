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
    await expect(page.locator('body')).not.toContainText('GraphRAG');
    await expect(page.getByLabel('Current search filters')).toContainText('"notice requirements"');
    await expect(page.getByRole('button', { name: /^Select / }).first()).toContainText('Selected');
    await expect(page.getByRole('button', { name: /^Select / }).first()).toContainText(/Score \d+\.\d{2}/);
    await expect(page.getByRole('button', { name: /^Select / }).first()).toContainText('Proof OK');
    await expect(page.getByRole('button', { name: /^Select / }).first().getByLabel('Structured result preview')).toContainText('Clause A');
    await expect(page.getByRole('button', { name: /^Select / }).first().getByLabel('Preview requirements')).toBeVisible();

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
    await expect(page.getByRole('heading', { name: /Logic Proof Explorer|Code Chat|Knowledge Graph Entities|.+/ }).first()).toBeVisible();

    await page.locator('#research-workbench').screenshot({
      path: screenshotPath(testInfo, 'desktop-section-reader.png'),
    });
    await expect(page.locator('#panel-section')).not.toContainText(/^Label:/);
    await expect(page.locator('#panel-section').getByLabel('Clause A')).toHaveCount(1);
    await expect(page.getByLabel('Section overview')).toContainText('Clauses');
    await expect(page.getByLabel('Section overview')).toContainText('Official code');
    await expectOfficialSourceButtonIsSingleLine(page);
    await expect(page.getByLabel('Code note')).toBeVisible();

    await page.getByRole('tab', { name: 'Chat' }).click();
    await page.locator('#panel-chat').getByRole('textbox', { name: /Question/ }).fill('What does this section say in simple terms?');
    await page.getByRole('button', { name: /^Ask$/ }).click();
    await expect(page.getByLabel('Chat answer')).toBeVisible({ timeout: 30000 });
    await expect(page.getByLabel('Chat answer')).toContainText('Cited answer');
    await expect(page.getByLabel('Chat answer')).not.toContainText('Label:');
    await expect(page.getByLabel('Chat response summary')).toContainText('Evidence sections');
    await expect(page.getByLabel('Chat response summary')).toContainText('Local evidence');
    await expect(page.getByLabel('Chat response summary')).toContainText('Portland City Code');
    await expect(page.getByLabel('Chat evidence')).toBeVisible();
    await expect(page.getByLabel('Chat evidence')).toContainText('Official source');
    await expect(page.getByLabel('Cited answer citations').getByRole('listitem')).toHaveCount(3);
    await expectChatAskButtonIsCompact(page);
    await page.locator('#research-workbench').screenshot({
      path: screenshotPath(testInfo, 'desktop-chat.png'),
    });

    await page.getByRole('tab', { name: 'Knowledge Graph' }).click();
    await expect(page.getByRole('heading', { name: 'Knowledge Graph' })).toBeVisible();
    await expect(page.getByLabel('Graph context summary')).toContainText('Entities');
    await expect(page.getByLabel('Graph context summary')).toContainText('Relationships');
    await expect(page.getByLabel('Graph type summaries')).toContainText('Entity types');
    await expect(page.getByLabel('Entity types summary').getByRole('listitem')).not.toHaveCount(0);
    await expect(page.getByLabel('Relationship types summary').getByRole('listitem')).not.toHaveCount(0);
    await expectGraphContextLoaded(page);
    await expect(page.locator('#panel-graph')).toContainText('This section');
    await expect(page.locator('#panel-graph')).not.toContainText('This section → This section');
    await expect(page.locator('#panel-graph')).not.toContainText('Selected section →');
    await expect(page.locator('#panel-graph')).not.toContainText('authority_grant');
    await page.locator('#research-workbench').screenshot({
      path: screenshotPath(testInfo, 'desktop-knowledge-graph.png'),
    });

    await page.getByRole('tab', { name: 'Logic Proofs' }).click();
    await expect(page.getByRole('heading', { name: 'Logic Proof Explorer' })).toBeVisible();
    await expect(page.getByLabel('Proof reading guide')).toContainText('How to read this proof');
    await expect(page.getByLabel('Proof reading guide')).toContainText('Code effect');
    await expect(page.locator('#panel-proof')).toContainText('DCEC parse');
    await expect(page.locator('#panel-proof')).toContainText('DCEC structure');
    await expect(page.getByLabel('Logic proof status metrics')).toContainText(/Required \(O\)|Allowed \(P\)|Forbidden \(F\)/);
    await expect(page.getByLabel('DCEC structure summary')).toContainText('Portland City Code');
    await expect(page.getByLabel('DCEC structure summary')).not.toContainText('portland_city_code');
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
    await expect(page.getByRole('tab', { name: 'Chat' })).toBeFocused();
    await expect(page.getByRole('tab', { name: 'Chat' })).toHaveAttribute('aria-selected', 'true');
    await expect(page.getByLabel('Chat empty state')).toContainText('No answer yet');
    await expect(page.getByLabel('Suggested chat questions').getByRole('button')).toHaveCount(3);
    await page.getByLabel('Suggested chat questions').getByRole('button', { name: 'Who is affected by this section?' }).click();
    await expect(page.locator('#panel-chat').getByRole('textbox', { name: /Question/ })).toHaveValue('Who is affected by this section?');
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
    await expect(page.getByText('Search the Portland code with graph, proof, and chat tools.')).toBeVisible();
    await expect(page.getByRole('region', { name: 'Mobile quick actions' })).toBeVisible();
    await expect(page.getByRole('region', { name: 'Mobile quick actions' }).getByRole('button', { name: 'Show search' })).toBeVisible();
    await expect(page.getByRole('region', { name: 'Mobile quick actions' }).getByRole('button', { name: 'Show chat' })).toBeVisible();
    await expect(page.getByRole('textbox', { name: 'Search all Portland City Code' })).toBeVisible();
    await expect(page.getByRole('textbox', { name: 'Ask all Portland City Code' })).toHaveCount(0);
    await expect(browseTitles).toBeVisible();
    await expect(mobileDirectory).toBeVisible();
    await expect(browseTitles).toContainText('Collapse');
    await expect(mobileDirectory.getByRole('button', { name: 'Title 1 General Provisions 7 chapters · 43 sections' })).toBeVisible();
    await expectElementBefore(page, '[aria-label="Mobile quick actions"]', '#code-directory');
    await expectElementBefore(page, '#code-directory', '#code-search');
    await browseTitles.click();
    await expect(mobileDirectory).not.toBeVisible();
    await expect(browseTitles).toContainText('Expand');
    await browseTitles.click();
    await expect(mobileDirectory).toBeVisible();
    await expect(browseTitles).toContainText('Collapse');
    await expectMobileFrontPanelRowsAreCompact(page);
    await expectElementTopLessThan(page, '[aria-label="Mobile quick actions"]', 245);
    await expectElementTopLessThan(page, '#code-directory', 360);
    await expectNoHorizontalOverflow(page);
    await page.screenshot({
      path: screenshotPath(testInfo, 'mobile-full-page-stack.png'),
      fullPage: true,
    });

    await page.getByRole('region', { name: 'Mobile quick actions' }).getByRole('button', { name: 'Show chat' }).click();
    await expect(page.getByRole('textbox', { name: 'Ask all Portland City Code' })).toBeVisible();
    await expect(page.getByLabel('Mobile suggested chat questions').getByRole('button')).toHaveCount(3);
    await page.getByLabel('Mobile suggested chat questions').getByRole('button', { name: 'Who is affected by this section?' }).click();
    await expect(page.getByRole('textbox', { name: 'Ask all Portland City Code' })).toHaveValue('Who is affected by this section?');
    await page.locator('[aria-label="Mobile quick actions"]').screenshot({
      path: screenshotPath(testInfo, 'mobile-front-chat.png'),
    });
    await page.getByRole('region', { name: 'Mobile quick actions' }).getByRole('button', { name: /^Ask$/ }).click();
    await expect(page.getByRole('tab', { name: 'Chat' })).toHaveAttribute('aria-selected', 'true');

    await page.getByRole('tab', { name: 'Knowledge Graph' }).click();
    await expect(page.getByRole('tab', { name: 'Knowledge Graph' })).toHaveAttribute('aria-selected', 'true');
    await expect(page.getByLabel('Graph context summary')).toContainText('Neighborhood');
    await expect(page.getByLabel('Graph type summaries')).toContainText('Relationship types');
    await expectGraphContextLoaded(page);
    await expect(page.locator('#panel-graph')).toContainText('This section', { timeout: 10000 });
    await expect(page.locator('#panel-graph')).not.toContainText('authority_grant');
    await expectNoHorizontalOverflow(page);
    await page.locator('#research-workbench').screenshot({
      path: screenshotPath(testInfo, 'mobile-scrollable-tabs-knowledge-graph.png'),
    });
  });

  test('captures mobile search results after filtering', async ({ page }, testInfo) => {
    const mobileFilters = page.locator('summary').filter({ hasText: 'Filters and examples' });
    await mobileFilters.click();
    await page.locator('#code-search details').getByLabel('Title').selectOption('14');
    await expect(page.getByLabel('Current search filters')).toContainText('Title 14');
    await mobileFilters.click();
    await page.getByRole('textbox', { name: 'Search all Portland City Code' }).fill('noise');
    await page.getByRole('button', { name: /^Search$/ }).click();
    await expect(page.locator('#search-status')).toContainText(/matches/);
    await expect(page.getByLabel('Current search filters')).not.toContainText('Title 14');
    await expect(page.getByLabel('Current search filters')).toContainText('"noise"');
    await expect(page.getByRole('button', { name: /^Select / }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /^Select / }).first()).toContainText('Selected');
    await expect(page.getByRole('button', { name: /^Select / }).first()).toContainText(/Score \d+\.\d{2}/);
    await expect(page.getByRole('button', { name: /^Select / }).first()).toContainText('Proof OK');
    await expect(page.getByRole('button', { name: /^Select / }).first().getByLabel('Structured result preview')).toBeVisible();
    await expect(page.getByRole('button', { name: /Show \d+ more results/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /^Select / }).first()).not.toContainText(/^Label:/);
    await expect(mobileFilters).toBeVisible();
    await expect(mobileFilters).toContainText('Expand');
    await mobileFilters.click();
    await expect(mobileFilters).toContainText('Collapse');
    await mobileFilters.click();
    await expect(mobileFilters).toContainText('Expand');
    await expect(page.getByRole('button', { name: 'temporary administrative rules' })).not.toBeVisible();
    await expect(page.getByLabel(/Relevance score/).first()).toBeVisible();
    await expect(page.getByLabel('Current search filters')).toContainText('"noise"');
    await expect(page.locator('#code-search').getByRole('textbox', { name: 'Search Portland City Code' })).toHaveCount(0);
    await expectElementTopLessThan(page, '#search-status', 360);
    await page.getByRole('textbox', { name: 'Search all Portland City Code' }).focus();

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
    await expect(page.locator('#panel-section').getByLabel('Clause A').getByRole('listitem')).toHaveCount(3);
    await expect(page.locator('#panel-section').getByLabel('Clause A').getByLabel('Numbered legal requirements')).toBeVisible();
    await expect(page.locator('#panel-section').getByLabel('Clause C').getByRole('listitem')).toHaveCount(5);
    await expect(page.getByLabel('Section overview')).toContainText('Clauses');
    await expectSectionOverviewUsesThreeColumns(page);

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
    await expect(page.getByLabel('Proof reading guide')).toContainText('Verification');
    await expect(page.locator('#panel-proof')).toContainText('DCEC structure');
    await expect(page.getByLabel('Logic proof status metrics')).toContainText(/Required \(O\)|Allowed \(P\)|Forbidden \(F\)/);
    await expect(page.getByLabel('DCEC structure summary')).toContainText('Portland City Code');
    await expect(page.getByLabel('DCEC structure summary')).not.toContainText('portland_city_code');
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

async function expectGraphContextLoaded(page: Page) {
  await expect(page.getByLabel('Related knowledge graph entities').getByRole('listitem').first()).toBeVisible({
    timeout: 10000,
  });
  await expect(page.getByLabel('Knowledge graph relationships').getByRole('listitem').first()).toBeVisible({
    timeout: 10000,
  });
  await expect(page.locator('#panel-graph')).not.toContainText('Loading graph');
  await expect(page.locator('#panel-graph')).not.toContainText('No related entities loaded');
  await expect(page.locator('#panel-graph')).not.toContainText('No relationships loaded');
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

async function expectSectionOverviewUsesThreeColumns(page: Page) {
  const positions = await page
    .getByLabel('Section overview')
    .locator('> div')
    .evaluateAll((elements) =>
      elements.slice(0, 3).map((element) => {
        const box = element.getBoundingClientRect();
        return { left: box.left, top: box.top };
      }),
    );

  expect(positions).toHaveLength(3);
  expect(Math.abs(positions[0].top - positions[1].top)).toBeLessThan(2);
  expect(Math.abs(positions[1].top - positions[2].top)).toBeLessThan(2);
  expect(positions[1].left).toBeGreaterThan(positions[0].left);
  expect(positions[2].left).toBeGreaterThan(positions[1].left);
}

async function expectOfficialSourceButtonIsSingleLine(page: Page) {
  const dimensions = await page.locator('#panel-section').getByRole('link', { name: /Official source/ }).evaluate((element) => {
    const box = element.getBoundingClientRect();
    return { height: box.height, scrollWidth: element.scrollWidth, clientWidth: element.clientWidth };
  });

  expect(dimensions.height, JSON.stringify(dimensions)).toBeLessThanOrEqual(46);
  expect(dimensions.scrollWidth, JSON.stringify(dimensions)).toBeLessThanOrEqual(dimensions.clientWidth + 1);
}

async function expectChatAskButtonIsCompact(page: Page) {
  const height = await page.locator('#panel-chat').getByRole('button', { name: /^Ask$/ }).evaluate((element) => {
    return element.getBoundingClientRect().height;
  });

  expect(height).toBeLessThanOrEqual(46);
}

async function expectElementTopLessThan(page: Page, selector: string, maxTop: number) {
  const top = await page.locator(selector).evaluate((element) => element.getBoundingClientRect().top);
  expect(top).toBeLessThan(maxTop);
}

async function expectElementBefore(page: Page, firstSelector: string, secondSelector: string) {
  const positions = await page.evaluate(
    ([first, second]) => {
      const firstElement = document.querySelector(first);
      const secondElement = document.querySelector(second);
      return {
        firstTop: firstElement?.getBoundingClientRect().top ?? Number.POSITIVE_INFINITY,
        secondTop: secondElement?.getBoundingClientRect().top ?? Number.NEGATIVE_INFINITY,
      };
    },
    [firstSelector, secondSelector],
  );

  expect(positions.firstTop, JSON.stringify(positions)).toBeLessThan(positions.secondTop);
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

async function expectMobileFrontPanelRowsAreCompact(page: Page) {
  const dimensions = await page
    .getByRole('region', { name: 'Mobile quick actions' })
    .locator('form')
    .evaluate((element) => {
      const input = element.querySelector('input')?.getBoundingClientRect();
      const button = element.querySelector('button')?.getBoundingClientRect();
      return {
        buttonLeft: button?.left ?? 0,
        buttonTop: button?.top ?? 0,
        inputRight: input?.right ?? 0,
        inputTop: input?.top ?? 0,
      };
    });

  expect(Math.abs(dimensions.buttonTop - dimensions.inputTop), JSON.stringify(dimensions)).toBeLessThan(2);
  expect(dimensions.buttonLeft, JSON.stringify(dimensions)).toBeGreaterThan(dimensions.inputRight);
}

function screenshotPath(testInfo: TestInfo, fileName: string) {
  const projectName = testInfo.project.name.replace(/[^a-z0-9-]+/gi, '-').toLowerCase();
  return path.join(screenshotRoot, projectName, fileName);
}
