/** A-028h / A-034 R3 — Attività / follow-up (lista + settimana leggera). */
import React, { useEffect, useMemo, useState } from "react";
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

function addDaysIso(iso, days) {
  const d = new Date(`${iso}T12:00:00.000Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

function weekDaysFrom(startIso) {
  return Array.from({ length: 7 }, (_, i) => addDaysIso(startIso, i));
}

function mondayOf(iso) {
  const d = new Date(`${iso}T12:00:00.000Z`);
  const day = d.getUTCDay(); // 0 Sun
  const diff = day === 0 ? -6 : 1 - day;
  d.setUTCDate(d.getUTCDate() + diff);
  return d.toISOString().slice(0, 10);
}

export default function ActivitiesPage() {
  const { lang } = useParams();
  const l = (lang || "it").slice(0, 2);
  const [items, setItems] = useState([]);
  const [filter, setFilter] = useState("open"); // open | today | overdue | week | done
  const [weekStart, setWeekStart] = useState(() => mondayOf(todayIsoDate()));
  const [loading, setLoading] = useState(true);
  const [title, setTitle] = useState("");
  const [kind, setKind] = useState("follow_up");
  const [due, setDue] = useState(todayIsoDate());
  const [clientId, setClientId] = useState("");
  const [propertyId, setPropertyId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      let params = "status=open";
      if (filter === "done") params = "status=done";
      else if (filter === "today") params = "status=open&due=today";
      else if (filter === "overdue") params = "status=open&due=overdue";
      else if (filter === "week") {
        params = `status=open&due=week&week_start=${weekStart}`;
      }
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
  }, [filter, weekStart]);

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
        related_client_id: clientId.trim() || null,
        related_property_id: propertyId.trim() || null,
      });
      setTitle("");
      setClientId("");
      setPropertyId("");
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

  const days = useMemo(() => weekDaysFrom(weekStart), [weekStart]);
  const byDay = useMemo(() => {
    const map = Object.fromEntries(days.map((d) => [d, []]));
    for (const a of items) {
      const day = a.due_at ? String(a.due_at).slice(0, 10) : null;
      if (day && map[day]) map[day].push(a);
    }
    return map;
  }, [items, days]);

  const weekdayLabel = (iso) => {
    try {
      return new Date(`${iso}T12:00:00`).toLocaleDateString("it-IT", {
        weekday: "short",
        day: "numeric",
        month: "short",
      });
    } catch {
      return iso;
    }
  };

  return (
    <AgencyShell current="activities">
      <section data-testid="activities-page" className="space-y-8 max-w-4xl">
        <div>
          <p className="text-[10px] uppercase tracking-[0.3em] text-stone-500 mb-2">ImmoWeb · Operativo</p>
          <h1
            className="text-3xl md:text-4xl tracking-tight"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            Attività
          </h1>
          <p className="text-sm text-stone-600 mt-2 max-w-xl">
            Chiamate, visite e cose da fare. Organizzate per giorno.
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
            <label className="min-w-[140px] flex-1">
              <span className="text-[10px] uppercase tracking-widest text-stone-500">Cliente (opzionale)</span>
              <input
                data-testid="activity-client-id"
                value={clientId}
                onChange={(e) => setClientId(e.target.value)}
                placeholder="Codice cliente, se ce l’hai"
                className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md text-sm"
              />
            </label>
            <label className="min-w-[140px] flex-1">
              <span className="text-[10px] uppercase tracking-widest text-stone-500">Immobile (opzionale)</span>
              <input
                data-testid="activity-property-id"
                value={propertyId}
                onChange={(e) => setPropertyId(e.target.value)}
                placeholder="Codice immobile, se ce l’hai"
                className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md text-sm"
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
            ["week", "Settimana"],
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

        {filter === "week" && (
          <div className="flex flex-wrap items-center gap-3" data-testid="activity-week-nav">
            <button
              type="button"
              onClick={() => setWeekStart(addDaysIso(weekStart, -7))}
              className="px-3 py-1.5 text-xs border border-stone-300 rounded-md bg-white"
            >
              ← Prec.
            </button>
            <p className="text-sm text-stone-700">
              Settimana dal <span className="font-medium">{weekStart}</span>
            </p>
            <button
              type="button"
              onClick={() => setWeekStart(addDaysIso(weekStart, 7))}
              className="px-3 py-1.5 text-xs border border-stone-300 rounded-md bg-white"
            >
              Succ. →
            </button>
            <button
              type="button"
              onClick={() => setWeekStart(mondayOf(todayIsoDate()))}
              className="px-3 py-1.5 text-xs border border-stone-300 rounded-md bg-white"
            >
              Questa settimana
            </button>
          </div>
        )}

        {loading ? (
          <p className="text-sm text-stone-500">Caricamento…</p>
        ) : filter === "week" ? (
          <div
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-7 gap-2"
            data-testid="activities-week-grid"
          >
            {days.map((day) => (
              <div key={day} className="border border-stone-200 bg-white rounded-lg min-h-[120px] p-2">
                <p className="text-[10px] uppercase tracking-widest text-stone-500 mb-2">
                  {weekdayLabel(day)}
                </p>
                <ul className="space-y-1.5">
                  {(byDay[day] || []).map((a) => (
                    <li key={a.id} className="text-xs border border-stone-100 rounded px-2 py-1.5">
                      <p className="font-medium text-stone-900 line-clamp-2">{a.title}</p>
                      <p className="text-[10px] text-stone-500 mt-0.5">
                        {KINDS.find((k) => k.id === a.kind)?.label || a.kind}
                      </p>
                      {(a.related_client_id || a.related_property_id) && (
                        <p className="text-[10px] mt-1 flex flex-wrap gap-1">
                          {a.related_client_id && (
                            <Link className="underline text-stone-600" to={`/${l}/app/clients/${a.related_client_id}`}>
                              Cliente
                            </Link>
                          )}
                          {a.related_property_id && (
                            <Link className="underline text-stone-600" to={`/${l}/app/properties/${a.related_property_id}`}>
                              Immobile
                            </Link>
                          )}
                        </p>
                      )}
                      {a.status === "open" && (
                        <button
                          type="button"
                          onClick={() => markDone(a.id)}
                          className="mt-1 text-[9px] uppercase tracking-widest text-stone-600 underline"
                        >
                          Fatto
                        </button>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
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
                  {(a.related_client_id || a.related_property_id) && (
                    <p className="text-[11px] mt-1 flex flex-wrap gap-2">
                      {a.related_client_id && (
                        <Link className="underline text-stone-600" to={`/${l}/app/clients/${a.related_client_id}`}>
                          Cliente
                        </Link>
                      )}
                      {a.related_property_id && (
                        <Link className="underline text-stone-600" to={`/${l}/app/properties/${a.related_property_id}`}>
                          Immobile
                        </Link>
                      )}
                    </p>
                  )}
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
