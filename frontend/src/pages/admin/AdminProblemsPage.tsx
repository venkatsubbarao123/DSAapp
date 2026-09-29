import React, { useState, useEffect } from 'react';
import { adminApi } from '../../services/adminApi';
import { AdminProblemListItem, AdminTestCaseItem } from '../../types/admin';

export const AdminProblemsPage: React.FC = () => {
  const [problems, setProblems] = useState<AdminProblemListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [difficultyFilter, setDifficultyFilter] = useState('');
  const [loading, setLoading] = useState(true);

  // Test Case Management
  const [selectedProblem, setSelectedProblem] = useState<AdminProblemListItem | null>(null);
  const [testCases, setTestCases] = useState<AdminTestCaseItem[]>([]);
  const [tcLoading, setTcLoading] = useState(false);

  // New test case state
  const [newInput, setNewInput] = useState('');
  const [newExpectedOutput, setNewExpectedOutput] = useState('');
  const [newIsSample, setNewIsSample] = useState(false);
  const [newIsHidden, setNewIsHidden] = useState(true);
  const [newDisplayOrder, setNewDisplayOrder] = useState(1);
  const [creatingTc, setCreatingTc] = useState(false);

  const fetchProblems = async () => {
    setLoading(true);
    try {
      const res = await adminApi.listProblems({
        page,
        pageSize: 20,
        search: search || undefined,
        difficulty: difficultyFilter || undefined,
      });
      setProblems(res.items);
      setTotal(res.total);
    } catch (err) {
      console.error('Failed to load problems:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProblems();
  }, [page, difficultyFilter]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchProblems();
  };

  const openTestCaseModal = async (problem: AdminProblemListItem) => {
    setSelectedProblem(problem);
    setTcLoading(true);
    try {
      const list = await adminApi.listTestCases(problem.id);
      setTestCases(list);
      setNewDisplayOrder(list.length + 1);
    } catch (err) {
      console.error('Failed to fetch test cases:', err);
    } finally {
      setTcLoading(false);
    }
  };

  const handleCreateTestCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProblem || !newInput || !newExpectedOutput) return;

    setCreatingTc(true);
    try {
      const created = await adminApi.createTestCase(selectedProblem.id, {
        input: newInput,
        expected_output: newExpectedOutput,
        is_sample: newIsSample,
        is_hidden: newIsHidden,
        display_order: newDisplayOrder,
      });
      setTestCases((prev) => [...prev, created]);
      setNewInput('');
      setNewExpectedOutput('');
      setNewDisplayOrder((o) => o + 1);
      fetchProblems();
    } catch (err: any) {
      alert(err.message || 'Failed to create test case');
    } finally {
      setCreatingTc(false);
    }
  };

  const handleDeleteTestCase = async (tcId: string) => {
    if (!confirm('Are you sure you want to permanently delete this test case?')) return;
    try {
      await adminApi.deleteTestCase(tcId);
      setTestCases((prev) => prev.filter((tc) => tc.id !== tcId));
      fetchProblems();
    } catch (err: any) {
      alert(err.message || 'Failed to delete test case');
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Problem & Test Case Studio</h1>
          <p className="text-xs text-slate-400 mt-1">
            Configure algorithmic problems and inspect hidden test cases required for Online Judge grading.
          </p>
        </div>
        <span className="rounded-full bg-slate-900 border border-slate-800 px-3 py-1 text-xs text-slate-400">
          Catalog Size: <strong className="text-white">{total}</strong>
        </span>
      </div>

      {/* Filter / Search Bar */}
      <div className="flex gap-3 bg-slate-900/60 p-4 rounded-xl border border-slate-800">
        <form onSubmit={handleSearch} className="flex-1">
          <input
            type="text"
            placeholder="Search problem title or slug..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </form>

        <select
          value={difficultyFilter}
          onChange={(e) => {
            setDifficultyFilter(e.target.value);
            setPage(1);
          }}
          className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500"
        >
          <option value="">All Difficulties</option>
          <option value="EASY">Easy</option>
          <option value="MEDIUM">Medium</option>
          <option value="HARD">Hard</option>
        </select>
      </div>

      {/* Problems Table */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 overflow-hidden shadow-xl">
        <table className="w-full text-left text-xs">
          <thead className="border-b border-slate-800 bg-slate-900/80 text-slate-400">
            <tr>
              <th className="px-4 py-3 font-semibold">Title</th>
              <th className="px-4 py-3 font-semibold">Difficulty</th>
              <th className="px-4 py-3 font-semibold">Status</th>
              <th className="px-4 py-3 font-semibold">Access</th>
              <th className="px-4 py-3 font-semibold">Test Cases</th>
              <th className="px-4 py-3 font-semibold text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {loading ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                  Loading problem catalog...
                </td>
              </tr>
            ) : problems.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                  No problems found.
                </td>
              </tr>
            ) : (
              problems.map((p) => (
                <tr key={p.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-3">
                    <div className="font-semibold text-white">{p.title}</div>
                    <div className="text-[11px] text-slate-500">{p.slug}</div>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded px-2 py-0.5 text-[10px] font-bold ${
                        p.difficulty === 'EASY'
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : p.difficulty === 'MEDIUM'
                          ? 'bg-amber-500/20 text-amber-400'
                          : 'bg-rose-500/20 text-rose-400'
                      }`}
                    >
                      {p.difficulty}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-slate-300 font-medium">{p.status}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] text-slate-400">
                      {p.access_level}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white">{p.test_cases_count}</span>
                      <span className="rounded-full bg-rose-950/60 border border-rose-500/30 px-2 py-0.5 text-[10px] text-rose-300 font-semibold">
                        {p.hidden_test_cases_count} Hidden
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => openTestCaseModal(p)}
                      className="rounded-lg bg-blue-600 px-3 py-1 text-xs font-semibold text-white hover:bg-blue-500 transition-colors shadow"
                    >
                      Manage Test Cases
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Test Case Management Modal */}
      {selectedProblem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-in fade-in">
          <div className="w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h2 className="text-base font-bold text-white">Test Cases Studio</h2>
                <p className="text-xs text-slate-400 mt-0.5">Problem: {selectedProblem.title}</p>
              </div>
              <button
                onClick={() => setSelectedProblem(null)}
                className="text-slate-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            {/* Existing Test Cases List */}
            <div className="space-y-3">
              <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Current Test Suite ({testCases.length} total)
              </h3>
              {tcLoading ? (
                <div className="py-6 text-center text-xs text-slate-400">Loading test cases...</div>
              ) : testCases.length === 0 ? (
                <div className="rounded-lg border border-dashed border-slate-800 p-6 text-center text-xs text-slate-500">
                  No test cases defined yet.
                </div>
              ) : (
                <div className="space-y-2">
                  {testCases.map((tc, idx) => (
                    <div
                      key={tc.id}
                      className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-slate-300">Case #{idx + 1}</span>
                          {tc.is_sample && (
                            <span className="rounded bg-blue-600/20 text-blue-400 px-2 py-0.5 text-[10px] font-semibold">
                              Sample
                            </span>
                          )}
                          {tc.is_hidden ? (
                            <span className="rounded bg-rose-600/20 text-rose-400 border border-rose-500/30 px-2 py-0.5 text-[10px] font-semibold">
                              Hidden Verification
                            </span>
                          ) : (
                            <span className="rounded bg-emerald-600/20 text-emerald-400 px-2 py-0.5 text-[10px] font-semibold">
                              Public
                            </span>
                          )}
                        </div>
                        <button
                          onClick={() => handleDeleteTestCase(tc.id)}
                          className="text-xs text-rose-400 hover:text-rose-300 font-semibold"
                        >
                          Delete
                        </button>
                      </div>

                      <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                        <div className="bg-slate-900 p-2 rounded border border-slate-800/80">
                          <span className="text-[10px] text-slate-500 block mb-1">Standard Input:</span>
                          <pre className="whitespace-pre-wrap text-slate-300 text-[11px]">{tc.input}</pre>
                        </div>
                        <div className="bg-slate-900 p-2 rounded border border-slate-800/80">
                          <span className="text-[10px] text-slate-500 block mb-1">Expected Output:</span>
                          <pre className="whitespace-pre-wrap text-emerald-400 text-[11px]">{tc.expected_output}</pre>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Author New Test Case */}
            <form onSubmit={handleCreateTestCase} className="rounded-xl border border-slate-800 bg-slate-950/80 p-4 space-y-3">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                + Add Test Case
              </h4>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-400">Standard Input</label>
                  <textarea
                    rows={3}
                    placeholder="e.g. 2 7 11 15\n9"
                    value={newInput}
                    onChange={(e) => setNewInput(e.target.value)}
                    className="w-full font-mono text-xs rounded-lg border border-slate-700 bg-slate-900 p-2 text-white focus:outline-none focus:border-blue-500"
                    required
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-[11px] font-semibold text-slate-400">Expected Output</label>
                  <textarea
                    rows={3}
                    placeholder="e.g. 0 1"
                    value={newExpectedOutput}
                    onChange={(e) => setNewExpectedOutput(e.target.value)}
                    className="w-full font-mono text-xs rounded-lg border border-slate-700 bg-slate-900 p-2 text-white focus:outline-none focus:border-blue-500"
                    required
                  />
                </div>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-4 pt-2">
                <div className="flex items-center gap-4 text-xs">
                  <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={newIsHidden}
                      onChange={(e) => setNewIsHidden(e.target.checked)}
                      className="h-4 w-4 rounded bg-slate-800 border-slate-700 text-rose-600 focus:ring-rose-500"
                    />
                    <span className="font-semibold text-rose-300">Hidden from students</span>
                  </label>

                  <label className="flex items-center gap-2 text-slate-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={newIsSample}
                      onChange={(e) => setNewIsSample(e.target.checked)}
                      className="h-4 w-4 rounded bg-slate-800 border-slate-700 text-blue-600 focus:ring-blue-500"
                    />
                    <span>Sample Test Case</span>
                  </label>
                </div>

                <button
                  type="submit"
                  disabled={creatingTc}
                  className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-emerald-500 transition-colors disabled:opacity-50"
                >
                  {creatingTc ? 'Saving...' : 'Add Test Case to Suite'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
