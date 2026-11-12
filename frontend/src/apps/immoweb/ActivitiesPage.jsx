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

function EntitySearch({ kind, value, onChange, testId, placeholder }) {
  const [q, setQ] = useState("");
  const [hits, setHits] = useState([]);
  const [label, setLabel] = useState("");

  useEffect(() => {
    if (!value) {
      setLabel("");
      return;
    }
    const url = kind === "client" ? `/app/clients/${value}` : `/app/properties/${value}`;
    api
      .get(url)
      .then((r) => {
        const d = r.data || {};
        setLabel(
          kind === "client"
            ? `${d.name || ""} ${d.surname || ""}`.trim() || d.email || value
            : d.title || d.reference_code || value
        );
      })
      .catch(() => setLabel(value));
  }, [kind, value]);

  const search = async (text) => {
    setQ(text);
    if (!text || text.length < 2) {
      setHits([]);
      return;
    }
    try {
      const url = kind === "client" ? "/app/clients" : "/app/properties";
      const { data } = await api.get(url, { params: { q: text, page_size: 8, limit: 8 } });
      setHits(data.items || []);
    } catch {
      setHits([]);
    }
  };

  const pick = (item) => {
    onChange(item.id);
    setLabel(
      kind === "client"
        ? `${item.name || ""} ${item.surname || ""}`.trim() || item.email
        : item.title || item.reference_code
    );
    setQ("");
    setHits([]);
  };

  return (
    <div className="relative min-w-[140px] flex-1">
      <span className="text-[10px] uppercase tracking-widest text-crm-muted">
        {kind === "client" ? "Cliente (opzionale)" : "Immobile (opzionale)"}
      </span>
      {value ? (
        <div className="mt-1 flex items-center gap-2 border border-crm-line rounded-md px-3 py-2 text-sm bg-white">
          <span className="truncate flex-1 text-crm-navy">{label || "Selezionato"}</span>
          <button
            type="button"
            className="text-[10px] uppercase tracking-widest text-crm-muted"
            onClick={() => {
              onChange("");
              setLabel("");
            }}
          >
            Cambia
          </button>
        </div>
      ) : (
        <input
          data-testid={testId}
          value={q}
          onChange={(e) => search(e.target.value)}
          placeholder={placeholder}
          className="crm-input mt-1 w-full px-3 py-2 border border-crm-line rounded-md text-sm"
          autoComplete="off"
        />
      )}
      {hits.length > 0 ? (
        <ul className="absolute z-20 mt-1 w-full bg-white border border-crm-line max-h-48 overflow-auto text-sm">
          {hits.map((h) => (
            <li key={h.id}>
              <button
                type="button"
                className="w-full text-left px-3 py-2 hover:bg-crm-mist"
                onClick={() => pick(h)}
              >
                {kind === "client"
                  ? `${h.name || ""} ${h.surname || ""}`.trim() || h.email
                  : h.title || h.reference_code}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
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
      <section data-testid="activities-page" className="crm-desk space-y-8 max-w-4xl">
        <div>
          <p className="crm-eyebrow mb-2" data-testid="activities-crm-eyebrow">
            Operativo · bancone
          </p>
          <h1 className="crm-title text-3xl md:text-4xl">Attività</h1>
          <p className="text-sm text-crm-muted mt-2 max-w-xl">
            Chiamate, visite e cose da fare. Organizzate per giorno.
          </p>
        </div>

        <form
          onSubmit={create}
          data-testid="activity-create-form"
          className="crm-panel p-5 space-y-3 bg-crm-mist/50"
        >
          <label className="block">
            <span className="text-[10px] uppercase tracking-widest text-crm-muted">Titolo</span>
            <input
              data-testid="activity-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Es. Richiamare Rossi su trilocali EUR"
              className="crm-input mt-1 w-full px-3 py-2 border border-crm-line rounded-md text-sm bg-white"
              required
            />
          </label>
          <div className="flex flex-wrap gap-3">
            <label>
              <span className="text-[10px] uppercase tracking-widest text-crm-muted">Tipo</span>
              <select
                data-testid="activity-kind"
                value={kind}
                onChange={(e) => setKind(e.target.value)}
                className="crm-input mt-1 block px-3 py-2 border border-crm-line rounded-md text-sm bg-white"
              >
                {KINDS.map((k) => (
                  <option key={k.id} value={k.id}>
                    {k.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span className="text-[10px] uppercase tracking-widest text-crm-muted">Scadenza</span>
              <input
                data-testid="activity-due"
                type="date"
                value={due}
                onChange={(e) => setDue(e.target.value)}
                className="crm-input mt-1 block px-3 py-2 border border-crm-line rounded-md text-sm bg-white"
              />
            </label>
            <EntitySearch
              kind="client"
              value={clientId}
              onChange={setClientId}
              testId="activity-client-id"
              placeholder="Cerca per nome o email"
            />
            <EntitySearch
              kind="property"
              value={propertyId}
              onChange={setPropertyId}
              testId="activity-property-id"
              placeholder="Cerca per titolo o codice"
            />
            <button
              type="submit"
              disabled={busy}
              data-testid="activity-submit"
              className="crm-btn-primary self-end px-4 py-2 text-xs uppercase tracking-widest rounded-md disabled:opacity-50"
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
              className={`px-3 py-1.5 text-[10px] uppercase tracking-widest rounded-md border ${
                filter === id
                  ? "crm-btn-primary border-crm-navy"
                  : "crm-btn-ghost"
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
              className="crm-btn-ghost px-3 py-1.5 text-xs rounded-md"
            >
              ← Prec.
            </button>
            <p className="text-sm text-crm-navy">
              Settimana dal <span className="font-medium">{weekStart}</span>
            </p>
            <button
              type="button"
              onClick={() => setWeekStart(addDaysIso(weekStart, 7))}
              className="crm-btn-ghost px-3 py-1.5 text-xs rounded-md"
            >
              Succ. →
            </button>
            <button
              type="button"
              onClick={() => setWeekStart(mondayOf(todayIsoDate()))}
              className="crm-btn-ghost px-3 py-1.5 text-xs rounded-md"
            >
              Questa settimana
            </button>
          </div>
        )}

        {loading ? (
          <p className="text-sm text-crm-muted">Caricamento…</p>
        ) : filter === "week" ? (
          <div
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-7 gap-2"
            data-testid="activities-week-grid"
          >
            {days.map((day) => (
              <div key={day} className="crm-panel min-h-[120px] p-2">
                <p className="text-[10px] uppercase tracking-widest text-crm-gold mb-2">
                  {weekdayLabel(day)}
                </p>
                <ul className="space-y-1.5">
                  {(byDay[day] || []).map((a) => (
                    <li key={a.id} className="text-xs border border-crm-line rounded px-2 py-1.5 bg-crm-mist/40">
                      <p className="font-medium text-crm-navy line-clamp-2">{a.title}</p>
                      <p className="text-[10px] text-crm-muted mt-0.5">
                        {KINDS.find((k) => k.id === a.kind)?.label || a.kind}
                      </p>
                      {(a.related_client_id || a.related_property_id) && (
                        <p className="text-[10px] mt-1 flex flex-wrap gap-1">
                          {a.related_client_id && (
                            <Link className="underline text-crm-navy" to={`/${l}/app/clients/${a.related_client_id}`}>
                              Cliente
                            </Link>
                          )}
                          {a.related_property_id && (
                            <Link className="underline text-crm-navy" to={`/${l}/app/properties/${a.related_property_id}`}>
                              Immobile
                            </Link>
                          )}
                        </p>
                      )}
                      {a.status === "open" && (
                        <button
                          type="button"
                          onClick={() => markDone(a.id)}
                          className="mt-1 text-[9px] uppercase tracking-widest text-crm-muted underline"
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
          <div
            data-testid="activities-empty"
            className="border border-dashed border-crm-line px-5 py-10 text-sm text-crm-muted"
          >
            Nessuna attività qui. Aggiungine una sopra, o torna alla{" "}
            <Link to={`/${l}/app/dashboard`} className="underline text-crm-navy">
              Dashboard
            </Link>
            .
          </div>
        ) : (
          <ul className="crm-panel divide-y divide-crm-line/70" data-testid="activities-list">
            {items.map((a) => (
              <li
                key={a.id}
                data-testid={`activity-${a.id}`}
                className="px-4 py-3 flex flex-wrap items-center justify-between gap-3"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-crm-navy">{a.title}</p>
                  <p className="text-[11px] text-crm-muted mt-0.5">
                    {KINDS.find((k) => k.id === a.kind)?.label || a.kind}
                    {a.due_at ? ` · ${String(a.due_at).slice(0, 10)}` : ""}
                    {a.status === "done" ? " · fatta" : ""}
                  </p>
                  {(a.related_client_id || a.related_property_id) && (
                    <p className="text-[11px] mt-1 flex flex-wrap gap-2">
                      {a.related_client_id && (
                        <Link className="underline text-crm-navy" to={`/${l}/app/clients/${a.related_client_id}`}>
                          Cliente
                        </Link>
                      )}
                      {a.related_property_id && (
                        <Link className="underline text-crm-navy" to={`/${l}/app/properties/${a.related_property_id}`}>
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
                      className="crm-btn-ghost text-[10px] uppercase tracking-widest px-2 py-1 rounded-md"
                    >
                      Fatto
                    </button>
                  )}
                  <button
                    type="button"
                    data-testid={`activity-del-${a.id}`}
                    onClick={() => remove(a.id)}
                    className="text-[10px] uppercase tracking-widest px-2 py-1 text-rose-700 border border-rose-200 rounded-md"
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
