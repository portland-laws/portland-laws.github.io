import { FormEvent, KeyboardEvent, useEffect, useMemo, useState } from 'react';
import {
  CorpusEntity,
  CorpusRelationship,
  CorpusSection,
  GraphRagEvidence,
  SearchResult,
  getRelatedGraph,
  loadPortlandCorpus,
  searchCorpus,
} from '../lib/portlandCorpus';
import { clientEmbeddingWorkerService } from '../lib/clientEmbeddingWorkerService';
import { answerWithGraphRag } from '../lib/portlandGraphRag';
import {
  LogicProofSummary,
  NormType,
  explainLogicProofSummary,
  getLogicProofForSection,
  getSimulatedCertificateWarning,
  loadLogicProofIndexes,
} from '../lib/portlandLogic';
import { formatTdfolFormula, parseTdfolFormula } from '../lib/logic/tdfol';

type LoadState = 'loading' | 'ready' | 'error';
type WorkspaceTab = 'section' | 'chat' | 'graph' | 'proof';

interface DirectoryTitle {
  number: string;
  label: string;
  sections: CorpusSection[];
  chapters: DirectoryChapter[];
}

interface DirectoryChapter {
  number: string;
  sections: CorpusSection[];
}

const EXAMPLE_QUERIES = [
  'notice requirements',
  'temporary administrative rules',
  'building permit appeal',
  'business license',
];
const INITIAL_RESULT_LIMIT = 6;
const RESULT_INCREMENT = 6;
const GRAPH_ENTITY_LIMIT = 14;
const GRAPH_RELATIONSHIP_LIMIT = 14;

const TITLE_LABELS: Record<string, string> = {
  '1': 'General Provisions',
  '2': 'Legislation & Elections',
  '3': 'Administration',
  '4': 'Original Art Murals',
  '5': 'Revenue and Finance',
  '6': 'Special Taxes',
  '7': 'Business Licenses',
  '9': 'Protected Sick Time',
  '10': 'Erosion and Sediment Control Regulations',
  '11': 'Trees',
  '12': 'Utility Operators',
  '13': 'Bees and Livestock',
  '14': 'Public Order and Police',
  '15': 'Emergency Code',
  '16': 'Vehicles and Traffic',
  '17': 'Public Improvements',
  '18': 'Noise Control',
  '19': 'Harbors',
  '20': 'Parks and Recreation',
  '21': 'Water',
  '22': 'Hearings Officer',
  '23': 'Civil Rights',
  '24': 'Building Regulations',
  '25': 'Plumbing Regulations',
  '26': 'Electrical Regulations',
  '27': 'Heating and Ventilating Regulations',
  '28': 'Floating Structures',
  '29': 'Property Maintenance Regulations',
  '30': 'Affordable Housing',
  '31': 'Fire Regulations',
  '32': 'Signs and Related Regulations',
  '33': 'Planning and Zoning',
  '34': 'Digital Justice',
  '35': 'Community Police Oversight Board',
};

