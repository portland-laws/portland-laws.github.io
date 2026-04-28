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
    await expect(page.getByLabel('Loaded corpus version')).toContainText('3,052 sections');
    await expect(page.getByLabel('Loaded corpus version')).toContainText('20 artifacts');
    await expect(page.getByLabel('Loaded corpus version')).toContainText(/refreshed [A-Z][a-z]{2} \d{1,2}, 2026/);
    const corpusUsage = await page.evaluate(async () => {
      const manifest = await fetch('/corpus/portland-or/current/artifacts.manifest.json', {
        cache: 'no-store',
      }).then((response) => response.json());
      const resourceUrls = performance
        .getEntriesByType('resource')
        .map((entry) => entry.name)
        .filter((name) => name.includes('/corpus/portland-or/current/'));
      const sectionsUrl = resourceUrls.find((name) => name.includes('/generated/sections.json?')) || '';
      const logicUrl = resourceUrls.find((name) => name.includes('/generated/logic-proof-summaries.json?')) || '';
      return {
        generatedAt: manifest.generatedAt,
        hasFaiss: manifest.generatedFiles.includes('canonical/STATE-OR.faiss'),
        hasRawPages: manifest.generatedFiles.includes('raw/pages.parquet'),
        hasSparkProofs: manifest.generatedFiles.includes(
          'logic_proofs_codex_spark/STATE-OR_logic_proof_artifacts.parquet',
        ),
        sectionsVersion: sectionsUrl ? new URL(sectionsUrl).searchParams.get('v') : null,
        logicVersion: logicUrl ? new URL(logicUrl).searchParams.get('v') : null,
      };
    });
    expect(corpusUsage.hasFaiss).toBe(true);
    expect(corpusUsage.hasRawPages).toBe(true);
    expect(corpusUsage.hasSparkProofs).toBe(true);
    expect(corpusUsage.sectionsVersion).toBe(corpusUsage.generatedAt);
    expect(corpusUsage.logicVersion).toBe(corpusUsage.generatedAt);
    await expect(page.getByRole('navigation', { name: 'City Code' })).toBeVisible();
    await expect(page.getByRole('navigation', { name: 'City Code' }).locator('..')).toContainText('Choose a title');
    await expect(page.getByRole('region', { name: 'Search and Chat' })).toBeVisible();
    await expect(page.getByRole('tab', { name: 'Search code' })).toHaveAttribute('aria-selected', 'true');
    await page.getByRole('tab', { name: 'Chat with code' }).click();
    await expect(page.getByRole('tab', { name: 'Chat with code' })).toHaveAttribute('aria-selected', 'true');
    await expect(page.getByRole('region', { name: 'Chat with Portland City Code' })).toBeVisible();
    await expect(page.getByRole('region', { name: 'Chat with Portland City Code' })).toContainText('Ask the full local corpus');
    await page.getByRole('region', { name: 'Chat with Portland City Code' }).getByRole('button', { name: 'Who is affected by this section?' }).click();
    await expect(page.getByRole('region', { name: 'Chat with Portland City Code' }).getByRole('textbox')).toHaveValue('Who is affected by this section?');
    await page.locator('#code-search').screenshot({
      path: screenshotPath(testInfo, 'desktop-corpus-chat-panel.png'),
    });
    await page.getByRole('region', { name: 'Chat with Portland City Code' }).getByRole('button', { name: /^Ask$/ }).click();
    await expect(page.getByRole('tab', { name: 'Chat', exact: true })).toHaveAttribute('aria-selected', 'true');
    await expect(page.getByLabel('Chat answer')).toBeVisible({ timeout: 30000 });
    await expect(page.getByLabel('Chat answer')).toContainText('Answer with citations');
    await expect(page.locator('body')).not.toContainText('Local model output did not include required citations');
    await expect(page.locator('body')).not.toContainText('Answered from retrieved evidence without local model generation');
    await expect(page.locator('body')).not.toContainText('could not be fully verified');
    await page.getByRole('tab', { name: 'Section' }).click();
    await page.getByRole('tab', { name: 'Search code' }).click();
    await expect(page.getByRole('region', { name: 'Selected section and research tools' })).toBeVisible();
    await expect(page.locator('body')).not.toContainText('GraphRAG');
    await expect(page.locator('body')).not.toContainText('Vector dims');
    await expect(page.locator('body')).not.toContainText('Retrieval');
    await expect(page.getByLabel('Current search filters')).toContainText('"notice requirements"');
    await expect(page.getByRole('button', { name: /^Select / }).first()).toContainText('Selected');
    await expect(page.getByRole('button', { name: /^Select / }).nth(1)).toContainText('Open section');
    await expect(page.getByRole('button', { name: /^Select / }).first()).not.toContainText(/Score \d+\.\d{2}/);
    await expect(page.getByRole('button', { name: /^Select / }).first()).not.toContainText('Proof OK');
    await expect(page.getByRole('button', { name: /^Select / }).first()).not.toContainText('Effect');
    await expect(page.getByRole('button', { name: /^Select / }).first().getByLabel('Structured result preview')).toContainText('A.');
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
    await expect(page.locator('#panel-section')).not.toContainText('Clause A');
    await expect(page.locator('#panel-section').getByLabel('Subsection A')).toHaveCount(1);
    await expect(page.getByLabel('Research actions')).toContainText('Research this section');
    await expect(page.getByRole('button', { name: 'Ask about it' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Related code' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Proof details' })).toBeVisible();
    await page.getByRole('button', { name: 'Related code' }).click();
    await expect(page.getByRole('tab', { name: 'Knowledge Graph' })).toHaveAttribute('aria-selected', 'true');
    await page.getByRole('tab', { name: 'Section' }).click();
    await page.getByRole('button', { name: 'Proof details' }).click();
    await expect(page.getByRole('tab', { name: 'Logic Proofs' })).toHaveAttribute('aria-selected', 'true');
    await page.getByRole('tab', { name: 'Section' }).click();
    await expect(page.getByLabel('Section overview')).toContainText('Subsections');
    await expect(page.getByLabel('Section overview')).toContainText('Official code');
    await expect(page.getByLabel('Section at a glance')).toContainText('At a glance');
    await expect(page.getByLabel('Citation details')).toContainText('Citation');
    await expect(page.getByLabel('Citation details')).toContainText('Chapter');
    await expect(page.getByLabel('Section at a glance')).not.toContainText('Proof OK');
    await expect(page.getByLabel('Section at a glance')).not.toContainText('Effect');
    await expectOfficialSourceButtonIsSingleLine(page);
    await expect(page.getByLabel('Code note')).toBeVisible();

    await page.getByRole('button', { name: 'Ask about it' }).click();
    await expect(page.getByRole('tab', { name: 'Chat', exact: true })).toHaveAttribute('aria-selected', 'true');
    await page.locator('#panel-chat').getByRole('textbox', { name: /Question/ }).fill('What does this section say in simple terms?');
    await page.locator('#panel-chat').getByRole('button', { name: /^Ask$/ }).click();
    await expect(page.getByLabel('Chat answer')).toBeVisible({ timeout: 30000 });
    await expect(page.getByLabel('Chat answer')).toContainText('Answer with citations');
    await expect(page.getByLabel('Chat answer')).not.toContainText('Label:');
    await expect(page.locator('body')).not.toContainText('Local model output did not include required citations');
    await expect(page.locator('body')).not.toContainText('Answered from retrieved evidence without local model generation');
    await expect(page.locator('body')).not.toContainText('could not be fully verified');
    await expect(page.getByLabel('Chat response summary')).toContainText('Sources found');
    await expect(page.getByLabel('Chat response summary')).toContainText('Retrieved code');
    await expect(page.getByLabel('Chat response summary')).toContainText('Portland City Code');
    await expect(page.getByLabel('Chat evidence')).toBeVisible();
    await expect(page.getByLabel('Chat evidence')).toContainText('Official source');
    await expect(page.getByLabel('Chat evidence').getByRole('link').first()).toContainText('Portland City Code 30.01.090');
    await expect(page.getByLabel('Cited answer citations').getByRole('listitem')).toHaveCount(3);
    await expectChatAskButtonIsCompact(page);
    await page.locator('#research-workbench').screenshot({
      path: screenshotPath(testInfo, 'desktop-chat.png'),
    });

    await page.getByRole('tab', { name: 'Knowledge Graph' }).click();
    await expect(page.getByRole('heading', { name: 'Knowledge Graph' })).toBeVisible();
    await expect(page.getByLabel('Graph context summary')).toContainText('Entities');
    await expect(page.getByLabel('Graph context summary')).toContainText('Relationships');
    await expect(page.locator('#panel-graph')).not.toContainText('Graph at a glance');
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
    await expect(page.locator('#panel-proof')).toContainText('Groth16 BN254 proof generated by bundled Rust backend');
    await expect(page.locator('#panel-proof')).not.toContainText('simulated educational certificate');
    await expect(page.locator('#panel-proof')).toContainText('Plain meaning');
    await expect(page.getByLabel('Proof plain meaning details')).toContainText('Time scope');
    await expect(page.getByLabel('Proof reading guide')).toContainText('How to read this proof');
    await expect(page.getByLabel('Proof reading guide')).toContainText('Code effect');
    await expect(page.locator('#panel-proof')).toContainText('DCEC parse');
    await expect(page.locator('#panel-proof')).toContainText('DCEC structure');
    await expect(page.locator('#panel-proof')).not.toContainText('Expected RPAREN');
    await expect(page.locator('#panel-proof')).not.toContainText('Expected LPAREN');
    await expect(page.getByLabel('Logic proof status metrics')).toContainText(/Required|Allowed|Forbidden/);
    await expect(page.getByLabel('DCEC structure summary')).toContainText('Portland City Code');
    await expect(page.getByLabel('DCEC structure summary')).not.toContainText('portland_city_code');
    await expectWorkbenchHasBoundedHeight(page);
    await page.locator('#research-workbench').screenshot({
      path: screenshotPath(testInfo, 'desktop-logic-proofs.png'),
    });

    await expectNoHorizontalOverflow(page);
  });

  test('renders deeply nested legal subsections for renter protections', async ({ page }, testInfo) => {
    await page.getByLabel('Search Portland City Code').fill('30.01.085');
    await page.getByRole('button', { name: /^Search$/ }).click();
    await expect(page.locator('#search-status')).toContainText(/matches/);
    await page.getByRole('button', { name: /^Select / }).first().click();

    await expect(page.locator('#panel-section').getByRole('heading', { name: '30.01.085 Portland Renter Additional Protections.' })).toBeVisible();
    await expect(page.getByLabel('Section overview')).toContainText('Subsections');
    await expect(page.getByLabel('Section overview')).toContainText('12');
    await expect(page.locator('#panel-section')).not.toContainText('Act B. A Landlord');
    await expect(page.locator('#panel-section').getByLabel('Subsection B')).toContainText('A Landlord may terminate');

    const subsectionC = page.locator('#panel-section').getByLabel('Subsection C');
    await expect(subsectionC.locator('[data-outline-depth="1"] > li[data-outline-marker="(a)"]')).toHaveCount(1);
    await expect(subsectionC.locator('[data-outline-depth="1"] > li[data-outline-marker="(b)"]')).toHaveCount(1);
    await expect(subsectionC.locator('[data-outline-depth="2"] > li[data-outline-marker="(i)"]')).toHaveCount(1);
    await expect(subsectionC.locator('[data-outline-depth="2"] > li[data-outline-marker="(ii)"]')).toHaveCount(1);

    const subsectionI = page.locator('#panel-section').getByLabel('Subsection I');
    await expect(subsectionI.locator('[data-outline-depth="1"] > li')).toHaveCount(12);
    await expect(subsectionI.locator('[data-outline-depth="2"] > li[data-outline-marker="a."]')).toHaveCount(1);
    await expect(subsectionI.locator('[data-outline-depth="2"] > li[data-outline-marker="d."]')).toHaveCount(1);

    await page.locator('#research-workbench').screenshot({
      path: screenshotPath(testInfo, 'desktop-renter-protections-outline.png'),
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
    await expect(page.getByRole('tab', { name: 'Chat', exact: true })).toBeFocused();
    await expect(page.getByRole('tab', { name: 'Chat', exact: true })).toHaveAttribute('aria-selected', 'true');
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
    await expect(page.getByRole('navigation', { name: 'Mobile page shortcuts' })).toHaveCount(0);
    await expect(browseTitles).toBeVisible();
    await expect(mobileDirectory).toBeVisible();
    await expect(browseTitles).toContainText('Collapse');
    await expect(page.locator('#code-directory')).toContainText('Choose a title');
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
    await expect(page.getByRole('navigation', { name: 'Mobile page shortcuts' }).getByRole('link', { name: 'Browse titles' })).toBeVisible();
    await expect(page.getByRole('navigation', { name: 'Mobile page shortcuts' }).getByRole('link', { name: 'View results' })).toBeVisible();
    await expect(page.getByLabel('Mobile suggested chat questions').getByRole('button')).toHaveCount(3);
    await page.getByLabel('Mobile suggested chat questions').getByRole('button', { name: 'Who is affected by this section?' }).click();
    await expect(page.getByRole('textbox', { name: 'Ask all Portland City Code' })).toHaveValue('Who is affected by this section?');
    await page.locator('[aria-label="Mobile quick actions"]').screenshot({
      path: screenshotPath(testInfo, 'mobile-front-chat.png'),
    });
    await page.getByRole('region', { name: 'Mobile quick actions' }).getByRole('button', { name: /^Ask$/ }).click();
    await expect(page.getByRole('tab', { name: 'Chat', exact: true })).toHaveAttribute('aria-selected', 'true');

    await page.getByRole('tab', { name: 'Knowledge Graph' }).click();
    await expect(page.getByRole('tab', { name: 'Knowledge Graph' })).toHaveAttribute('aria-selected', 'true');
    await expect(page.getByLabel('Graph context summary')).toContainText('Neighborhood');
    await expect(page.locator('#panel-graph')).not.toContainText('Graph at a glance');
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
    await expect(page.getByRole('button', { name: /^Select / }).nth(1)).toContainText('Open section');
    await expect(page.getByRole('button', { name: /^Select / }).first()).not.toContainText(/Score \d+\.\d{2}/);
    await expect(page.getByRole('button', { name: /^Select / }).first()).not.toContainText('Proof OK');
    await expect(page.getByRole('button', { name: /^Select / }).first()).not.toContainText('Effect');
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
    await expect(page.getByLabel(/Relevance score/)).toHaveCount(0);
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
    await expect(page.locator('#panel-section')).not.toContainText('Clause A');
    await expect(page.locator('#panel-section').getByLabel('Subsection A')).toHaveCount(1);
    await expect(page.locator('#panel-section').getByLabel('Subsection A').getByRole('listitem')).toHaveCount(3);
    await expect(page.locator('#panel-section').getByLabel('Subsection A').getByLabel('Numbered legal requirements')).toBeVisible();
    await expect(page.locator('#panel-section').getByLabel('Subsection C').getByRole('listitem')).toHaveCount(5);
    await expect(page.getByLabel('Research actions')).toContainText('Research this section');
    await expect(page.getByRole('button', { name: 'Ask about it' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Related code' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Proof details' })).toBeVisible();
    await expect(page.getByLabel('Section overview')).toContainText('Subsections');
    await expect(page.getByLabel('Section at a glance')).toContainText('At a glance');
    await expect(page.getByLabel('Citation details')).toContainText('Citation');
    await expect(page.getByLabel('Section at a glance')).not.toContainText('Logic');
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

    await page.getByRole('button', { name: 'Related code' }).click();
    await expect(page.getByRole('tab', { name: 'Knowledge Graph' })).toHaveAttribute('aria-selected', 'true');
    await page.getByRole('tab', { name: 'Section' }).click();
    await page.getByRole('button', { name: 'Proof details' }).click();
    await expect(page.getByRole('tab', { name: 'Logic Proofs' })).toHaveAttribute('aria-selected', 'true');
    await expect(page.locator('#panel-proof')).toContainText('Plain meaning');
    await expect(page.getByLabel('Proof reading guide')).toContainText('Verification');
    await expect(page.locator('#panel-proof')).toContainText('DCEC structure');
    await expect(page.getByLabel('Logic proof status metrics')).toContainText(/Required|Allowed|Forbidden/);
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
