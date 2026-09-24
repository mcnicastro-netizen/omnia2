/** A-028h — Attività / follow-up (minimal). */
import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import AgencyShell from "./components/AgencyShell";
import { api } from "../../shared/lib/api";

const KINDS = [
  { id: "follow_up", label: "Follow-up" },
  { id: "call", label: "Chiamata" },
  { id: "visit", label: "Visita" },
  { id: "other", label: "Altro" },
];

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

export default function ActivitiesPage() {
  const { lang } = useParams();
  const l = (lang || "it").slice(0, 2);
  const [items, setItems] = useState([]);
  const [filter, setFilter] = useState("open"); // open | today | overdue | done
  const [loading, setLoading] = useState(true);
  const [title, setTitle] = useState("");
  const [kind, setKind] = useState("follow_up");
  const [due, setDue] = useState(todayIsoDate());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      let params = "status=open";
      if (filter === "done") params = "status=done";
      else if (filter === "today") params = "status=open&due=today";
      else if (filter === "overdue") params = "status=open&due=overdue";
      const { data } = await api.get(`/app/activities?${params}&limit=100`);
      setItems(data.items || []);
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  const create = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;
    setBusy(true);
    setError("");
    try {
      await api.post("/app/activities", {
        title: title.trim(),
        kind,
        due_at: due ? `${due}T12:00:00.000Z` : null,
      });
      setTitle("");
      await load();
    } catch (err) {
      setError(err?.response?.data?.detail || "Errore salvataggio");
    } finally {
      setBusy(false);
    }
  };

  const markDone = async (id) => {
    await api.patch(`/app/activities/${id}`, { status: "done" });
    await load();
  };

  const remove = async (id) => {
    if (!window.confirm("Eliminare questa attività?")) return;
    await api.delete(`/app/activities/${id}`);
    await load();
  };

  return (
    <AgencyShell current="activities">
      <section data-testid="activities-page" className="space-y-8 max-w-3xl">
        <div>
          <p className="text-[10px] uppercase tracking-[0.3em] text-stone-500 mb-2">ImmoWeb · Operativo</p>
          <h1
            className="text-3xl md:text-4xl tracking-tight"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            Attività
          </h1>
          <p className="text-sm text-stone-600 mt-2 max-w-xl">
            Follow-up della giornata. Non sostituisce un calendario completo — alimenta il cockpit «Oggi».
          </p>
        </div>

        <form
          onSubmit={create}
          data-testid="activity-create-form"
          className="bg-white border border-stone-200 rounded-lg p-5 space-y-3"
        >
          <label className="block">
            <span className="text-[10px] uppercase tracking-widest text-stone-500">Titolo</span>
            <input
              data-testid="activity-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Es. Richiamare Rossi su trilocali EUR"
              className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md text-sm"
              required
            />
          </label>
          <div className="flex flex-wrap gap-3">
            <label>
              <span className="text-[10px] uppercase tracking-widest text-stone-500">Tipo</span>
              <select
                data-testid="activity-kind"
                value={kind}
                onChange={(e) => setKind(e.target.value)}
                className="mt-1 block px-3 py-2 border border-stone-300 rounded-md text-sm"
              >
                {KINDS.map((k) => (
                  <option key={k.id} value={k.id}>{k.label}</option>
                ))}
              </select>
            </label>
            <label>
              <span className="text-[10px] uppercase tracking-widest text-stone-500">Scadenza</span>
              <input
                data-testid="activity-due"
                type="date"
                value={due}
                onChange={(e) => setDue(e.target.value)}
                className="mt-1 block px-3 py-2 border border-stone-300 rounded-md text-sm"
              />
            </label>
            <button
              type="submit"
              disabled={busy}
              data-testid="activity-submit"
              className="self-end px-4 py-2 bg-stone-900 text-white text-xs uppercase tracking-widest rounded-md disabled:opacity-50"
            >
              Aggiungi
            </button>
          </div>
          {error && <p className="text-sm text-rose-700">{error}</p>}
        </form>

        <div className="flex flex-wrap gap-2" data-testid="activity-filters">
          {[
            ["open", "Aperte"],
            ["today", "Oggi"],
            ["overdue", "In ritardo"],
            ["done", "Fatte"],
          ].map(([id, label]) => (
            <button
              key={id}
              type="button"
              onClick={() => setFilter(id)}
              className={`px-3 py-1.5 text-[10px] uppercase tracking-widest rounded border ${
                filter === id ? "bg-stone-900 text-white border-stone-900" : "bg-white text-stone-700 border-stone-300"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {loading ? (
          <p className="text-sm text-stone-500">Caricamento…</p>
        ) : items.length === 0 ? (
          <div data-testid="activities-empty" className="border border-dashed border-stone-300 px-5 py-10 text-sm text-stone-600">
            Nessuna attività qui. Aggiungine una sopra, o torna alla{" "}
            <Link to={`/${l}/app/dashboard`} className="underline">Dashboard</Link>.
          </div>
        ) : (
          <ul className="divide-y divide-stone-100 border border-stone-200 bg-white rounded-lg" data-testid="activities-list">
            {items.map((a) => (
              <li key={a.id} data-testid={`activity-${a.id}`} className="px-4 py-3 flex flex-wrap items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-stone-900">{a.title}</p>
                  <p className="text-[11px] text-stone-500 mt-0.5">
                    {KINDS.find((k) => k.id === a.kind)?.label || a.kind}
                    {a.due_at ? ` · ${String(a.due_at).slice(0, 10)}` : ""}
                    {a.status === "done" ? " · fatta" : ""}
                  </p>
                </div>
                <div className="flex gap-2">
                  {a.status === "open" && (
                    <button
                      type="button"
                      data-testid={`activity-done-${a.id}`}
                      onClick={() => markDone(a.id)}
                      className="text-[10px] uppercase tracking-widest px-2 py-1 border border-stone-300 rounded hover:border-stone-900"
                    >
                      Fatto
                    </button>
                  )}
                  <button
                    type="button"
                    data-testid={`activity-del-${a.id}`}
                    onClick={() => remove(a.id)}
                    className="text-[10px] uppercase tracking-widest px-2 py-1 text-rose-700 border border-rose-200 rounded"
                  >
                    Elimina
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </AgencyShell>
  );
}
