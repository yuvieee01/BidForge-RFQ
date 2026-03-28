import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { rfqService } from '../services';

const TRIGGER_TYPES = [
  { value: 'ANY_BID', label: 'Any Bid', desc: 'Extend whenever any bid lands in the trigger window' },
  { value: 'ANY_RANK_CHANGE', label: 'Any Rank Change', desc: 'Extend when any supplier changes position' },
  { value: 'L1_CHANGE', label: 'L1 Change', desc: 'Extend only when the lowest bid (L1) changes' },
];

function Field({ label, hint, children }) {
  return (
    <div>
      <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">{label}</label>
      {hint && <p className="text-xs text-slate-600 mb-1.5">{hint}</p>}
      {children}
    </div>
  );
}

const inputCls = "w-full px-4 py-2.5 rounded-xl bg-slate-800/60 border border-slate-700/50 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/50 transition-all text-sm";

export default function RFQCreatePage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const now = new Date();
  const toLocal = (d) => new Date(d - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);

  const [form, setForm] = useState({
    name: '',
    reference_id: '',
    bid_start_time: toLocal(new Date(now.getTime() + 5 * 60000)),
    bid_close_time: toLocal(new Date(now.getTime() + 65 * 60000)),
    forced_close_time: toLocal(new Date(now.getTime() + 125 * 60000)),
    trigger_window_minutes: 5,
    extension_minutes: 5,
    trigger_type: 'ANY_BID',
  });

  const update = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const payload = {
      name: form.name,
      reference_id: form.reference_id,
      bid_start_time: new Date(form.bid_start_time).toISOString(),
      bid_close_time: new Date(form.bid_close_time).toISOString(),
      forced_close_time: new Date(form.forced_close_time).toISOString(),
      auction_config: {
        trigger_window_minutes: Number(form.trigger_window_minutes),
        extension_minutes: Number(form.extension_minutes),
        trigger_type: form.trigger_type,
      },
    };

    try {
      const res = await rfqService.create(payload);
      navigate(`/auction/${res.data.data.id}`);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create RFQ.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-10">
      {/* Header */}
      <div className="mb-8">
        <button onClick={() => navigate(-1)} className="text-slate-500 hover:text-slate-300 text-sm flex items-center gap-1 mb-4 transition-colors">
          ← Back
        </button>
        <h1 className="text-2xl font-bold text-slate-100">Create New RFQ</h1>
        <p className="text-slate-500 text-sm mt-1">Set up an auction with British-style extension rules</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Section: Basic Info */}
        <section className="bg-slate-900/60 border border-slate-700/50 rounded-2xl p-6 space-y-5">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Basic Information</h2>

          <Field label="RFQ Name">
            <input type="text" value={form.name} onChange={e => update('name', e.target.value)}
              placeholder="e.g. Supply of Raw Materials Q2 2025" required className={inputCls} />
          </Field>

          <Field label="Reference ID" hint="A unique identifier for this RFQ">
            <input type="text" value={form.reference_id} onChange={e => update('reference_id', e.target.value)}
              placeholder="e.g. RFQ-2025-001" required className={inputCls} />
          </Field>
        </section>

        {/* Section: Timing */}
        <section className="bg-slate-900/60 border border-slate-700/50 rounded-2xl p-6 space-y-5">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Auction Schedule</h2>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Field label="Bid Start Time">
              <input type="datetime-local" value={form.bid_start_time}
                onChange={e => update('bid_start_time', e.target.value)} required className={inputCls} />
            </Field>
            <Field label="Bid Close Time" hint="Dynamic — may extend">
              <input type="datetime-local" value={form.bid_close_time}
                onChange={e => update('bid_close_time', e.target.value)} required className={inputCls} />
            </Field>
            <Field label="Forced Close Time" hint="Hard limit — never exceeded">
              <input type="datetime-local" value={form.forced_close_time}
                onChange={e => update('forced_close_time', e.target.value)} required className={inputCls} />
            </Field>
          </div>

          <div className="px-4 py-3 rounded-xl bg-blue-500/10 border border-blue-500/20 text-xs text-blue-300">
            💡 <strong>Forced close time</strong> is the absolute hard limit. Auction will never run beyond this time, regardless of extensions.
          </div>
        </section>

        {/* Section: Extension Rules */}
        <section className="bg-slate-900/60 border border-slate-700/50 rounded-2xl p-6 space-y-5">
          <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Extension Rules</h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Field label="Trigger Window (minutes)" hint="Extend if event occurs within X min of close">
              <input type="number" min="1" max="60" value={form.trigger_window_minutes}
                onChange={e => update('trigger_window_minutes', e.target.value)} required className={inputCls} />
            </Field>
            <Field label="Extension Duration (minutes)" hint="Add Y minutes when triggered">
              <input type="number" min="1" max="60" value={form.extension_minutes}
                onChange={e => update('extension_minutes', e.target.value)} required className={inputCls} />
            </Field>
          </div>

          <Field label="Trigger Type">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-1">
              {TRIGGER_TYPES.map((t) => (
                <button
                  key={t.value}
                  type="button"
                  onClick={() => update('trigger_type', t.value)}
                  className={`p-3 rounded-xl border text-left transition-all duration-150 ${
                    form.trigger_type === t.value
                      ? 'border-blue-500 bg-blue-500/10 text-blue-300'
                      : 'border-slate-700/50 bg-slate-800/40 text-slate-400 hover:border-slate-600'
                  }`}
                >
                  <p className="text-xs font-bold mb-1">{t.label}</p>
                  <p className="text-xs leading-relaxed opacity-80">{t.desc}</p>
                </button>
              ))}
            </div>
          </Field>
        </section>

        {error && (
          <div className="px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
            {error}
          </div>
        )}

        <div className="flex gap-3">
          <button type="button" onClick={() => navigate(-1)}
            className="flex-1 py-3 rounded-xl border border-slate-700 text-slate-400 hover:text-slate-200 hover:border-slate-600 font-semibold text-sm transition-all">
            Cancel
          </button>
          <button type="submit" disabled={loading}
            className="flex-1 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 active:scale-95 text-white font-semibold text-sm transition-all shadow-lg shadow-blue-900/30 disabled:opacity-50">
            {loading ? 'Creating…' : 'Create RFQ →'}
          </button>
        </div>
      </form>
    </div>
  );
}
