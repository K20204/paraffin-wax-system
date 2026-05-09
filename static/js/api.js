const api = {
    async request(method, url, data = null) {
        const opts = {
            method,
            headers: { "Content-Type": "application/json" },
        };
        if (data && method !== "GET") {
            opts.body = JSON.stringify(data);
        }
        const res = await fetch(url, opts);
        const json = await res.json();
        if (!json.success) {
            throw new Error(json.error || "Unknown error");
        }
        return json;
    },
    get(url) { return this.request("GET", url); },
    post(url, data) { return this.request("POST", url, data); },
    put(url, data) { return this.request("PUT", url, data); },
    del(url) { return this.request("DELETE", url); },
};