export default function PortlandLegalResearchApp() {
  const [loadState, setLoadState] = useState<LoadState>('loading');
  const [sections, setSections] = useState<CorpusSection[]>([]);
  const [query, setQuery] = useState('notice requirements');
  const [titleFilter, setTitleFilter] = useState('');
  const [chapterFilter, setChapterFilter] = useState('');
  const [normFilter, setNormFilter] = useState<NormType | ''>('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [proofByCid, setProofByCid] = useState<Map<string, LogicProofSummary>>(new Map());
  const [selectedCid, setSelectedCid] = useState<string | null>(null);
  const [selectedProof, setSelectedProof] = useState<LogicProofSummary | null>(null);
  const [relatedEntities, setRelatedEntities] = useState<CorpusEntity[]>([]);
  const [relatedRelationships, setRelatedRelationships] = useState<CorpusRelationship[]>([]);
  const [activeTab, setActiveTab] = useState<WorkspaceTab>('section');
  const [isSearching, setIsSearching] = useState(false);
  const [retrievalMode, setRetrievalMode] = useState<'Hybrid' | 'Keyword'>('Keyword');
  const [error, setError] = useState<string | null>(null);
  const [chatQuestion, setChatQuestion] = useState('What does the code say about notice requirements?');
  const [chatAnswer, setChatAnswer] = useState('');
  const [chatEvidence, setChatEvidence] = useState<GraphRagEvidence | null>(null);
  const [chatWarning, setChatWarning] = useState<string | null>(null);
  const [isAnswering, setIsAnswering] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [corpus, logicIndexes] = await Promise.all([
          loadPortlandCorpus(),
          loadLogicProofIndexes(),
        ]);
        if (cancelled) return;
        setSections(corpus.sections);
        setProofByCid(logicIndexes.proofByCid);
        setLoadState('ready');
      } catch (err) {
        if (cancelled) return;
        setLoadState('error');
        setError(err instanceof Error ? err.message : 'Unable to load Portland corpus');
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (loadState !== 'ready') return;
    void runSearch(query, titleFilter, chapterFilter, normFilter);
    // Run the initial search once after corpus load.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadState]);

  useEffect(() => {
    let cancelled = false;

    async function loadSelectedContext() {
      if (!selectedCid) {
        setRelatedEntities([]);
        setRelatedRelationships([]);
        setSelectedProof(null);
        return;
      }
      try {
        const [related, proof] = await Promise.all([
          getRelatedGraph(selectedCid, 1),
          getLogicProofForSection(selectedCid),
        ]);
        if (!cancelled) {
          setRelatedEntities(
            related.entities
              .filter((entity) => entity.id !== selectedCid)
              .sort((left, right) => left.type.localeCompare(right.type) || left.label.localeCompare(right.label))
              .slice(0, 28),
          );
          setRelatedRelationships(related.relationships.slice(0, 36));
          setSelectedProof(proof);
        }
      } catch (err) {
        if (!cancelled) {
          console.warn('Failed to load selected section context', err);
          setRelatedEntities([]);
          setRelatedRelationships([]);
          setSelectedProof(null);
        }
      }
    }

    loadSelectedContext();
    return () => {
      cancelled = true;
    };
  }, [selectedCid]);

  const directory = useMemo(() => buildDirectory(sections), [sections]);
  const selected = useMemo(() => {
    if (!selectedCid) return results[0]?.section || sections[0] || null;
    return results.find((result) => result.ipfs_cid === selectedCid)?.section
      || sections.find((section) => section.ipfs_cid === selectedCid)
      || null;
  }, [results, sections, selectedCid]);
  const visibleChapters = useMemo(
    () => directory.find((title) => title.number === titleFilter)?.chapters || [],
    [directory, titleFilter],
  );

  async function runSearch(
    nextQuery = query,
    nextTitleFilter = titleFilter,
    nextChapterFilter = chapterFilter,
    nextNormFilter: NormType | '' = normFilter,
  ) {
    if (!nextQuery.trim()) {
      const browsedSections = filterDirectorySections(sections, nextTitleFilter, nextChapterFilter).slice(0, 30);
      setResults(browsedSections.map(sectionToResult));
      setSelectedCid(browsedSections[0]?.ipfs_cid || null);
      return;
    }

    setIsSearching(true);
    setError(null);
    try {
      let queryEmbedding: Float32Array | undefined;
      let mode: 'hybrid' | 'keyword' = 'keyword';

      try {
        queryEmbedding = await clientEmbeddingWorkerService.generateEmbedding(nextQuery);
        mode = 'hybrid';
        setRetrievalMode('Hybrid');
      } catch (err) {
        console.warn('Vector embedding unavailable, using keyword search', err);
        setRetrievalMode('Keyword');
      }

      const nextResults = await searchCorpus(
        nextQuery,
        { titleNumber: nextTitleFilter || undefined, limit: nextNormFilter || nextChapterFilter ? 140 : 40 },
        mode,
        queryEmbedding,
      );
      const filteredResults = nextResults.filter((result) => {
        if (nextChapterFilter && getChapterNumber(result.section) !== nextChapterFilter) {
          return false;
        }
        if (nextNormFilter && proofByCid.get(result.ipfs_cid)?.norm_type !== nextNormFilter) {
          return false;
        }
        return true;
      });
      const limitedResults = filteredResults.slice(0, 40);
      setResults(limitedResults);
      setSelectedCid(limitedResults[0]?.ipfs_cid || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setIsSearching(false);
    }
  }

  function selectDirectoryTitle(titleNumber: string) {
    const nextTitle = titleFilter === titleNumber ? '' : titleNumber;
    setTitleFilter(nextTitle);
    setChapterFilter('');
    setQuery('');
    void runSearch('', nextTitle, '', normFilter);
  }

  function selectDirectoryChapter(titleNumber: string, chapterNumber: string) {
    setTitleFilter(titleNumber);
    setChapterFilter(chapterNumber);
    setQuery('');
    void runSearch('', titleNumber, chapterNumber, normFilter);
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void runSearch();
  }

  async function onAskQuestion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!chatQuestion.trim()) return;

    setActiveTab('chat');
    setIsAnswering(true);
    setChatWarning(null);
    try {
      const response = await answerWithGraphRag(chatQuestion);
      setChatAnswer(response.answer);
      setChatEvidence(response.evidence);
      setChatWarning(
        response.warning || (response.usedLocalModel ? null : 'Answered from retrieved evidence without local model generation.'),
      );
    } catch (err) {
      setChatWarning(err instanceof Error ? err.message : 'Unable to answer that question.');
      setChatAnswer('');
      setChatEvidence(null);
    } finally {
      setIsAnswering(false);
    }
  }

  return (
    <main className="min-h-screen bg-[#f3f5ef] text-[#1f2933] font-system">
      <nav className="skip-links" aria-label="Skip links">
        <a href="#code-directory">Skip to code directory</a>
        <a href="#code-search">Skip to search</a>
        <a href="#research-workbench">Skip to selected section and research tools</a>
      </nav>
      <Header sections={sections} retrievalMode={retrievalMode} />

      <div
        id="main-content"
        className="mx-auto grid max-w-[1520px] gap-3 px-3 py-3 sm:gap-4 sm:px-4 sm:py-4 lg:grid-cols-[300px_minmax(360px,480px)_1fr]"
      >
        <DirectoryPanel
          directory={directory}
          selectedTitle={titleFilter}
          selectedChapter={chapterFilter}
          onSelectTitle={selectDirectoryTitle}
          onSelectChapter={selectDirectoryChapter}
        />

        <SearchPanel
          query={query}
          titleFilter={titleFilter}
          chapterFilter={chapterFilter}
          normFilter={normFilter}
          directory={directory}
          visibleChapters={visibleChapters}
          results={results}
          selectedCid={selected?.ipfs_cid || null}
          proofByCid={proofByCid}
          loadState={loadState}
          isSearching={isSearching}
          error={error}
          onQueryChange={setQuery}
          onTitleChange={(value) => {
            setTitleFilter(value);
            setChapterFilter('');
            void runSearch(query, value, '', normFilter);
          }}
          onChapterChange={(value) => {
            setChapterFilter(value);
            void runSearch(query, titleFilter, value, normFilter);
          }}
          onNormChange={(value) => {
            setNormFilter(value);
            void runSearch(query, titleFilter, chapterFilter, value);
          }}
          onSubmit={onSubmit}
          onSelectResult={(cid) => {
            setSelectedCid(cid);
            setActiveTab('section');
            if (window.matchMedia('(max-width: 1023px)').matches) {
              window.requestAnimationFrame(() => {
                const workbench = document.getElementById('research-workbench');
                const targetTop = workbench
                  ? window.scrollY + workbench.getBoundingClientRect().top
                  : window.scrollY;
                window.scrollTo({ left: 0, top: Math.max(targetTop, 0) });
                document.getElementById('panel-section')?.focus({ preventScroll: true });
                window.requestAnimationFrame(() => {
                  window.scrollTo({ left: 0, top: window.scrollY });
                });
              });
            }
          }}
          onExample={(example) => {
            setQuery(example);
            void runSearch(example, titleFilter, chapterFilter, normFilter);
          }}
        />

        <WorkspacePanel
          selected={selected}
          proof={selectedProof}
          relatedEntities={relatedEntities}
          relatedRelationships={relatedRelationships}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          chatQuestion={chatQuestion}
          chatAnswer={chatAnswer}
          chatEvidence={chatEvidence}
          chatWarning={chatWarning}
          isAnswering={isAnswering}
          onQuestionChange={setChatQuestion}
          onAskQuestion={onAskQuestion}
        />
      </div>
    </main>
  );
}

