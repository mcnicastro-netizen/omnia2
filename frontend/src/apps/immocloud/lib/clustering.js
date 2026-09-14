/* M22 — grid clustering puro (nessuna dipendenza da leaflet: testabile in jest). */
export const CLUSTER_MAX_ZOOM = 14;

export function clusterMarkers(markers, zoom) {
  if (zoom >= CLUSTER_MAX_ZOOM) return { clusters: [], singles: markers };
  const cell = 360 / Math.pow(2, zoom + 2); // gradi per cella, si dimezza a ogni zoom
  const grid = new Map();
  for (const m of markers) {
    const key = `${Math.floor(m.lat / cell)}:${Math.floor(m.lng / cell)}`;
    (grid.get(key) || grid.set(key, []).get(key)).push(m);
  }
  const clusters = [];
  const singles = [];
  for (const group of grid.values()) {
    if (group.length === 1) singles.push(group[0]);
    else {
      clusters.push({
        lat: group.reduce((s, m) => s + m.lat, 0) / group.length,
        lng: group.reduce((s, m) => s + m.lng, 0) / group.length,
        count: group.length,
      });
    }
  }
  return { clusters, singles };
}
