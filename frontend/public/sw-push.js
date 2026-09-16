/* ImmobilCloud Web Push service worker */
self.addEventListener("push", (event) => {
  let data = { title: "ImmobilCloud", body: "", url: "/it/cloud/account" };
  try {
    if (event.data) data = { ...data, ...event.data.json() };
  } catch (e) {
    try {
      data.body = event.data ? event.data.text() : "";
    } catch (_) {}
  }
  event.waitUntil(
    self.registration.showNotification(data.title || "ImmobilCloud", {
      body: data.body || "",
      icon: "/favicon.ico",
      badge: "/favicon.ico",
      data: { url: data.url || "/it/cloud/account" },
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || "/it/cloud/account";
  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((list) => {
      for (const c of list) {
        if (c.url.includes("/cloud") && "focus" in c) {
          c.navigate(url);
          return c.focus();
        }
      }
      if (clients.openWindow) return clients.openWindow(url);
    })
  );
});
