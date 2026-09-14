/**
 * M22 — unit test del grid clustering (logica pura, nessun DOM/leaflet).
 */
const { clusterMarkers } = require("../apps/immocloud/lib/clustering");

const mk = (lat, lng, id) => ({ id, lat, lng });

describe("clusterMarkers", () => {
  test("zoom alto → nessun cluster, tutti singoli", () => {
    const markers = [mk(41.9, 12.5, "a"), mk(41.91, 12.51, "b")];
    const { clusters, singles } = clusterMarkers(markers, 15);
    expect(clusters).toHaveLength(0);
    expect(singles).toHaveLength(2);
  });

  test("zoom basso → marker vicini raggruppati", () => {
    const markers = [
      mk(41.9, 12.5, "a"), mk(41.901, 12.501, "b"), mk(41.902, 12.502, "c"),
      mk(45.46, 9.19, "milano"),
    ];
    const { clusters, singles } = clusterMarkers(markers, 5);
    expect(clusters).toHaveLength(1);
    expect(clusters[0].count).toBe(3);
    expect(singles.map((s) => s.id)).toEqual(["milano"]);
  });

  test("500 marker → output completo senza perdite", () => {
    const markers = Array.from({ length: 500 }, (_, i) =>
      mk(36 + (i % 50) * 0.2, 7 + Math.floor(i / 50) * 0.5, `p${i}`)
    );
    const { clusters, singles } = clusterMarkers(markers, 6);
    const total = clusters.reduce((s, c) => s + c.count, 0) + singles.length;
    expect(total).toBe(500);
  });
});