function Header({ sections, retrievalMode }: { sections: CorpusSection[]; retrievalMode: string }) {
  return (
    <header className="border-b border-[#d3d8cf] bg-[#fbfcf8]">
      <div className="mx-auto flex max-w-[1520px] flex-col gap-4 px-3 py-4 sm:px-4 sm:py-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#4f6f52]">
            Portland, Oregon
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-normal text-[#172026] sm:text-4xl">
            City Code Research Directory
          </h1>
          <p className="mt-2 max-w-3xl text-base leading-7 text-[#43534d]">
            Browse Titles, Chapters, and Sections like the official code directory, with client-side
            GraphRAG search, knowledge graph context, logic proofs, and corpus chat layered in.
          </p>
        </div>
        <div className="grid grid-cols-3 gap-2 text-sm sm:gap-3">
          <Metric label="Sections" value={sections.length ? sections.length.toLocaleString() : '...'} />
          <Metric label="Vector dims" value="384" />
          <Metric label="Search" value={retrievalMode} />
        </div>
      </div>
    </header>
  );
}

function DirectoryPanel({
  directory,
  selectedTitle,
  selectedChapter,
  onSelectTitle,
  onSelectChapter,
}: {
  directory: DirectoryTitle[];
  selectedTitle: string;
  selectedChapter: string;
  onSelectTitle: (titleNumber: string) => void;
  onSelectChapter: (titleNumber: string, chapterNumber: string) => void;
}) {
  return (
    <nav
      id="code-directory"
      aria-labelledby="code-directory-heading"
      className="min-w-0 max-h-[48vh] overflow-auto rounded-md border border-[#d8dfd3] bg-white shadow-sm lg:sticky lg:top-4 lg:max-h-[calc(100vh-2rem)]"
    >
      <div className="border-b border-[#e1e6dc] px-4 py-4">
        <h2 id="code-directory-heading" className="text-lg font-semibold text-[#172026]">
          City Code
        </h2>
        <p className="mt-1 text-sm leading-6 text-[#4f615b]">Titles, Chapters, and Sections</p>
      </div>
      <ul className="divide-y divide-[#edf1e8]">
        {directory.map((title) => (
          <li key={title.number} className="px-3 py-2">
            <button
              type="button"
              onClick={() => onSelectTitle(title.number)}
              aria-expanded={selectedTitle === title.number}
              aria-controls={`title-${title.number}-chapters`}
              className={`min-h-12 w-full rounded-md px-3 py-2 text-left transition ${
                selectedTitle === title.number ? 'bg-[#e8f0e8]' : 'hover:bg-[#f6f8f3]'
              }`}
            >
              <div className="text-sm font-semibold text-[#24594f]">Title {title.number}</div>
              <div className="mt-0.5 text-sm leading-5 text-[#26343a]">{title.label}</div>
              <div className="mt-1 text-xs text-[#66756f]">
                {title.chapters.length} chapters · {title.sections.length} sections
              </div>
            </button>
            {selectedTitle === title.number && (
              <ul id={`title-${title.number}-chapters`} className="mt-2 space-y-1 pl-3">
                {title.chapters.slice(0, 30).map((chapter) => (
                  <li key={chapter.number}>
                    <button
                      type="button"
                      onClick={() => onSelectChapter(title.number, chapter.number)}
                      aria-current={selectedChapter === chapter.number ? 'true' : undefined}
                      className={`block min-h-11 w-full rounded-md px-3 py-2 text-left text-sm ${
                        selectedChapter === chapter.number
                          ? 'bg-[#24594f] text-white'
                          : 'text-[#394a4f] hover:bg-[#f2f5ee]'
                      }`}
                    >
                      Chapter {chapter.number}
                      <span className="ml-2 text-xs opacity-75">({chapter.sections.length})</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ul>
    </nav>
  );
}

function SearchPanel({
  query,
  titleFilter,
  chapterFilter,
  normFilter,
  directory,
  visibleChapters,
  results,
  selectedCid,
  proofByCid,
  loadState,
  isSearching,
  error,
  onQueryChange,
  onTitleChange,
  onChapterChange,
  onNormChange,
  onSubmit,
  onSelectResult,
  onExample,
}: {
  query: string;
  titleFilter: string;
  chapterFilter: string;
  normFilter: NormType | '';
  directory: DirectoryTitle[];
  visibleChapters: DirectoryChapter[];
  results: SearchResult[];
  selectedCid: string | null;
  proofByCid: Map<string, LogicProofSummary>;
  loadState: LoadState;
  isSearching: boolean;
  error: string | null;
  onQueryChange: (query: string) => void;
  onTitleChange: (title: string) => void;
  onChapterChange: (chapter: string) => void;
  onNormChange: (norm: NormType | '') => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onSelectResult: (cid: string) => void;
  onExample: (query: string) => void;
}) {
  const [resultLimit, setResultLimit] = useState(INITIAL_RESULT_LIMIT);
  const selectedIndex = results.findIndex((result) => result.ipfs_cid === selectedCid);
  const visibleLimit = Math.max(resultLimit, selectedIndex >= 0 ? selectedIndex + 1 : INITIAL_RESULT_LIMIT);
  const visibleResults = results.slice(0, visibleLimit);
  const hiddenResultCount = Math.max(results.length - visibleResults.length, 0);

  useEffect(() => {
    setResultLimit(INITIAL_RESULT_LIMIT);
  }, [results]);

  return (
    <section
      id="code-search"
      aria-labelledby="code-search-heading"
      className="min-w-0 rounded-md border border-[#d8dfd3] bg-[#fbfcf8] shadow-sm"
    >
      <div className="border-b border-[#e1e6dc] px-4 py-4">
        <h2 id="code-search-heading" className="text-lg font-semibold text-[#172026]">
          Find Code Sections
        </h2>
        <p className="mt-1 text-sm leading-6 text-[#4f615b]">Keyword, vector, graph, and proof-aware retrieval</p>
      </div>

      <form onSubmit={onSubmit} className="grid gap-3 border-b border-[#e1e6dc] px-4 py-4" aria-label="Search and filter code sections">
        <label className="block">
          <span className="mb-1 block text-sm font-semibold text-[#26343a]">Search Portland City Code</span>
          <input
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            aria-describedby="search-help"
            className="h-12 w-full rounded-md border border-[#8fa08a] bg-white px-4 text-base text-[#172026] shadow-sm transition"
            placeholder="Search code sections"
          />
          <span id="search-help" className="mt-1 block text-sm leading-6 text-[#4f615b]">
            Search by words, citation, topic, or a plain-language question.
          </span>
        </label>

        <div className="grid gap-3 sm:grid-cols-2">
          <Select value={titleFilter} onChange={onTitleChange} label="Title">
            <option value="">All titles</option>
            {directory.map((title) => (
              <option key={title.number} value={title.number}>
                Title {title.number}
              </option>
            ))}
          </Select>
          <Select value={chapterFilter} onChange={onChapterChange} label="Chapter" disabled={!titleFilter}>
            <option value="">All chapters</option>
            {visibleChapters.map((chapter) => (
              <option key={chapter.number} value={chapter.number}>
                Chapter {chapter.number}
              </option>
            ))}
          </Select>
        </div>

        <div className="grid gap-3 sm:grid-cols-[1fr_120px]">
          <Select value={normFilter} onChange={(value) => onNormChange(value as NormType | '')} label="Norm">
            <option value="">All norms</option>
            <option value="obligation">Obligations</option>
            <option value="permission">Permissions</option>
            <option value="prohibition">Prohibitions</option>
            <option value="unknown">Unknown norms</option>
          </Select>
          <button
            type="submit"
            disabled={loadState !== 'ready' || isSearching}
            aria-describedby="search-status"
            className="min-h-11 rounded-md bg-[#24594f] px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-[#1d473f] disabled:cursor-not-allowed disabled:bg-[#8aa19b]"
          >
            {isSearching ? 'Searching' : 'Search'}
          </button>
        </div>

        <div className="flex flex-wrap gap-2">
          {EXAMPLE_QUERIES.map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => onExample(example)}
              className="min-h-11 rounded-md border border-[#aab8a4] bg-white px-3 py-2 text-sm text-[#30413f] hover:border-[#49635a]"
            >
              {example}
            </button>
          ))}
        </div>
      </form>

      <div className="px-4 py-4">
        <div className="mb-3 flex items-center justify-between gap-3">
          <h3 className="text-base font-semibold text-[#172026]">Results</h3>
          <span id="search-status" role="status" aria-live="polite" className="text-sm text-[#4f615b]">
            {loadState === 'ready'
              ? hiddenResultCount > 0
                ? `${results.length} matches, showing ${visibleResults.length}`
                : `${results.length} matches`
              : 'Loading corpus'}
          </span>
        </div>

        {error && (
          <div className="mb-3 rounded-md border border-[#d89b82] bg-[#fff4ef] px-3 py-2 text-sm text-[#8a3b22]">
            {error}
          </div>
        )}
        {loadState === 'loading' && <EmptyState title="Loading Portland code corpus" />}
        {loadState === 'error' && <EmptyState title="Corpus assets could not be loaded" />}
        {loadState === 'ready' && results.length === 0 && <EmptyState title="No matching sections" />}

        <div
          className="space-y-3"
          aria-label={`Search results${hiddenResultCount > 0 ? ` showing top ${visibleResults.length} of ${results.length}` : ''}`}
        >
          {visibleResults.map((result) => (
            <ResultCard
              key={result.ipfs_cid}
              result={result}
              proof={proofByCid.get(result.ipfs_cid) || null}
              selected={selectedCid === result.ipfs_cid}
              onSelect={() => onSelectResult(result.ipfs_cid)}
            />
          ))}
        </div>
        {hiddenResultCount > 0 && (
          <div className="mt-3 rounded-md border border-[#dce3d6] bg-white px-3 py-3">
            <p className="text-sm leading-6 text-[#4f615b]">
              Showing {visibleResults.length} strong matches. Refine the search or filters to narrow the remaining{' '}
              {hiddenResultCount.toLocaleString()} results.
            </p>
            <button
              type="button"
              onClick={() => setResultLimit((current) => Math.min(current + RESULT_INCREMENT, results.length))}
              className="mt-2 min-h-11 rounded-md border border-[#8fa08a] px-3 text-sm font-semibold text-[#24594f] hover:bg-[#f3f6ef]"
            >
              Show {Math.min(RESULT_INCREMENT, hiddenResultCount)} more results
            </button>
          </div>
        )}
      </div>
    </section>
  );
}

function WorkspacePanel({
  selected,
  proof,
  relatedEntities,
  relatedRelationships,
  activeTab,
  setActiveTab,
  chatQuestion,
  chatAnswer,
  chatEvidence,
  chatWarning,
  isAnswering,
  onQuestionChange,
  onAskQuestion,
}: {
  selected: CorpusSection | null;
  proof: LogicProofSummary | null;
  relatedEntities: CorpusEntity[];
  relatedRelationships: CorpusRelationship[];
  activeTab: WorkspaceTab;
  setActiveTab: (tab: WorkspaceTab) => void;
  chatQuestion: string;
  chatAnswer: string;
  chatEvidence: GraphRagEvidence | null;
  chatWarning: string | null;
  isAnswering: boolean;
  onQuestionChange: (question: string) => void;
  onAskQuestion: (event: FormEvent<HTMLFormElement>) => void;
}) {
  const tabs: Array<{ tab: WorkspaceTab; label: string; shortLabel: string }> = [
    { tab: 'section', label: 'Section', shortLabel: 'Section' },
    { tab: 'chat', label: 'GraphRAG', shortLabel: 'GraphRAG' },
    { tab: 'graph', label: 'Knowledge Graph', shortLabel: 'Graph' },
    { tab: 'proof', label: 'Logic Proofs', shortLabel: 'Proofs' },
  ];
  const activeIndex = tabs.findIndex((item) => item.tab === activeTab);

  function onTabKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) {
      return;
    }
    event.preventDefault();
    const lastIndex = tabs.length - 1;
    const nextIndex =
      event.key === 'Home'
        ? 0
        : event.key === 'End'
          ? lastIndex
          : event.key === 'ArrowRight'
            ? (activeIndex + 1) % tabs.length
            : (activeIndex - 1 + tabs.length) % tabs.length;
    const nextTab = tabs[nextIndex].tab;
    setActiveTab(nextTab);
    window.requestAnimationFrame(() => {
      document.getElementById(`tab-${nextTab}`)?.focus();
    });
  }

  return (
    <section
      id="research-workbench"
      aria-labelledby="research-workbench-heading"
      className="min-w-0 rounded-md border border-[#d8dfd3] bg-white shadow-sm"
    >
      <div className="border-b border-[#e1e6dc] px-4 pt-4">
        <h2 id="research-workbench-heading" className="sr-only">
          Selected section and research tools
        </h2>
        <a
          href="#code-search"
          className="mb-3 inline-flex min-h-11 items-center rounded-md border border-[#8fa08a] px-3 text-sm font-semibold text-[#24594f] hover:bg-[#f3f6ef] lg:hidden"
        >
          Back to results
        </a>
        <div className="flex gap-1.5 overflow-x-auto pb-px sm:gap-2" role="tablist" aria-label="Research workspace panels">
          {tabs.map(({ tab, label, shortLabel }) => (
            <button
              id={`tab-${tab}`}
              key={tab}
              type="button"
              role="tab"
              aria-label={label}
              aria-selected={activeTab === tab}
              aria-controls={`panel-${tab}`}
              tabIndex={activeTab === tab ? 0 : -1}
              onClick={() => setActiveTab(tab as WorkspaceTab)}
              onKeyDown={onTabKeyDown}
              title={label}
              className={`min-h-11 shrink-0 rounded-t-md border border-b-0 px-2 py-2 text-xs font-semibold sm:px-3 sm:text-sm ${
                activeTab === tab
                  ? 'border-[#d8dfd3] bg-white text-[#24594f]'
                  : 'border-transparent bg-[#eef2ea] text-[#596861] hover:text-[#24594f]'
              }`}
            >
              <span className="sm:hidden">{shortLabel}</span>
              <span className="hidden sm:inline">{label}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="min-h-[420px] lg:min-h-[560px]" aria-live="polite">
        {!selected && <EmptyState title="Select a section" />}
        {selected && activeTab === 'section' && (
          <div id="panel-section" role="tabpanel" aria-labelledby="tab-section" tabIndex={0}>
            <SectionReader section={selected} />
          </div>
        )}
        {selected && activeTab === 'chat' && (
          <div id="panel-chat" role="tabpanel" aria-labelledby="tab-chat" tabIndex={0}>
            <GraphRagChat
              question={chatQuestion}
              answer={chatAnswer}
              evidence={chatEvidence}
              warning={chatWarning}
              isAnswering={isAnswering}
              onQuestionChange={onQuestionChange}
              onSubmit={onAskQuestion}
            />
          </div>
        )}
        {selected && activeTab === 'graph' && (
          <div id="panel-graph" role="tabpanel" aria-labelledby="tab-graph" tabIndex={0}>
            <GraphPanel entities={relatedEntities} relationships={relatedRelationships} />
          </div>
        )}
        {selected && activeTab === 'proof' && (
          <div id="panel-proof" role="tabpanel" aria-labelledby="tab-proof" tabIndex={0}>
            <ProofPanel proof={proof} />
          </div>
        )}
      </div>
    </section>
  );
}

function Select({
  value,
  onChange,
  label,
  disabled,
  children,
}: {
  value: string;
  onChange: (value: string) => void;
  label: string;
  disabled?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-[#607068]">{label}</span>
      <select
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        className="min-h-11 w-full rounded-md border border-[#8fa08a] bg-white px-3 text-sm text-[#172026] shadow-sm transition disabled:bg-[#eef2ea]"
      >
        {children}
      </select>
    </label>
  );
}

function ResultCard({
  result,
  proof,
  selected,
  onSelect,
}: {
  result: SearchResult;
  proof: LogicProofSummary | null;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
      aria-label={`Select ${result.citation}: ${result.section.title}`}
      className={`block min-h-12 w-full rounded-md border bg-white p-4 text-left shadow-sm transition hover:border-[#49635a] ${
        selected ? 'border-[#24594f] ring-2 ring-[#24594f]/15' : 'border-[#dde3d8]'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-semibold text-[#24594f]">{result.citation}</p>
          <h3 className="mt-1 text-base font-semibold leading-snug text-[#172026] [overflow-wrap:anywhere]">
            {result.section.title}
          </h3>
        </div>
        <span className="shrink-0 rounded-md bg-[#eef2ea] px-2 py-1 text-xs font-semibold text-[#4d625b]">
          {result.score.toFixed(2)}
        </span>
      </div>

      {proof && (
        <div className="mt-3 flex flex-wrap gap-2">
          <ResultBadge label={proof.norm_type} />
          <ResultBadge label={formatNormOperatorForBadge(proof.norm_operator)} />
          <ResultBadge label={formatProofStatusForBadge(proof.deontic_status)} />
        </div>
      )}
      <p className="mt-3 line-clamp-3 text-sm leading-6 text-[#52615c] [overflow-wrap:anywhere]">{result.snippet}</p>
    </button>
  );
}

function ResultBadge({ label }: { label: string }) {
  return (
    <span className="rounded-md border border-[#d4ddd0] bg-[#f8faf5] px-2 py-1 text-xs font-semibold text-[#53655f]">
      {label}
    </span>
  );
}

function formatNormOperatorForBadge(operator: string) {
  const normalized = operator.toUpperCase();
  if (normalized === 'O') return 'required';
  if (normalized === 'P') return 'allowed';
  if (normalized === 'F') return 'forbidden';
  return operator;
}

function formatProofStatusForBadge(status: string) {
  if (status === 'success') return 'proof ok';
  if (status === 'warning') return 'needs review';
  if (status === 'error') return 'proof error';
  return status.replace(/_/g, ' ');
}

function GraphRagChat({
  question,
  answer,
  evidence,
  warning,
  isAnswering,
  onQuestionChange,
  onSubmit,
}: {
  question: string;
  answer: string;
  evidence: GraphRagEvidence | null;
  warning: string | null;
  isAnswering: boolean;
  onQuestionChange: (question: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <div className="px-4 py-4 sm:px-5 sm:py-5">
      <div className="mb-4">
        <h2 className="text-xl font-semibold tracking-normal text-[#172026]">GraphRAG Chat</h2>
        <p className="mt-1 text-base leading-7 text-[#4f615b]">Ask questions grounded in local Portland City Code evidence.</p>
      </div>
      <form onSubmit={onSubmit} className="grid gap-3 md:grid-cols-[1fr_112px]">
        <label className="block">
          <span className="mb-1 block text-sm font-semibold text-[#26343a]">Question</span>
          <input
            value={question}
            onChange={(event) => onQuestionChange(event.target.value)}
            aria-describedby="chat-help"
            className="min-h-11 w-full rounded-md border border-[#8fa08a] bg-white px-3 text-sm text-[#172026] shadow-sm transition"
            placeholder="Ask about the Portland City Code"
          />
          <span id="chat-help" className="mt-1 block text-sm leading-6 text-[#4f615b]">
            Answers are informational and cite retrieved code sections.
          </span>
        </label>
        <button
          type="submit"
          disabled={isAnswering}
          className="min-h-11 rounded-md bg-[#24594f] px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-[#1d473f] disabled:cursor-not-allowed disabled:bg-[#8aa19b]"
        >
          {isAnswering ? 'Asking' : 'Ask'}
        </button>
      </form>

      {warning && (
        <div role="status" className="mt-4 rounded-md border border-[#d6c28e] bg-[#fff9e8] px-3 py-2 text-sm text-[#735b18]">
          {warning}
        </div>
      )}
      {answer && (
        <div
          className="mt-4 rounded-md border border-[#dce3d6] bg-[#f8faf5] px-4 py-4"
          aria-label="GraphRAG answer"
          aria-live="polite"
        >
          <div className="whitespace-pre-wrap text-sm leading-6 text-[#26343a] [overflow-wrap:anywhere]">{answer}</div>
        </div>
      )}
      {evidence && evidence.sections.length > 0 && (
        <div className="mt-4" aria-label="GraphRAG evidence">
          <h3 className="text-sm font-semibold uppercase tracking-[0.14em] text-[#607068]">Evidence</h3>
          <div className="mt-2 grid gap-2">
            {evidence.sections.slice(0, 5).map((result, index) => (
              <a
                key={result.ipfs_cid}
                href={result.section.source_url}
                target="_blank"
                rel="noreferrer"
                className="rounded-md border border-[#dce3d6] bg-white px-3 py-2 text-sm hover:border-[#7a9487]"
              >
                <span className="font-semibold text-[#24594f]">[{index + 1}] {result.citation}</span>
                <span className="ml-2 text-[#394a4f] [overflow-wrap:anywhere]">{result.section.title}</span>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function GraphPanel({
  entities,
  relationships,
}: {
  entities: CorpusEntity[];
  relationships: CorpusRelationship[];
}) {
  const visibleEntities = entities.slice(0, GRAPH_ENTITY_LIMIT);
  const hiddenEntityCount = Math.max(entities.length - visibleEntities.length, 0);
  const visibleRelationships = relationships.slice(0, GRAPH_RELATIONSHIP_LIMIT);
  const hiddenRelationshipCount = Math.max(relationships.length - visibleRelationships.length, 0);

  return (
    <div className="grid gap-5 px-4 py-4 sm:px-5 sm:py-5 xl:grid-cols-[1fr_1fr]">
      <div>
        <h2 className="text-xl font-semibold tracking-normal text-[#172026]">Knowledge Graph Entities</h2>
        <div className="mt-3 grid gap-2" role="list" aria-label="Related knowledge graph entities">
          {entities.length === 0 && <EmptyState title="No related entities loaded" />}
          {visibleEntities.map((entity) => (
            <div key={entity.id} role="listitem" className="rounded-md border border-[#dce3d6] bg-[#fbfcf8] px-3 py-2">
              <div className="text-xs font-semibold uppercase tracking-wide text-[#5f7469]">{formatGraphTypeLabel(entity.type)}</div>
              <div className="mt-1 text-sm font-medium leading-5 text-[#223035] [overflow-wrap:anywhere]">{entity.label}</div>
            </div>
          ))}
        </div>
        {hiddenEntityCount > 0 && (
          <p className="mt-3 rounded-md border border-[#dce3d6] bg-white px-3 py-2 text-sm leading-6 text-[#4f615b]">
            Showing {visibleEntities.length} of {entities.length} related entities.
          </p>
        )}
      </div>
      <div>
        <h2 className="text-xl font-semibold tracking-normal text-[#172026]">Relationships</h2>
        <div className="mt-3 grid gap-2" role="list" aria-label="Knowledge graph relationships">
          {relationships.length === 0 && <EmptyState title="No relationships loaded" />}
          {visibleRelationships.map((relationship) => (
            <div key={relationship.id} role="listitem" className="rounded-md border border-[#dce3d6] bg-white px-3 py-2">
              <div className="text-xs font-semibold uppercase tracking-wide text-[#5f7469]">
                {formatGraphTypeLabel(relationship.type)}
              </div>
              <div className="mt-1 text-sm leading-5 text-[#52615c] [overflow-wrap:anywhere]">
                {formatGraphNodeLabel(relationship.source)} → {formatGraphNodeLabel(relationship.target)}
              </div>
            </div>
          ))}
        </div>
        {hiddenRelationshipCount > 0 && (
          <p className="mt-3 rounded-md border border-[#dce3d6] bg-white px-3 py-2 text-sm leading-6 text-[#4f615b]">
            Showing {visibleRelationships.length} of {relationships.length} graph relationships.
          </p>
        )}
      </div>
    </div>
  );
}

function formatGraphTypeLabel(type: string) {
  const withoutTechnicalSuffix = type.replace(/_cid$/i, '');
  return withoutTechnicalSuffix
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatGraphNodeLabel(nodeId: string) {
  if (nodeId.startsWith('bafk')) return 'Selected section';
  const [prefix, value] = nodeId.split(':');
  if (!value) return nodeId;
  if (prefix === 'portland_code_title') return `Title ${value}`;
  if (prefix === 'portland_code_chapter') return `Chapter ${value}`;
  if (prefix === 'portland_code_section') return `Section ${value.replace(/_/g, '.')}`;
  if (prefix === 'municipal_actor') return value.replace(/_/g, ' ');
  if (prefix === 'municipal_subject') return value.replace(/_/g, ' ');
  if (prefix === 'ordinance') return `Ordinance ${value}`;
  if (prefix === 'jurisdiction') return value;
  return value.replace(/_/g, ' ');
}

function SectionReader({ section }: { section: CorpusSection }) {
  return (
    <article aria-labelledby="selected-section-heading">
      <div className="border-b border-[#e1e6dc] px-4 py-4 sm:px-5">
        <div className="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
          <div>
            <p className="text-sm font-semibold text-[#24594f]">
              {section.bluebook_citation || section.official_cite || section.identifier}
            </p>
            <h2 id="selected-section-heading" className="mt-1 text-xl font-semibold tracking-normal text-[#172026] [overflow-wrap:anywhere] sm:text-2xl">{section.title}</h2>
          </div>
          <a
            href={section.source_url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex min-h-11 items-center justify-center rounded-md border border-[#8fa08a] px-3 text-sm font-semibold text-[#24594f] hover:bg-[#f3f6ef]"
          >
            Official source<span className="sr-only"> for {section.identifier}</span>
          </a>
        </div>
      </div>
      <div className="max-w-prose px-4 py-4 sm:px-5 sm:py-5">
        {section.text.split(/\n{2,}/).map((paragraph, index) => (
          <p key={index} className="mb-4 text-base leading-7 text-[#26343a] [overflow-wrap:anywhere]">
            {paragraph.trim()}
          </p>
        ))}
      </div>
    </article>
  );
}

function ProofPanel({ proof }: { proof: LogicProofSummary | null }) {
  if (!proof) {
    return <div className="px-4 py-4 sm:px-5 sm:py-5"><EmptyState title="No proof summary loaded" /></div>;
  }

  const certificateWarning = getSimulatedCertificateWarning(proof);
  const tdfolParse = parseTdfolForDisplay(proof.deontic_temporal_fol);
  const explanation = explainLogicProofSummary(proof);

  return (
    <div className="px-4 py-4 sm:px-5 sm:py-5">
      <div className="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
        <div>
          <h2 className="text-xl font-semibold tracking-normal text-[#172026]">Logic Proof Explorer</h2>
          <p className="mt-1 text-sm text-[#607068]">{proof.formalization_scope}</p>
        </div>
        <span className="rounded-md bg-[#eef2ea] px-3 py-1.5 text-xs font-semibold uppercase text-[#4d625b]">
          {proof.norm_type}
        </span>
      </div>

      <div className="mt-4 grid gap-2 text-xs min-[480px]:grid-cols-2 xl:grid-cols-4">
        <ProofMetric label="Operator" value={proof.norm_operator} />
        <ProofMetric label="FOL" value={proof.fol_status} />
        <ProofMetric label="Deontic" value={proof.deontic_status} />
        <ProofMetric label="TDFOL parse" value={tdfolParse.ok ? 'valid' : 'check'} />
      </div>

      {certificateWarning && (
        <div className="mt-4 rounded-md border border-[#d6c28e] bg-[#fff9e8] px-3 py-2 text-sm leading-6 text-[#735b18]">
          {certificateWarning}
        </div>
      )}

      <div className="mt-4 rounded-md border border-[#dce3d6] bg-[#f8faf5] px-4 py-4">
        <div className="text-xs font-semibold uppercase tracking-wide text-[#607068]">Explanation</div>
        <p className="mt-2 text-sm leading-6 text-[#26343a] [overflow-wrap:anywhere]">{explanation.plainLanguage}</p>
        <div className="mt-2 text-xs leading-5 text-[#65736e]">
          {explanation.temporalScope}. {explanation.certificateStatus}.
        </div>
      </div>

      {!tdfolParse.ok && (
        <div className="mt-4 rounded-md border border-[#d89b82] bg-[#fff4ef] px-3 py-2 text-sm leading-6 text-[#8a3b22]">
          {tdfolParse.error}
        </div>
      )}

      <FormulaBlock label="TDFOL" value={tdfolParse.formatted || proof.deontic_temporal_fol} />
      <FormulaBlock label="DCEC" value={proof.deontic_cognitive_event_calculus} />
      <FormulaBlock label="Frame Logic" value={proof.frame_logic_ergo} />
      <FormulaBlock label="Certificate" value={`${proof.zkp_backend}: ${proof.zkp_security_note}`} />
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-md border border-[#d7ddd2] bg-white px-2 py-2 text-left shadow-sm sm:min-w-[86px] sm:px-3 sm:text-right">
      <div className="text-base font-semibold text-[#172026] sm:text-lg">{value}</div>
      <div className="text-[0.68rem] uppercase tracking-wide text-[#607068] sm:text-xs">{label}</div>
    </div>
  );
}

function EmptyState({ title }: { title: string }) {
  return (
    <div className="rounded-md border border-dashed border-[#aebba9] bg-white/70 px-4 py-8 text-center text-sm text-[#4f615b]" role="status">
      {title}
    </div>
  );
}

function ProofMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-[#f4f7f0] px-2 py-2">
      <div className="uppercase tracking-wide text-[#6d7b74]">{label}</div>
      <div className="mt-1 font-semibold text-[#26343a] [overflow-wrap:anywhere]">{value}</div>
    </div>
  );
}

function FormulaBlock({ label, value }: { label: string; value: string }) {
  if (!value) return null;
  return (
    <details className="mt-4 rounded-md border border-[#dce3d6] bg-[#fbfcf8]">
      <summary className="min-h-11 cursor-pointer px-3 py-3 text-xs font-semibold uppercase tracking-wide text-[#4f615b]">
        {label}
      </summary>
      <pre className="max-h-56 overflow-auto whitespace-pre-wrap border-t border-[#dce3d6] px-3 py-3 text-xs leading-5 text-[#26343a] [overflow-wrap:anywhere]">
        {value}
      </pre>
    </details>
  );
}

function parseTdfolForDisplay(source: string): { ok: boolean; formatted?: string; error?: string } {
  if (!source) {
    return { ok: false, error: 'No TDFOL formula available.' };
  }
  try {
    return { ok: true, formatted: formatTdfolFormula(parseTdfolFormula(source)) };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : 'Unable to parse TDFOL formula.',
    };
  }
}

function buildDirectory(sections: CorpusSection[]): DirectoryTitle[] {
  const byTitle = new Map<string, CorpusSection[]>();
  for (const section of sections) {
    const titleNumber = section.title_number || getTitleNumber(section) || 'Other';
    byTitle.set(titleNumber, [...(byTitle.get(titleNumber) || []), section]);
  }

  return [...byTitle.entries()]
    .sort(([left], [right]) => Number(left) - Number(right))
    .map(([number, titleSections]) => {
      const byChapter = new Map<string, CorpusSection[]>();
      for (const section of titleSections) {
        const chapter = getChapterNumber(section) || number;
        byChapter.set(chapter, [...(byChapter.get(chapter) || []), section]);
      }
      const chapters = [...byChapter.entries()]
        .sort(([left], [right]) => compareCodeNumbers(left, right))
        .map(([chapterNumber, chapterSections]) => ({
          number: chapterNumber,
          sections: chapterSections.sort(compareSections),
        }));
      return {
        number,
        label: TITLE_LABELS[number] || `Title ${number}`,
        sections: titleSections.sort(compareSections),
        chapters,
      };
    });
}

function filterDirectorySections(sections: CorpusSection[], titleFilter: string, chapterFilter: string) {
  return sections
    .filter((section) => !titleFilter || (section.title_number || getTitleNumber(section)) === titleFilter)
    .filter((section) => !chapterFilter || getChapterNumber(section) === chapterFilter)
    .sort(compareSections);
}

function sectionToResult(section: CorpusSection): SearchResult {
  return {
    ipfs_cid: section.ipfs_cid,
    section,
    score: 0,
    scoreParts: { keyword: 0, vector: 0, title: 0, citation: 0 },
    snippet: section.text.replace(/\s+/g, ' ').slice(0, 320),
    citation: section.bluebook_citation || section.official_cite || section.identifier,
  };
}

function getTitleNumber(section: CorpusSection) {
  return getCodeParts(section).title;
}

function getChapterNumber(section: CorpusSection) {
  return getCodeParts(section).chapter;
}

function getCodeParts(section: CorpusSection) {
  const source = section.identifier || section.title || '';
  const match = source.match(/Portland City Code\s+(\d+)(?:[A-Z])?\.(\d+[A-Z]?)/i)
    || source.match(/^(\d+)(?:[A-Z])?\.(\d+[A-Z]?)/);
  if (!match) {
    return { title: section.title_number || '', chapter: '' };
  }
  return { title: match[1], chapter: `${match[1]}.${match[2]}` };
}

function compareSections(left: CorpusSection, right: CorpusSection) {
  return compareCodeNumbers(left.identifier || left.title, right.identifier || right.title);
}

function compareCodeNumbers(left: string, right: string) {
  const leftParts = (left.match(/\d+[A-Z]?/gi) || []).map(normalizeCodePart);
  const rightParts = (right.match(/\d+[A-Z]?/gi) || []).map(normalizeCodePart);
  const length = Math.max(leftParts.length, rightParts.length);
  for (let index = 0; index < length; index += 1) {
    const leftValue = leftParts[index] || '';
    const rightValue = rightParts[index] || '';
    if (leftValue !== rightValue) {
      return leftValue.localeCompare(rightValue, undefined, { numeric: true });
    }
  }
  return left.localeCompare(right);
}

function normalizeCodePart(value: string) {
  return value.toUpperCase();
}
